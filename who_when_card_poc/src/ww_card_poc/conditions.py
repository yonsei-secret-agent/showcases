from __future__ import annotations

from dataclasses import asdict, dataclass
import re

from ww_card_poc.who_when_io import WhoWhenCase


DEFAULT_CONDITIONS = [
    "no_guidance",
    "coarse_reflection",
    "broad_verification_card",
    "sanitized_raw_gold_explanation",
    "oracle_specific_card",
    "hard_mismatched_card",
]


STEP_PATTERNS = [
    re.compile(r"\bstep\s*\d+\b", re.IGNORECASE),
    re.compile(r"\bt\*\b", re.IGNORECASE),
    re.compile(r"\bmistake_step\b", re.IGNORECASE),
]

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


@dataclass(frozen=True)
class RuntimeCard:
    failure_mode: str
    violated_requirement_pattern: str
    risky_next_action_pattern: str
    do: str
    do_not: str
    check_before_next_action: str
    applicable_when: str

    def render(self) -> str:
        return "\n".join(
            [
                "Runtime Failure Card",
                f"Failure mode: {self.failure_mode}",
                f"Violated requirement pattern: {self.violated_requirement_pattern}",
                f"Risky next-action pattern: {self.risky_next_action_pattern}",
                f"Do: {self.do}",
                f"Do not: {self.do_not}",
                f"Check before next action: {self.check_before_next_action}",
                f"Applicable when: {self.applicable_when}",
            ]
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def sanitize_text(text: str, *, forbidden_terms: list[str] | None = None) -> str:
    sanitized = " ".join(text.split())
    sanitized = re.sub(r"\bstep\s*\d+\b", "the critical action", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bmistake_step\b", "critical action", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\boriginally\b", "previously", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\byou will fail\b", "this can fail", sanitized, flags=re.IGNORECASE)
    for term in forbidden_terms or []:
        term = term.strip()
        if not term:
            continue
        sanitized = re.sub(re.escape(term), "[REDACTED_GOLD_ANSWER]", sanitized, flags=re.IGNORECASE)
    return sanitized.strip()


def infer_failure_mode(reason: str) -> str:
    lowered = reason.lower()
    if any(word in lowered for word in ["simulate", "assum", "fabricat"]):
        return "unsupported assumption or fabricated intermediate data"
    if any(word in lowered for word in ["incorrect", "wrong", "inaccurate", "not reliable"]):
        return "unverified or inaccurate factual claim"
    if any(word in lowered for word in ["edge case", "failed to handle", "incomplete"]):
        return "incomplete handling of task constraints or data cases"
    if any(word in lowered for word in ["irrelevant", "click", "website", "loop"]):
        return "irrelevant action or navigation drift"
    if any(word in lowered for word in ["terminate", "premature", "conclude"]):
        return "premature finalization before sufficient verification"
    return "decisive reasoning or execution error"


def runtime_guidance_for_mode(failure_mode: str) -> RuntimeCard:
    if failure_mode == "unsupported assumption or fabricated intermediate data":
        return RuntimeCard(
            failure_mode=failure_mode,
            violated_requirement_pattern=(
                "Claims, examples, measurements, or intermediate values must be grounded in "
                "provided evidence, retrieved evidence, or an explicit computation."
            ),
            risky_next_action_pattern=(
                "The next action would introduce data, examples, measurements, or factual claims "
                "that were not obtained from an available source or computation."
            ),
            do=(
                "Ground the next action in retrieved evidence, a provided file, or an explicit "
                "calculation. If evidence is unavailable, say what must be obtained next."
            ),
            do_not="Do not invent placeholder data or proceed with simulated values.",
            check_before_next_action=(
                "Identify the source or computation supporting each factual value before using it."
            ),
            applicable_when="Use this before providing factual data or derived answers.",
        )
    if failure_mode == "unverified or inaccurate factual claim":
        return RuntimeCard(
            failure_mode=failure_mode,
            violated_requirement_pattern=(
                "Factual claims that later agents may trust must be verified against a relevant "
                "source before handoff or finalization."
            ),
            risky_next_action_pattern=(
                "The next action would pass along a factual claim, citation, price, title, date, "
                "rating, or availability statement that later agents may trust."
            ),
            do="Verify the claim against the relevant source or explicitly mark it as unverified.",
            do_not="Do not hand off or finalize factual claims without a verification step.",
            check_before_next_action=(
                "State the evidence used for the claim and whether it satisfies the task constraints."
            ),
            applicable_when="Use this before making or relaying factual assertions.",
        )
    if failure_mode == "incomplete handling of task constraints or data cases":
        return RuntimeCard(
            failure_mode=failure_mode,
            violated_requirement_pattern=(
                "All stated constraints, filters, exceptions, and edge cases must be preserved "
                "before computation, extraction, or handoff."
            ),
            risky_next_action_pattern=(
                "The next action uses a simplified rule, parser, or checklist that may miss edge "
                "cases in the user request or data."
            ),
            do="Check all stated constraints and edge cases before computing or handing off results.",
            do_not="Do not assume the first obvious parsing or filtering rule covers every row or case.",
            check_before_next_action=(
                "List the constraints being applied and confirm that the next action handles each one."
            ),
            applicable_when="Use this before data extraction, filtering, or constraint-based counting.",
        )
    if failure_mode == "irrelevant action or navigation drift":
        return RuntimeCard(
            failure_mode=failure_mode,
            violated_requirement_pattern=(
                "Each tool, navigation, or handoff action must directly advance an unmet "
                "requirement from the original task."
            ),
            risky_next_action_pattern=(
                "The next action would follow a page, link, tool result, or subtask that is not "
                "directly tied to the original request."
            ),
            do="Re-anchor on the original task and choose the next action that directly resolves it.",
            do_not="Do not continue browsing or acting on irrelevant pages, ads, or tangential results.",
            check_before_next_action=(
                "Explain how the next action advances a specific unmet requirement from the task."
            ),
            applicable_when="Use this during web navigation, tool use, and multi-step search.",
        )
    if failure_mode == "premature finalization before sufficient verification":
        return RuntimeCard(
            failure_mode=failure_mode,
            violated_requirement_pattern=(
                "A final answer or completion signal must wait until the required evidence, "
                "constraints, or calculations have been checked."
            ),
            risky_next_action_pattern="The next action would conclude or terminate before required checks are done.",
            do="Perform the missing verification or explicitly request the information needed.",
            do_not="Do not finalize while key constraints, evidence, or calculations remain unchecked.",
            check_before_next_action="Name the remaining verification step before any final answer.",
            applicable_when="Use this before final answers, termination, or handoff completion.",
        )
    return RuntimeCard(
        failure_mode=failure_mode,
        violated_requirement_pattern=(
            "The next action must be checked against the original task, available evidence, "
            "and the acting agent's role duties."
        ),
        risky_next_action_pattern="The next action may become the decisive point that propagates an error.",
        do="Pause and verify the action against the original task, available evidence, and role duties.",
        do_not="Do not proceed if the action relies on an unchecked assumption.",
        check_before_next_action="State the evidence and constraint check supporting the next action.",
        applicable_when="Use this before any action that other agents will rely on.",
    )


def build_runtime_card(case: WhoWhenCase) -> RuntimeCard:
    reason = sanitize_text(case.mistake_reason, forbidden_terms=[case.ground_truth])
    failure_mode = infer_failure_mode(reason)
    return runtime_guidance_for_mode(failure_mode)


def _compact_reason(reason: str, *, max_chars: int = 260) -> str:
    compact = " ".join(reason.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def build_oracle_specific_card(case: WhoWhenCase) -> RuntimeCard:
    reason = sanitize_text(case.mistake_reason, forbidden_terms=[case.ground_truth])
    failure_mode = infer_failure_mode(reason)
    mode_card = runtime_guidance_for_mode(failure_mode)
    diagnostic_pattern = _compact_reason(reason)
    return RuntimeCard(
        failure_mode=failure_mode,
        violated_requirement_pattern=(
            "In this class of failures, the acting agent must guard against this diagnostic "
            f"pattern: {diagnostic_pattern}"
        ),
        risky_next_action_pattern=mode_card.risky_next_action_pattern,
        do=mode_card.do,
        do_not=mode_card.do_not,
        check_before_next_action=mode_card.check_before_next_action,
        applicable_when=mode_card.applicable_when,
    )


def build_broad_verification_card() -> RuntimeCard:
    return RuntimeCard(
        failure_mode="general verification and constraint preservation",
        violated_requirement_pattern=(
            "Any next action can fail if it carries forward unchecked facts, assumptions, "
            "constraints, calculations, or handoff requirements."
        ),
        risky_next_action_pattern=(
            "The next action would proceed without explicitly checking evidence, task constraints, "
            "and role responsibilities."
        ),
        do=(
            "Before acting, verify the evidence or computation supporting the next step and check "
            "that it preserves all stated task constraints."
        ),
        do_not="Do not rely on unchecked assumptions, incomplete context, or unsupported factual claims.",
        check_before_next_action=(
            "What evidence, constraint, or role requirement could make this next action wrong?"
        ),
        applicable_when="Use this before any next action in a multi-agent task.",
    )


def leakage_flags(text: str, *, case: WhoWhenCase) -> list[str]:
    flags: list[str] = []
    normalized_text = " ".join(text.lower().split())
    for pattern in STEP_PATTERNS:
        if pattern.search(text):
            flags.append("mentions_exact_step_or_hidden_step_marker")
            break
    if "you will fail" in text.lower():
        flags.append("future_failure_wording")
    if case.ground_truth and case.ground_truth in text:
        flags.append("contains_ground_truth")
    failed_action = case.content_at(case.mistake_step or -1)
    normalized_failed_action = " ".join(failed_action.lower().split())
    if failed_action and normalized_failed_action and normalized_failed_action in normalized_text:
        flags.append("quotes_original_failed_action")
    failed_tokens = TOKEN_RE.findall(normalized_failed_action)
    normalized_text_tokens = TOKEN_RE.findall(normalized_text)
    text_token_set = set(normalized_text_tokens)
    if len(failed_tokens) >= 12 and text_token_set:
        overlap = sum(1 for token in failed_tokens if token in text_token_set) / len(failed_tokens)
        if overlap >= 0.45:
            flags.append("high_token_overlap_with_original_failed_action")
    if len(failed_tokens) >= 8:
        text_ngrams = {
            tuple(normalized_text_tokens[idx : idx + 6])
            for idx in range(max(0, len(normalized_text_tokens) - 5))
        }
        failed_ngrams = {
            tuple(failed_tokens[idx : idx + 6]) for idx in range(max(0, len(failed_tokens) - 5))
        }
        if text_ngrams & failed_ngrams:
            flags.append("shared_long_phrase_with_original_failed_action")
    return flags


def render_condition(
    condition: str,
    *,
    case: WhoWhenCase,
    mismatched_case: WhoWhenCase | None = None,
) -> tuple[str, dict[str, object]]:
    if condition == "no_guidance":
        return "", {"condition_source": "none"}
    if condition == "coarse_reflection":
        text = "\n".join(
            [
                "Coarse reflection prompt:",
                "This trajectory may be heading toward a mistake.",
                "Before producing the next action, reflect on what could go wrong and avoid it.",
                "No specific responsible agent, step, or failure explanation is provided.",
            ]
        )
        return text, {"condition_source": "coarse_reflection"}
    if condition == "broad_verification_card":
        card = build_broad_verification_card()
        return card.render(), {"condition_source": "broad_verification_card", "card": card.to_dict()}
    if condition == "strong_generic_guideline":
        text = "\n".join(
            [
                "General execution guideline:",
                "- Preserve all user constraints and required evidence.",
                "- Verify factual claims, calculations, and tool outputs before relying on them.",
                "- If information is missing or uncertain, ask for clarification or gather evidence.",
                "- Do not finalize until the next action is grounded in the task context.",
            ]
        )
        return text, {"condition_source": "generic"}
    if condition == "sanitized_raw_gold_explanation":
        text = "Prior failure pattern to avoid: " + sanitize_text(
            case.mistake_reason,
            forbidden_terms=[case.ground_truth],
        )
        return text, {"condition_source": "gold_reason_sanitized"}
    if condition == "oracle_runtime_card":
        card = build_runtime_card(case)
        return card.render(), {"condition_source": "oracle_runtime_card", "card": card.to_dict()}
    if condition == "oracle_specific_card":
        card = build_oracle_specific_card(case)
        return card.render(), {"condition_source": "oracle_specific_card", "card": card.to_dict()}
    if condition == "wrong_mismatched_card":
        source = mismatched_case or case
        card = build_runtime_card(source)
        return card.render(), {
            "condition_source": "mismatched_runtime_card",
            "mismatched_source_case_id": source.case_id,
            "card": card.to_dict(),
        }
    if condition == "hard_mismatched_card":
        if mismatched_case is None or mismatched_case.case_id == case.case_id:
            raise ValueError(f"No hard mismatched source case available for {case.case_id}.")
        card = build_oracle_specific_card(mismatched_case)
        return card.render(), {
            "condition_source": "hard_mismatched_card",
            "mismatched_source_case_id": mismatched_case.case_id,
            "mismatched_source_failure_mode": infer_failure_mode(
                sanitize_text(mismatched_case.mistake_reason, forbidden_terms=[mismatched_case.ground_truth])
            ),
            "card": card.to_dict(),
        }
    raise ValueError(f"Unknown condition: {condition}")
