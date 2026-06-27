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
        intents: list[float] = []
        concrete_actions: list[float] = []
        negative_transfers: list[float] = []
        scores: list[float] = []
        for record in parsed_records:
            parsed = dict(record.get("parsed") or {})
            success = _as_bool(parsed.get("repair_success"))
            recurrence = _as_bool(parsed.get("recurs_same_failure"))
            task_relevant = _as_bool(parsed.get("task_relevant"))
            intent = _as_bool(parsed.get("states_relevant_intent"))
            concrete = _as_bool(parsed.get("performs_concrete_repair_action"))
            negative_transfer = _as_bool(parsed.get("negative_transfer"))
            score = _as_float(parsed.get("repair_score"))
            if success is not None:
                successes.append(1.0 if success else 0.0)
            if recurrence is not None:
                recurrences.append(1.0 if recurrence else 0.0)
            if task_relevant is not None:
                relevant.append(1.0 if task_relevant else 0.0)
            if intent is not None:
                intents.append(1.0 if intent else 0.0)
            if concrete is not None:
                concrete_actions.append(1.0 if concrete else 0.0)
            if negative_transfer is not None:
                negative_transfers.append(1.0 if negative_transfer else 0.0)
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
                "intent_rate": round(mean(intents), 4) if intents else "",
                "concrete_repair_action_rate": round(mean(concrete_actions), 4)
                if concrete_actions
                else "",
                "negative_transfer_rate": round(mean(negative_transfers), 4)
                if negative_transfers
                else "",
                "mean_repair_score": round(mean(scores), 4) if scores else "",
            }
        )

    case_rows: list[dict[str, Any]] = []
    for (case_id, condition), case_records in sorted(by_case_condition.items()):
        parsed_records = [record for record in case_records if record.get("parsed")]
        recurrences: list[float] = []
        successes: list[float] = []
        concrete_actions: list[float] = []
        negative_transfers: list[float] = []
        for record in parsed_records:
            parsed = dict(record.get("parsed") or {})
            recurrence = _as_bool(parsed.get("recurs_same_failure"))
            success = _as_bool(parsed.get("repair_success"))
            concrete = _as_bool(parsed.get("performs_concrete_repair_action"))
            negative_transfer = _as_bool(parsed.get("negative_transfer"))
            if recurrence is not None:
                recurrences.append(1.0 if recurrence else 0.0)
            if success is not None:
                successes.append(1.0 if success else 0.0)
            if concrete is not None:
                concrete_actions.append(1.0 if concrete else 0.0)
            if negative_transfer is not None:
                negative_transfers.append(1.0 if negative_transfer else 0.0)
        case_rows.append(
            {
                "case_id": case_id,
                "condition": condition,
                "attempts": len(case_records),
                "valid_judgments": len(parsed_records),
                "same_failure_recurrence_rate": round(mean(recurrences), 4) if recurrences else "",
                "repair_success_rate": round(mean(successes), 4) if successes else "",
                "concrete_repair_action_rate": round(mean(concrete_actions), 4)
                if concrete_actions
                else "",
                "negative_transfer_rate": round(mean(negative_transfers), 4)
                if negative_transfers
                else "",
            }
        )
    return condition_rows, case_rows


def paired_contrasts(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in case_rows:
        by_case[str(row["case_id"])][str(row["condition"])] = row

    contrasts = [
        ("oracle_specific_vs_no_guidance", "oracle_specific_card", "no_guidance"),
        ("oracle_specific_vs_broad_verification", "oracle_specific_card", "broad_verification_card"),
        ("oracle_specific_vs_hard_mismatch", "oracle_specific_card", "hard_mismatched_card"),
        ("oracle_specific_vs_raw_gold", "oracle_specific_card", "sanitized_raw_gold_explanation"),
        ("oracle_specific_vs_coarse_reflection", "oracle_specific_card", "coarse_reflection"),
    ]
    rows: list[dict[str, Any]] = []
    for name, left, right in contrasts:
        deltas: list[float] = []
        recurrence_deltas: list[float] = []
        for conditions in by_case.values():
            if left not in conditions or right not in conditions:
                continue
            left_success = _as_float(conditions[left].get("repair_success_rate"))
            right_success = _as_float(conditions[right].get("repair_success_rate"))
            left_recur = _as_float(conditions[left].get("same_failure_recurrence_rate"))
            right_recur = _as_float(conditions[right].get("same_failure_recurrence_rate"))
            if left_success is not None and right_success is not None:
                deltas.append(left_success - right_success)
            if left_recur is not None and right_recur is not None:
                recurrence_deltas.append(right_recur - left_recur)
        if deltas or recurrence_deltas:
            rows.append(
                {
                    "contrast": name,
                    "cases": len(deltas),
                    "repair_success_delta": round(mean(deltas), 4) if deltas else "",
                    "recurrence_reduction_delta": round(mean(recurrence_deltas), 4)
                    if recurrence_deltas
                    else "",
                }
            )
    return rows


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary_report(
    condition_rows: list[dict[str, Any]],
    output_path: Path,
    paired_rows: list[dict[str, Any]] | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 2A Judgment Summary",
        "",
        "## By Condition",
        "",
        "| condition | n | valid | repair_success_rate | same_failure_recurrence_rate | concrete_action_rate | negative_transfer_rate | mean_score | errors |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in condition_rows:
        lines.append(
            "| {condition} | {n} | {valid_judgments} | {repair_success_rate} | "
            "{same_failure_recurrence_rate} | {concrete_repair_action_rate} | "
            "{negative_transfer_rate} | {mean_repair_score} | {errors} |".format(**row)
        )
    if paired_rows:
        lines.extend(
            [
                "",
                "## Case-Level Paired Contrasts",
                "",
                "| contrast | cases | repair_success_delta | recurrence_reduction_delta |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for row in paired_rows:
            lines.append(
                "| {contrast} | {cases} | {repair_success_delta} | "
                "{recurrence_reduction_delta} |".format(**row)
            )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
