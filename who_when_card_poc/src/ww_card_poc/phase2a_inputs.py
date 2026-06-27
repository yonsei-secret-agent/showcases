from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from ww_card_poc.conditions import (
    DEFAULT_CONDITIONS,
    infer_failure_mode,
    leakage_flags,
    render_condition,
    sanitize_text,
)
from ww_card_poc.who_when_io import WhoWhenCase


@dataclass(frozen=True)
class Phase2AInput:
    run_id: str
    case_id: str
    condition: str
    source_path: str
    responsible_agent: str
    intervention_step: int
    prefix_len: int
    system_prompt: str
    user_prompt: str
    condition_text: str
    leakage_flags: list[str]
    metadata: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


def _agent_roster(case: WhoWhenCase) -> str:
    system_agents = case.system_prompt_agents()
    history_agents = case.distinct_history_agents()
    agents = system_agents or history_agents
    return ", ".join(agents)


def _history_prefix_text(case: WhoWhenCase) -> str:
    lines: list[str] = []
    for idx, entry in enumerate(case.prefix_before_mistake()):
        agent = str(entry.get("name") or entry.get("role") or "Unknown")
        content = " ".join(str(entry.get("content", "")).split())
        lines.append(f"Step {idx} - {agent}: {content}")
    if not lines:
        return "(No prior trajectory steps. The next action is the first agent action.)"
    return "\n".join(lines)


def _system_prompt(case: WhoWhenCase) -> str:
    role_prompt = case.system_prompt.get(case.mistake_agent, "")
    if role_prompt:
        return role_prompt
    return (
        f"You are the original agent named {case.mistake_agent}. Continue the multi-agent "
        "task from the provided prefix and produce only your next message/action."
    )


def build_user_prompt(case: WhoWhenCase, condition_text: str) -> str:
    guidance = condition_text.strip() or "No additional guidance is provided."
    return "\n\n".join(
        [
            "You are continuing a multi-agent trajectory from a prefix.",
            "Original task:\n" + case.question,
            "Agent roster:\n" + (_agent_roster(case) or "(unknown)"),
            "Trajectory prefix before your next action:\n" + _history_prefix_text(case),
            "Guidance for this run:\n" + guidance,
            (
                "Instruction:\n"
                f"Produce the next message/action as {case.mistake_agent}. "
                "Do not mention hidden labels, benchmark setup, mistake steps, or evaluation. "
                "Do not summarize the trajectory; continue it with the next useful action."
            ),
        ]
    )


def _failure_mode(case: WhoWhenCase) -> str:
    return infer_failure_mode(sanitize_text(case.mistake_reason, forbidden_terms=[case.ground_truth]))


ORTHOGONAL_MODE_PREFERENCES = {
    "unsupported assumption or fabricated intermediate data": [
        "irrelevant action or navigation drift",
        "premature finalization before sufficient verification",
        "incomplete handling of task constraints or data cases",
    ],
    "unverified or inaccurate factual claim": [
        "irrelevant action or navigation drift",
        "premature finalization before sufficient verification",
        "incomplete handling of task constraints or data cases",
    ],
    "incomplete handling of task constraints or data cases": [
        "irrelevant action or navigation drift",
        "unsupported assumption or fabricated intermediate data",
        "premature finalization before sufficient verification",
    ],
    "irrelevant action or navigation drift": [
        "incomplete handling of task constraints or data cases",
        "unsupported assumption or fabricated intermediate data",
        "unverified or inaccurate factual claim",
    ],
    "premature finalization before sufficient verification": [
        "irrelevant action or navigation drift",
        "incomplete handling of task constraints or data cases",
        "unsupported assumption or fabricated intermediate data",
    ],
    "decisive reasoning or execution error": [
        "irrelevant action or navigation drift",
        "incomplete handling of task constraints or data cases",
        "unsupported assumption or fabricated intermediate data",
    ],
}


def _mismatched_case(case: WhoWhenCase, cases: list[WhoWhenCase]) -> WhoWhenCase | None:
    target_mode = _failure_mode(case)
    by_mode: dict[str, list[WhoWhenCase]] = {}
    for candidate in cases:
        if candidate.case_id == case.case_id:
            continue
        by_mode.setdefault(_failure_mode(candidate), []).append(candidate)

    for preferred_mode in ORTHOGONAL_MODE_PREFERENCES.get(target_mode, []):
        candidates = by_mode.get(preferred_mode, [])
        if candidates:
            return candidates[0]
    return None


def build_phase2a_inputs(
    cases: list[WhoWhenCase],
    *,
    conditions: list[str] | None = None,
    mismatch_pool: list[WhoWhenCase] | None = None,
    block_leakage: bool = True,
) -> list[Phase2AInput]:
    active_conditions = conditions or DEFAULT_CONDITIONS
    mismatch_candidates = mismatch_pool or cases
    records: list[Phase2AInput] = []
    for case in cases:
        mismatched_case = _mismatched_case(case, mismatch_candidates)
        case_records: list[Phase2AInput] = []
        blocked_by_leakage = False
        for condition in active_conditions:
            condition_text, metadata = render_condition(
                condition,
                case=case,
                mismatched_case=mismatched_case,
            )
            flags = leakage_flags(condition_text, case=case)
            if block_leakage and flags:
                blocked_by_leakage = True
                break
            step = case.mistake_step
            if step is None:
                continue
            run_id = f"phase2a__{case.case_id.replace(':', '_')}__{condition}"
            case_records.append(
                Phase2AInput(
                    run_id=run_id,
                    case_id=case.case_id,
                    condition=condition,
                    source_path=str(case.path),
                    responsible_agent=case.mistake_agent,
                    intervention_step=step,
                    prefix_len=len(case.prefix_before_mistake()),
                    system_prompt=_system_prompt(case),
                    user_prompt=build_user_prompt(case, condition_text),
                    condition_text=condition_text,
                    leakage_flags=flags,
                    metadata={
                        **metadata,
                        "question_id": case.question_id,
                        "dataset_type": case.dataset_type,
                        "history_len": case.history_len,
                        "target_failure_mode": _failure_mode(case),
                        "mistake_reason": case.mistake_reason,
                        "leakage_blocked": False,
                    },
                )
            )
        if not blocked_by_leakage:
            records.extend(case_records)
    return records


def write_phase2a_inputs(records: list[Phase2AInput], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(record.to_json() for record in records) + ("\n" if records else ""),
        encoding="utf-8",
    )
