from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from ww_card_poc.conditions import (
    RuntimeCard,
    build_abstracted_card,
    build_broad_verification_card,
    build_mode_only_card,
    build_oracle_specific_card,
    infer_failure_mode,
    leakage_flags,
    sanitize_text,
)
from ww_card_poc.generation_runner import read_jsonl
from ww_card_poc.model_client import ModelClient, ModelClientError
from ww_card_poc.phase2a_inputs import (
    Phase2AInput,
    _failure_mode,
    _mismatched_case,
    _system_prompt,
    build_user_prompt,
    write_phase2a_inputs,
)
from ww_card_poc.settings import Settings
from ww_card_poc.who_when_io import WhoWhenCase


ALLOWED_FAILURE_MODES = [
    "unsupported assumption or fabricated intermediate data",
    "unverified or inaccurate factual claim",
    "incomplete handling of task constraints or data cases",
    "irrelevant action or navigation drift",
    "premature finalization before sufficient verification",
    "decisive reasoning or execution error",
]


@dataclass(frozen=True)
class AbstractCardArtifact:
    case_id: str
    source_path: str
    failure_mode: str
    missing_check_type: str
    abstract_failure_pattern: str
    abstract_corrective_action: str
    check_before_next_action: str
    applicable_when: str
    removed_literal_terms: list[str]
    abstraction_level: str
    abstractiveness_rationale: str
    raw_model_text: str
    error: str

    def card(self) -> RuntimeCard:
        return build_abstracted_card(
            failure_mode=self.failure_mode,
            missing_check_type=self.missing_check_type,
            abstract_failure_pattern=self.abstract_failure_pattern,
            abstract_corrective_action=self.abstract_corrective_action,
            check_before_next_action=self.check_before_next_action,
            applicable_when=self.applicable_when,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["card"] = self.card().to_dict() if not self.error else {}
        payload["card_text"] = self.card().render() if not self.error else ""
        return payload


@dataclass(frozen=True)
class Exp3AuditRecord:
    case_id: str
    source_path: str
    target_failure_mode: str
    mismatch_source_case_id: str
    mismatch_source_failure_mode: str
    oracle_abstracted: dict[str, Any]
    hard_mismatched_abstracted: dict[str, Any]
    correct_mode_only_card: dict[str, Any]
    broad_verification_card: dict[str, Any]
    exact_leakage_flags: list[str]
    manipulation_audit: dict[str, Any]
    mismatch_manipulation_audit: dict[str, Any]
    accepted: bool
    reject_reasons: list[str]
    model: str
    created_at: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return json.loads(stripped[start : end + 1])
    raise ValueError("model response did not contain JSON")


def _cases_by_id(cases: list[WhoWhenCase]) -> dict[str, WhoWhenCase]:
    return {case.case_id: case for case in cases}


def case_ids_from_input(input_path: Path) -> list[str]:
    seen: set[str] = set()
    case_ids: list[str] = []
    for record in read_jsonl(input_path):
        case_id = str(record.get("case_id") or "")
        if case_id and case_id not in seen:
            seen.add(case_id)
            case_ids.append(case_id)
    return case_ids


def _source_terms(case: WhoWhenCase) -> list[str]:
    terms = [
        case.ground_truth,
        case.question,
        case.content_at(case.mistake_step or -1),
    ]
    return [term for term in terms if term]


def _abstract_card_prompt(case: WhoWhenCase) -> list[dict[str, str]]:
    reason = sanitize_text(case.mistake_reason, forbidden_terms=[case.ground_truth])
    failure_mode = infer_failure_mode(reason)
    failed_action = case.content_at(case.mistake_step or -1)
    user_prompt = "\n\n".join(
        [
            "Create an abstract runtime Failure Card for a multi-agent failure.",
            "The card must be narrower than a generic verification reminder but must not reveal literal source-case details.",
            "Target granularity: failure-mode pattern + missing-check type + abstract corrective action.",
            "Do not include exact step numbers, original failed-action wording, gold answers, entity names, answer-like values, or benchmark labels.",
            "Use the provided failure mode exactly.",
            f"Allowed failure modes: {ALLOWED_FAILURE_MODES}",
            "Original task, for identifying literal terms to remove:\n" + case.question,
            "Gold answer / ground truth, forbidden in output:\n" + case.ground_truth,
            "Hidden original failed action, forbidden to quote or closely paraphrase:\n" + failed_action,
            "Sanitized diagnostic reason:\n" + reason,
            f"Failure mode:\n{failure_mode}",
            (
                "Return JSON only with keys: failure_mode, missing_check_type, "
                "abstract_failure_pattern, abstract_corrective_action, check_before_next_action, "
                "applicable_when, removed_literal_terms, abstraction_level, abstractiveness_rationale. "
                "abstraction_level must be one of: mode_only, check_type, action_schema, too_literal."
            ),
        ]
    )
    return [
        {
            "role": "system",
            "content": (
                "You generate non-leaky abstract failure-memory cards. Output valid JSON only."
            ),
        },
        {"role": "user", "content": user_prompt},
    ]


def generate_abstract_card(
    *,
    client: ModelClient,
    settings: Settings,
    case: WhoWhenCase,
) -> AbstractCardArtifact:
    try:
        response = client.complete(
            model=settings.models.card_model,
            messages=_abstract_card_prompt(case),
            temperature=settings.models.card_temperature,
            max_tokens=settings.models.max_output_tokens,
            seed=settings.experiment_seed,
        )
        parsed = _extract_json(response.content)
        failure_mode = str(parsed.get("failure_mode") or _failure_mode(case))
        if failure_mode not in ALLOWED_FAILURE_MODES:
            failure_mode = _failure_mode(case)
        removed = parsed.get("removed_literal_terms") or []
        removed_terms = [str(item) for item in removed] if isinstance(removed, list) else [str(removed)]
        return AbstractCardArtifact(
            case_id=case.case_id,
            source_path=str(case.path),
            failure_mode=failure_mode,
            missing_check_type=str(parsed.get("missing_check_type") or "abstract check"),
            abstract_failure_pattern=str(
                parsed.get("abstract_failure_pattern") or "A required abstract check may be missing."
            ),
            abstract_corrective_action=str(
                parsed.get("abstract_corrective_action") or "Perform the missing abstract check before acting."
            ),
            check_before_next_action=str(
                parsed.get("check_before_next_action") or "What required check is still missing?"
            ),
            applicable_when=str(parsed.get("applicable_when") or "Use before the next action."),
            removed_literal_terms=removed_terms,
            abstraction_level=str(parsed.get("abstraction_level") or "check_type"),
            abstractiveness_rationale=str(parsed.get("abstractiveness_rationale") or ""),
            raw_model_text=response.content,
            error="",
        )
    except (ModelClientError, ValueError, json.JSONDecodeError) as exc:
        return AbstractCardArtifact(
            case_id=case.case_id,
            source_path=str(case.path),
            failure_mode=_failure_mode(case),
            missing_check_type="",
            abstract_failure_pattern="",
            abstract_corrective_action="",
            check_before_next_action="",
            applicable_when="",
            removed_literal_terms=[],
            abstraction_level="",
            abstractiveness_rationale="",
            raw_model_text="",
            error=str(exc),
        )


def _audit_prompt(
    *,
    case: WhoWhenCase,
    artifact: AbstractCardArtifact,
    broad_card_text: str,
) -> list[dict[str, str]]:
    card_text = artifact.card().render() if not artifact.error else ""
    failed_action = case.content_at(case.mistake_step or -1)
    user_prompt = "\n\n".join(
        [
            "Audit this abstract Failure Card before it is used in an experiment.",
            "The card should preserve the intended failure mode and missing-check type, but must not leak literal source details.",
            "Source task:\n" + case.question,
            "Forbidden gold answer / ground truth:\n" + case.ground_truth,
            "Forbidden original failed action:\n" + failed_action,
            "Hidden diagnostic reason:\n" + case.mistake_reason,
            "Intended failure mode:\n" + artifact.failure_mode,
            "Intended missing_check_type:\n" + artifact.missing_check_type,
            "Broad baseline card:\n" + broad_card_text,
            "Abstract card:\n" + card_text,
            (
                "Return JSON only with keys: leakage (boolean), leakage_severity "
                "(none|low|medium|high), leakage_flags (array), mode_recoverable (boolean), "
                "missing_check_recoverable (boolean), distinct_from_broad (boolean), "
                "too_literal (boolean), too_generic (boolean), rationale (string)."
            ),
        ]
    )
    return [
        {"role": "system", "content": "You are a strict experiment-validity auditor. Output valid JSON only."},
        {"role": "user", "content": user_prompt},
    ]


def audit_abstract_card(
    *,
    client: ModelClient,
    settings: Settings,
    case: WhoWhenCase,
    artifact: AbstractCardArtifact,
    broad_card_text: str,
) -> dict[str, Any]:
    try:
        response = client.complete(
            model=settings.models.judge_model,
            messages=_audit_prompt(case=case, artifact=artifact, broad_card_text=broad_card_text),
            temperature=settings.models.judge_temperature,
            max_tokens=settings.models.max_output_tokens,
            seed=settings.experiment_seed,
        )
        parsed = _extract_json(response.content)
        parsed["raw_text"] = response.content
        return parsed
    except (ModelClientError, ValueError, json.JSONDecodeError) as exc:
        return {"error": str(exc), "raw_text": ""}


def _reject_reasons(
    *,
    artifact: AbstractCardArtifact,
    exact_flags: list[str],
    audit: dict[str, Any],
    mismatch_artifact: AbstractCardArtifact,
    mismatch_audit: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if artifact.error:
        reasons.append(f"oracle_card_error:{artifact.error}")
    if mismatch_artifact.error:
        reasons.append(f"mismatch_card_error:{mismatch_artifact.error}")
    if exact_flags:
        reasons.append("exact_leakage_flags")
    for prefix, parsed in [("oracle", audit), ("mismatch", mismatch_audit)]:
        if parsed.get("error"):
            reasons.append(f"{prefix}_audit_error")
        if parsed.get("leakage") and str(parsed.get("leakage_severity")) in {"medium", "high"}:
            reasons.append(f"{prefix}_leakage")
        if not parsed.get("mode_recoverable"):
            reasons.append(f"{prefix}_mode_not_recoverable")
        if not parsed.get("missing_check_recoverable"):
            reasons.append(f"{prefix}_missing_check_not_recoverable")
        if not parsed.get("distinct_from_broad"):
            reasons.append(f"{prefix}_not_distinct_from_broad")
        if parsed.get("too_literal"):
            reasons.append(f"{prefix}_too_literal")
        if parsed.get("too_generic"):
            reasons.append(f"{prefix}_too_generic")
    if artifact.abstraction_level not in {"check_type", "action_schema"}:
        reasons.append(f"oracle_bad_abstraction_level:{artifact.abstraction_level}")
    return reasons


def run_exp3a_audit(
    *,
    settings: Settings,
    cases: list[WhoWhenCase],
    case_ids: list[str],
    output_path: Path,
    limit: int | None = None,
) -> list[Exp3AuditRecord]:
    by_case = _cases_by_id(cases)
    selected = [by_case[case_id] for case_id in case_ids if case_id in by_case]
    if limit is not None:
        selected = selected[:limit]
    mismatch_pool = [case for case in cases if case.dataset_type == "algorithm_generated"]
    client = ModelClient(settings)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    broad_card = build_broad_verification_card()
    broad_text = broad_card.render()
    written: list[Exp3AuditRecord] = []

    with output_path.open("w", encoding="utf-8") as handle:
        for case in selected:
            mismatch = _mismatched_case(case, mismatch_pool)
            oracle_artifact = generate_abstract_card(client=client, settings=settings, case=case)
            mismatch_artifact = (
                generate_abstract_card(client=client, settings=settings, case=mismatch)
                if mismatch is not None
                else AbstractCardArtifact(
                    case_id="",
                    source_path="",
                    failure_mode="",
                    missing_check_type="",
                    abstract_failure_pattern="",
                    abstract_corrective_action="",
                    check_before_next_action="",
                    applicable_when="",
                    removed_literal_terms=[],
                    abstraction_level="",
                    abstractiveness_rationale="",
                    raw_model_text="",
                    error="no hard mismatched source",
                )
            )
            exact_flags = leakage_flags(oracle_artifact.card().render(), case=case) if not oracle_artifact.error else []
            if mismatch is not None and not mismatch_artifact.error:
                exact_flags.extend(
                    f"mismatch_source:{flag}"
                    for flag in leakage_flags(mismatch_artifact.card().render(), case=mismatch)
                )
            audit = audit_abstract_card(
                client=client,
                settings=settings,
                case=case,
                artifact=oracle_artifact,
                broad_card_text=broad_text,
            )
            mismatch_audit = (
                audit_abstract_card(
                    client=client,
                    settings=settings,
                    case=mismatch,
                    artifact=mismatch_artifact,
                    broad_card_text=broad_text,
                )
                if mismatch is not None
                else {"error": "no hard mismatched source"}
            )
            reject_reasons = _reject_reasons(
                artifact=oracle_artifact,
                exact_flags=exact_flags,
                audit=audit,
                mismatch_artifact=mismatch_artifact,
                mismatch_audit=mismatch_audit,
            )
            record = Exp3AuditRecord(
                case_id=case.case_id,
                source_path=str(case.path),
                target_failure_mode=_failure_mode(case),
                mismatch_source_case_id=mismatch.case_id if mismatch is not None else "",
                mismatch_source_failure_mode=_failure_mode(mismatch) if mismatch is not None else "",
                oracle_abstracted=oracle_artifact.to_dict(),
                hard_mismatched_abstracted=mismatch_artifact.to_dict(),
                correct_mode_only_card=build_mode_only_card(_failure_mode(case)).to_dict(),
                broad_verification_card=broad_card.to_dict(),
                exact_leakage_flags=exact_flags,
                manipulation_audit=audit,
                mismatch_manipulation_audit=mismatch_audit,
                accepted=not reject_reasons,
                reject_reasons=reject_reasons,
                model=settings.models.card_model,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            handle.write(record.to_json() + "\n")
            handle.flush()
            written.append(record)
    return written


def _audit_records(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(path)


def build_exp3b_inputs_from_audit(
    *,
    audit_path: Path,
    output_path: Path,
    cases: list[WhoWhenCase],
    conditions: list[str],
) -> list[Phase2AInput]:
    by_case = _cases_by_id(cases)
    records: list[Phase2AInput] = []
    for audit in _audit_records(audit_path):
        if not audit.get("accepted"):
            continue
        case = by_case.get(str(audit.get("case_id")))
        if case is None or case.mistake_step is None:
            continue
        condition_texts = {
            "broad_verification_card": build_broad_verification_card().render(),
            "correct_mode_only_placebo": build_mode_only_card(
                str(audit.get("target_failure_mode") or "")
            ).render(),
            "oracle_abstracted_card": str(audit["oracle_abstracted"]["card_text"]),
            "hard_mismatched_abstracted_card": str(audit["hard_mismatched_abstracted"]["card_text"]),
            "oracle_specific_card_current": build_oracle_specific_card(case).render(),
        }
        for condition in conditions:
            condition_text = condition_texts[condition]
            metadata = {
                "experiment": "exp3",
                "judge_mode": "decoupled",
                "target_failure_mode": audit.get("target_failure_mode", ""),
                "target_missing_check_type": audit["oracle_abstracted"].get("missing_check_type", ""),
                "target_abstract_corrective_action": audit["oracle_abstracted"].get(
                    "abstract_corrective_action", ""
                ),
                "mismatch_source_case_id": audit.get("mismatch_source_case_id", ""),
                "mismatch_source_failure_mode": audit.get("mismatch_source_failure_mode", ""),
                "abstraction_level": audit["oracle_abstracted"].get("abstraction_level", ""),
                "condition_source": condition,
            }
            run_id = f"exp3__{case.case_id.replace(':', '_')}__{condition}"
            records.append(
                Phase2AInput(
                    run_id=run_id,
                    case_id=case.case_id,
                    condition=condition,
                    source_path=str(case.path),
                    responsible_agent=case.mistake_agent,
                    intervention_step=case.mistake_step,
                    prefix_len=len(case.prefix_before_mistake()),
                    system_prompt=_system_prompt(case),
                    user_prompt=build_user_prompt(case, condition_text),
                    condition_text=condition_text,
                    leakage_flags=leakage_flags(condition_text, case=case),
                    metadata=metadata,
                )
            )
    write_phase2a_inputs(records, output_path)
    return records
