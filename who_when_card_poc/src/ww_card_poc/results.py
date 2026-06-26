from __future__ import annotations

from collections import defaultdict
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from ww_card_poc.generation_runner import read_jsonl


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_judgments(judgments_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = read_jsonl(judgments_path)
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_case_condition: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_condition[str(record.get("condition"))].append(record)
        by_case_condition[(str(record.get("case_id")), str(record.get("condition")))].append(record)

    condition_rows: list[dict[str, Any]] = []
    for condition, condition_records in sorted(by_condition.items()):
        parsed_records = [record for record in condition_records if record.get("parsed")]
        errors = len(condition_records) - len(parsed_records)
        successes: list[float] = []
        recurrences: list[float] = []
        relevant: list[float] = []
        scores: list[float] = []
        for record in parsed_records:
            parsed = dict(record.get("parsed") or {})
            success = _as_bool(parsed.get("repair_success"))
            recurrence = _as_bool(parsed.get("recurs_same_failure"))
            task_relevant = _as_bool(parsed.get("task_relevant"))
            score = _as_float(parsed.get("repair_score"))
            if success is not None:
                successes.append(1.0 if success else 0.0)
            if recurrence is not None:
                recurrences.append(1.0 if recurrence else 0.0)
            if task_relevant is not None:
                relevant.append(1.0 if task_relevant else 0.0)
            if score is not None:
                scores.append(score)
        condition_rows.append(
            {
                "condition": condition,
                "n": len(condition_records),
                "valid_judgments": len(parsed_records),
                "errors": errors,
                "repair_success_rate": round(mean(successes), 4) if successes else "",
                "same_failure_recurrence_rate": round(mean(recurrences), 4) if recurrences else "",
                "task_relevance_rate": round(mean(relevant), 4) if relevant else "",
                "mean_repair_score": round(mean(scores), 4) if scores else "",
            }
        )

    case_rows: list[dict[str, Any]] = []
    for (case_id, condition), case_records in sorted(by_case_condition.items()):
        parsed_records = [record for record in case_records if record.get("parsed")]
        recurrences: list[float] = []
        successes: list[float] = []
        for record in parsed_records:
            parsed = dict(record.get("parsed") or {})
            recurrence = _as_bool(parsed.get("recurs_same_failure"))
            success = _as_bool(parsed.get("repair_success"))
            if recurrence is not None:
                recurrences.append(1.0 if recurrence else 0.0)
            if success is not None:
                successes.append(1.0 if success else 0.0)
        case_rows.append(
            {
                "case_id": case_id,
                "condition": condition,
                "attempts": len(case_records),
                "valid_judgments": len(parsed_records),
                "same_failure_recurrence_rate": round(mean(recurrences), 4) if recurrences else "",
                "repair_success_rate": round(mean(successes), 4) if successes else "",
            }
        )
    return condition_rows, case_rows


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary_report(condition_rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 2A Judgment Summary",
        "",
        "## By Condition",
        "",
        "| condition | n | valid | repair_success_rate | same_failure_recurrence_rate | mean_score | errors |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in condition_rows:
        lines.append(
            "| {condition} | {n} | {valid_judgments} | {repair_success_rate} | "
            "{same_failure_recurrence_rate} | {mean_repair_score} | {errors} |".format(**row)
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
