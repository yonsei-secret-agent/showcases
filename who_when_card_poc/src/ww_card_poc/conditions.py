from __future__ import annotations

from dataclasses import asdict, dataclass
import re

from ww_card_poc.who_when_io import WhoWhenCase


DEFAULT_CONDITIONS = [
    "no_guidance",
    "strong_generic_guideline",
    "sanitized_raw_gold_explanation",
    "oracle_runtime_card",
    "wrong_mismatched_card",
]


STEP_PATTERNS = [
    re.compile(r"\bstep\s*\d+\b", re.IGNORECASE),
    re.compile(r"\bt\*\b", re.IGNORECASE),
    re.compile(r"\bmistake_step\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class RuntimeCard:
    failure_mode: str
    trigger_pattern: str
    do: str
    do_not: str
    check_before_next_action: str
    applicable_when: str

    def render(self) -> str:
        return "\n".join(
            [
                "Runtime Failure Card",
                f"Failure mode: {self.failure_mode}",
                f"Trigger pattern: {self.trigger_pattern}",
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


def build_runtime_card(case: WhoWhenCase) -> RuntimeCard:
    reason = sanitize_text(case.mistake_reason, forbidden_terms=[case.ground_truth])
    failure_mode = infer_failure_mode(reason)
    return RuntimeCard(
        failure_mode=failure_mode,
        trigger_pattern=reason or "The next action may carry forward an unverified assumption.",
        do=(
            "Before acting, verify the relevant evidence, constraints, and intermediate result "
            "against the original task."
        ),
        do_not=(
            "Do not proceed with assumed, simulated, or unverified information when the task "
            "requires grounded evidence or exact computation."
        ),
        check_before_next_action=(
            "State what evidence or computation supports the next action, and if it is missing, "
            "request or obtain it before continuing."
        ),
        applicable_when=(
            "Use this when the next response would introduce data, facts, tool results, or a "
            "decision that later agents may rely on."
        ),
    )


def leakage_flags(text: str, *, case: WhoWhenCase) -> list[str]:
    flags: list[str] = []
    for pattern in STEP_PATTERNS:
        if pattern.search(text):
            flags.append("mentions_exact_step_or_hidden_step_marker")
            break
    if "you will fail" in text.lower():
        flags.append("future_failure_wording")
    if case.ground_truth and case.ground_truth in text:
        flags.append("contains_ground_truth")
    if case.content_at(case.mistake_step or -1) and case.content_at(case.mistake_step or -1) in text:
        flags.append("quotes_original_failed_action")
    return flags


def render_condition(
    condition: str,
    *,
    case: WhoWhenCase,
    mismatched_case: WhoWhenCase | None = None,
) -> tuple[str, dict[str, object]]:
    if condition == "no_guidance":
        return "", {"condition_source": "none"}
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
    if condition == "wrong_mismatched_card":
        source = mismatched_case or case
        card = build_runtime_card(source)
        return card.render(), {
            "condition_source": "mismatched_runtime_card",
            "mismatched_source_case_id": source.case_id,
            "card": card.to_dict(),
        }
    raise ValueError(f"Unknown condition: {condition}")
