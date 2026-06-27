from __future__ import annotations

from pathlib import Path
from typing import Any

from ww_card_poc.conditions import (
    build_broad_verification_card,
    build_mode_only_card,
    leakage_flags,
    sanitize_text,
)
from ww_card_poc.generation_runner import read_jsonl
from ww_card_poc.phase2a_inputs import (
    Phase2AInput,
    _system_prompt,
    build_user_prompt,
    write_phase2a_inputs,
)
from ww_card_poc.who_when_io import WhoWhenCase


DEFAULT_EXP4_CONDITIONS = [
    "no_guidance",
    "coarse_reflection_from_source",
    "broad_verification_card",
    "raw_source_explanation",
    "source_mode_only_placebo",
    "source_oracle_abstracted_card",
    "source_hard_mismatched_abstracted_card",
]


def _cases_by_id(cases: list[WhoWhenCase]) -> dict[str, WhoWhenCase]:
    return {case.case_id: case for case in cases}


def _accepted_audits(audit_path: Path) -> list[dict[str, Any]]:
    return [record for record in read_jsonl(audit_path) if record.get("accepted")]


def _source_for_target(
    target: dict[str, Any],
    audits: list[dict[str, Any]],
) -> dict[str, Any] | None:
    target_id = str(target.get("case_id") or "")
    target_mode = str(target.get("target_failure_mode") or "")
    for candidate in audits:
        if str(candidate.get("case_id") or "") == target_id:
            continue
        if str(candidate.get("target_failure_mode") or "") == target_mode:
            return candidate
    return None


def _coarse_reflection_text(source: dict[str, Any]) -> str:
    source_mode = str(source.get("target_failure_mode") or "a prior failure mode")
    return "\n".join(
        [
            "Coarse source-memory prompt:",
            "A prior trajectory with a related abstract failure mode did not succeed.",
            f"Related failure category: {source_mode}",
            "Before producing the next action, reflect on what could go wrong and avoid it.",
            "No source-specific who, when, or detailed failure explanation is provided.",
        ]
    )


def _raw_source_explanation(source_case: WhoWhenCase) -> str:
    return "Prior source failure explanation to consider:\n" + sanitize_text(
        source_case.mistake_reason,
        forbidden_terms=[source_case.ground_truth],
    )


def _condition_text(
    *,
    condition: str,
    source_audit: dict[str, Any],
    target_audit: dict[str, Any],
    source_case: WhoWhenCase,
) -> tuple[str, dict[str, Any]]:
    if condition == "no_guidance":
        return "", {"condition_source": "none"}
    if condition == "coarse_reflection_from_source":
        return _coarse_reflection_text(source_audit), {"condition_source": condition}
    if condition == "broad_verification_card":
        card = build_broad_verification_card()
        return card.render(), {"condition_source": condition, "card": card.to_dict()}
    if condition == "raw_source_explanation":
        return _raw_source_explanation(source_case), {"condition_source": condition}
    if condition == "source_mode_only_placebo":
        card = build_mode_only_card(str(source_audit.get("target_failure_mode") or "unknown"))
        return card.render(), {"condition_source": condition, "card": card.to_dict()}
    if condition == "source_oracle_abstracted_card":
        card_text = str(source_audit["oracle_abstracted"]["card_text"])
        return card_text, {
            "condition_source": condition,
            "card_source_case_id": source_audit.get("case_id", ""),
        }
    if condition == "source_hard_mismatched_abstracted_card":
        card_text = str(target_audit["hard_mismatched_abstracted"]["card_text"])
        return card_text, {
            "condition_source": condition,
            "card_source_case_id": target_audit.get("mismatch_source_case_id", ""),
        }
    raise ValueError(f"Unknown Experiment 4 condition: {condition}")


def build_exp4_inputs_from_audit(
    *,
    audit_path: Path,
    output_path: Path,
    cases: list[WhoWhenCase],
    conditions: list[str] | None = None,
    limit: int | None = None,
) -> list[Phase2AInput]:
    audits = _accepted_audits(audit_path)
    if limit is not None:
        audits = audits[:limit]
    by_case = _cases_by_id(cases)
    active_conditions = conditions or DEFAULT_EXP4_CONDITIONS
    records: list[Phase2AInput] = []

    for target_audit in audits:
        target_case = by_case.get(str(target_audit.get("case_id") or ""))
        if target_case is None or target_case.mistake_step is None:
            continue
        source_audit = _source_for_target(target_audit, audits)
        if source_audit is None:
            continue
        source_case = by_case.get(str(source_audit.get("case_id") or ""))
        if source_case is None:
            continue

        for condition in active_conditions:
            condition_text, condition_metadata = _condition_text(
                condition=condition,
                source_audit=source_audit,
                target_audit=target_audit,
                source_case=source_case,
            )
            metadata = {
                **condition_metadata,
                "experiment": "exp4",
                "judge_mode": "decoupled",
                "target_failure_mode": target_audit.get("target_failure_mode", ""),
                "target_missing_check_type": target_audit["oracle_abstracted"].get(
                    "missing_check_type", ""
                ),
                "target_abstract_corrective_action": target_audit["oracle_abstracted"].get(
                    "abstract_corrective_action", ""
                ),
                "source_case_id": source_audit.get("case_id", ""),
                "source_failure_mode": source_audit.get("target_failure_mode", ""),
                "source_missing_check_type": source_audit["oracle_abstracted"].get(
                    "missing_check_type", ""
                ),
                "mismatch_source_case_id": target_audit.get("mismatch_source_case_id", ""),
                "mismatch_source_failure_mode": target_audit.get(
                    "mismatch_source_failure_mode", ""
                ),
                "oracle_retrieval_upper_bound": True,
            }
            run_id = f"exp4__{target_case.case_id.replace(':', '_')}__{condition}"
            records.append(
                Phase2AInput(
                    run_id=run_id,
                    case_id=target_case.case_id,
                    condition=condition,
                    source_path=str(target_case.path),
                    responsible_agent=target_case.mistake_agent,
                    intervention_step=target_case.mistake_step,
                    prefix_len=len(target_case.prefix_before_mistake()),
                    system_prompt=_system_prompt(target_case),
                    user_prompt=build_user_prompt(target_case, condition_text),
                    condition_text=condition_text,
                    leakage_flags=leakage_flags(condition_text, case=target_case),
                    metadata=metadata,
                )
            )
    write_phase2a_inputs(records, output_path)
    return records
