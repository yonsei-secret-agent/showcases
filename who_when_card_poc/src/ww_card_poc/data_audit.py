from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path

from ww_card_poc.who_when_io import WhoWhenCase, case_index_row, load_cases, phase2a_status


CASE_INDEX_FIELDS = [
    "case_id",
    "dataset_type",
    "source_path",
    "question_id",
    "history_len",
    "mistake_agent",
    "mistake_step",
    "mistake_step_valid",
    "mistake_entry_agent",
    "mistake_entry_base_agent",
    "mistake_entry_directed_target",
    "mistake_agent_matches_step",
    "mistake_agent_is_directed_target",
    "prefix_len",
    "prefix_empty",
    "has_question",
    "has_ground_truth",
    "has_mistake_reason",
    "system_prompt_agent_count",
    "history_agent_count",
    "phase2a_status",
    "phase2a_note",
]


def write_case_index(cases: list[WhoWhenCase], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CASE_INDEX_FIELDS)
        writer.writeheader()
        for case in cases:
            writer.writerow(case_index_row(case))


def _status_counts(cases: list[WhoWhenCase]) -> Counter[str]:
    return Counter(phase2a_status(case)[0] for case in cases)


def _dataset_counts(cases: list[WhoWhenCase]) -> Counter[str]:
    return Counter(case.dataset_type for case in cases)


def _bool_count(cases: list[WhoWhenCase], attr: str) -> tuple[int, int]:
    true_count = sum(1 for case in cases if getattr(case, attr)())
    return true_count, len(cases) - true_count


def _sample_block(case: WhoWhenCase) -> list[str]:
    step = case.mistake_step
    status, note = phase2a_status(case)
    lines = [
        f"### {case.case_id}",
        "",
        f"- dataset: `{case.dataset_type}`",
        f"- path: `{case.path}`",
        f"- history_len: `{case.history_len}`",
        f"- mistake_agent: `{case.mistake_agent}`",
        f"- mistake_step: `{case.mistake_step_raw}`",
        f"- mistake_entry_agent: `{case.agent_at(step) if step is not None else ''}`",
        f"- prefix_len: `{len(case.prefix_before_mistake())}`",
        f"- phase2a_status: `{status}`",
        f"- phase2a_note: `{note}`",
        f"- mistake_reason: {case.mistake_reason[:500]}",
        "",
    ]
    if step is not None and 0 <= step < case.history_len:
        before = max(0, step - 1)
        after = min(case.history_len, step + 2)
        lines.extend(["Nearby steps:", ""])
        for idx in range(before, after):
            content = " ".join(case.content_at(idx).split())
            if len(content) > 500:
                content = content[:500] + "..."
            marker = " <-- mistake" if idx == step else ""
            lines.append(f"- step {idx} `{case.agent_at(idx)}`{marker}: {content}")
        lines.append("")
    return lines


def render_data_audit_report(cases: list[WhoWhenCase], *, sample_count: int = 3) -> str:
    dataset_counts = _dataset_counts(cases)
    status_counts = _status_counts(cases)
    valid_steps, invalid_steps = _bool_count(cases, "mistake_step_valid")
    matched_agents, mismatched_agents = _bool_count(cases, "mistake_agent_matches_step")
    empty_prefix = sum(1 for case in cases if len(case.prefix_before_mistake()) == 0)
    non_empty_prefix = len(cases) - empty_prefix

    lines = [
        "# Who&When Data Audit",
        "",
        "## Summary",
        "",
        f"- total_cases: `{len(cases)}`",
        f"- algorithm_generated: `{dataset_counts.get('algorithm_generated', 0)}`",
        f"- hand_crafted: `{dataset_counts.get('hand_crafted', 0)}`",
        f"- valid_mistake_steps: `{valid_steps}`",
        f"- invalid_mistake_steps: `{invalid_steps}`",
        f"- mistake_agent_matches_step: `{matched_agents}`",
        f"- mistake_agent_mismatches_step: `{mismatched_agents}`",
        f"- non_empty_prefix_cases: `{non_empty_prefix}`",
        f"- empty_prefix_cases: `{empty_prefix}`",
        "",
        "## Phase 2A Status",
        "",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}: `{count}`")

    lines.extend(
        [
            "",
            "## Initial Feasibility Judgment",
            "",
        ]
    )
    blockers = status_counts.get("blocker", 0)
    candidates = status_counts.get("candidate", 0) + status_counts.get("candidate_initial_step", 0)
    if cases and blockers == 0 and candidates > 0:
        lines.extend(
            [
                "`t*-1` trace-prefix repair is structurally feasible for Phase 2A.",
                "",
                "Caveat: cases with `candidate_initial_step` have an empty prefix and need prompts built",
                "from the task, agent role, and system prompt rather than prior trajectory context.",
                "",
                "Recommended first smoke filter:",
                "",
                "```text",
                "dataset_type == algorithm_generated",
                "mistake_step >= 2",
                "phase2a_status == candidate",
                "```",
            ]
        )
    elif candidates > 0:
        lines.extend(
            [
                "`t*-1` trace-prefix repair is partially feasible, but some cases are blocked.",
                "Use the case index to filter main-set candidates.",
            ]
        )
    else:
        lines.append("No Phase 2A candidates found. The native design needs revision.")

    lines.extend(["", "## Sample Cases", ""])
    for case in cases[:sample_count]:
        lines.extend(_sample_block(case))
    return "\n".join(lines)


def write_data_audit_report(
    cases: list[WhoWhenCase],
    output_path: Path,
    *,
    sample_count: int = 3,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_data_audit_report(cases, sample_count=sample_count),
        encoding="utf-8",
    )


def load_who_when_cases(repo_path: Path) -> list[WhoWhenCase]:
    return load_cases(repo_path)
