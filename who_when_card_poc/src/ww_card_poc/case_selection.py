from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Any

from ww_card_poc.conditions import infer_failure_mode, sanitize_text
from ww_card_poc.who_when_io import WhoWhenCase, phase2a_status


@dataclass(frozen=True)
class SmokeCaseFilter:
    dataset_type: str = "algorithm_generated"
    min_mistake_step: int = 2
    phase2a_status: str = "candidate"
    include_warnings: bool = False
    max_history_len: int | None = 10

    @classmethod
    def from_config(cls, raw: dict[str, Any] | None) -> "SmokeCaseFilter":
        config = raw or {}
        max_history_len_raw = config.get("max_history_len", 10)
        return cls(
            dataset_type=str(config.get("dataset_type", "algorithm_generated")),
            min_mistake_step=int(config.get("min_mistake_step", 2)),
            phase2a_status=str(config.get("phase2a_status", "candidate")),
            include_warnings=bool(config.get("include_warnings", False)),
            max_history_len=None if max_history_len_raw in {"", None} else int(max_history_len_raw),
        )

    def matches(self, case: WhoWhenCase) -> bool:
        status, _ = phase2a_status(case)
        step = case.mistake_step
        if case.dataset_type != self.dataset_type:
            return False
        if step is None or step < self.min_mistake_step:
            return False
        if status != self.phase2a_status:
            if not (self.include_warnings and status == "warning"):
                return False
        if self.max_history_len is not None and case.history_len > self.max_history_len:
            return False
        return True


def select_smoke_cases(
    cases: list[WhoWhenCase],
    *,
    smoke_filter: SmokeCaseFilter,
    limit: int,
    stratify_by_failure_mode: bool = False,
) -> list[WhoWhenCase]:
    selected = [case for case in cases if smoke_filter.matches(case)]
    selected.sort(
        key=lambda case: (
            case.dataset_type,
            case.mistake_step or 0,
            int(case.path.stem) if case.path.stem.isdigit() else 0,
        )
    )
    if stratify_by_failure_mode:
        by_mode: dict[str, list[WhoWhenCase]] = defaultdict(list)
        for case in selected:
            mode = infer_failure_mode(
                sanitize_text(case.mistake_reason, forbidden_terms=[case.ground_truth])
            )
            by_mode[mode].append(case)
        stratified: list[WhoWhenCase] = []
        modes = sorted(by_mode)
        while len(stratified) < limit and any(by_mode.values()):
            for mode in modes:
                if by_mode[mode]:
                    stratified.append(by_mode[mode].pop(0))
                    if len(stratified) >= limit:
                        break
        return stratified[:limit]
    return selected[:limit]


def selection_rows(cases: list[WhoWhenCase]) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for rank, case in enumerate(cases, start=1):
        status, note = phase2a_status(case)
        rows.append(
            {
                "rank": rank,
                "case_id": case.case_id,
                "dataset_type": case.dataset_type,
                "source_path": str(case.path),
                "question_id": case.question_id,
                "history_len": case.history_len,
                "mistake_agent": case.mistake_agent,
                "mistake_step": case.mistake_step if case.mistake_step is not None else "",
                "prefix_len": len(case.prefix_before_mistake()),
                "phase2a_status": status,
                "phase2a_note": note,
                "failure_mode": infer_failure_mode(
                    sanitize_text(case.mistake_reason, forbidden_terms=[case.ground_truth])
                ),
            }
        )
    return rows
