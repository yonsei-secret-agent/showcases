from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    task_id: str
    condition: str
    seed: int | None
    trial: int | None
    reward: float | None
    success: bool
    db_reward: float | None
    communicate_reward: float | None
    nl_assertion_reward: float | None
    result_path: Path


@dataclass(frozen=True)
class ConditionSummary:
    condition: str
    attempts: int
    successes: int
    success_rate: float
    mean_reward: float


@dataclass(frozen=True)
class TaskStability:
    task_id: str
    attempts: int
    successes: int
    failures: int
    group: str


@dataclass(frozen=True)
class PairedConditionSummary:
    condition: str
    paired_attempts: int
    baseline_successes: int
    condition_successes: int
    paired_rescues: int
    paired_regressions: int
    success_delta: float
    rescue_rate_among_baseline_failures: float
    regression_rate_among_baseline_successes: float


@dataclass(frozen=True)
class PairwiseConditionComparison:
    condition_a: str
    condition_b: str
    paired_attempts: int
    condition_a_successes: int
    condition_b_successes: int
    a_beats_b: int
    b_beats_a: int
    ties_success: int
    ties_failure: int
    success_delta_a_minus_b: float


def collect_experiment_records(
    experiment_dir: str | Path,
    *,
    default_condition: str = "unknown",
) -> list[ExperimentRecord]:
    experiment_path = Path(experiment_dir)
    records: list[ExperimentRecord] = []
    result_paths = sorted(experiment_path.glob("task_*/condition_*/seed_*/results.json"))
    if not result_paths and (experiment_path / "results.json").exists():
        result_paths = [experiment_path / "results.json"]

    for result_path in result_paths:
        data = json.loads(result_path.read_text())
        info = data.get("info") or {}
        condition = str(info.get("condition") or _condition_from_path(result_path, default_condition))
        for simulation in data.get("simulations") or []:
            reward_info = simulation.get("reward_info") or {}
            reward = _as_float(reward_info.get("reward"))
            breakdown = reward_info.get("reward_breakdown") or {}
            records.append(
                ExperimentRecord(
                    experiment_id=experiment_path.name,
                    task_id=str(simulation.get("task_id", "")),
                    condition=condition,
                    seed=_as_int(simulation.get("seed")),
                    trial=_as_int(simulation.get("trial")),
                    reward=reward,
                    success=reward == 1.0,
                    db_reward=_breakdown_value(breakdown, "DB"),
                    communicate_reward=_breakdown_value(breakdown, "COMMUNICATE"),
                    nl_assertion_reward=_breakdown_value(breakdown, "NL_ASSERTION"),
                    result_path=result_path,
                )
            )
    return records


def condition_summary(records: list[ExperimentRecord]) -> dict[str, ConditionSummary]:
    grouped: dict[str, list[ExperimentRecord]] = {}
    for record in records:
        grouped.setdefault(record.condition, []).append(record)

    summaries = {}
    for condition, condition_records in sorted(grouped.items()):
        attempts = len(condition_records)
        successes = sum(1 for record in condition_records if record.success)
        rewards = [record.reward or 0.0 for record in condition_records]
        summaries[condition] = ConditionSummary(
            condition=condition,
            attempts=attempts,
            successes=successes,
            success_rate=successes / attempts if attempts else 0.0,
            mean_reward=sum(rewards) / attempts if attempts else 0.0,
        )
    return summaries


def task_stability_summary(records: list[ExperimentRecord]) -> dict[str, TaskStability]:
    grouped: dict[str, list[ExperimentRecord]] = {}
    for record in records:
        grouped.setdefault(record.task_id, []).append(record)

    summaries = {}
    for task_id, task_records in sorted(grouped.items(), key=lambda item: int(item[0])):
        attempts = len(task_records)
        successes = sum(1 for record in task_records if record.success)
        failures = attempts - successes
        if successes == attempts:
            group = "stable_success"
        elif failures == attempts:
            group = "stable_failure"
        else:
            group = "mixed"
        summaries[task_id] = TaskStability(
            task_id=task_id,
            attempts=attempts,
            successes=successes,
            failures=failures,
            group=group,
        )
    return summaries


def paired_condition_summary(
    records: list[ExperimentRecord],
    *,
    baseline_condition: str = "no_memory",
) -> dict[str, PairedConditionSummary]:
    baseline_by_key: dict[tuple[str, int | None], ExperimentRecord] = {}
    condition_by_key: dict[str, dict[tuple[str, int | None], ExperimentRecord]] = {}
    for record in records:
        key = (record.task_id, record.seed)
        if record.condition == baseline_condition:
            baseline_by_key[key] = record
        else:
            condition_by_key.setdefault(record.condition, {})[key] = record

    summaries: dict[str, PairedConditionSummary] = {}
    for condition, condition_records in sorted(condition_by_key.items()):
        pairs = [
            (baseline_by_key[key], condition_record)
            for key, condition_record in condition_records.items()
            if key in baseline_by_key
        ]
        paired_attempts = len(pairs)
        baseline_successes = sum(1 for baseline, _ in pairs if baseline.success)
        condition_successes = sum(1 for _, condition_record in pairs if condition_record.success)
        paired_rescues = sum(
            1
            for baseline, condition_record in pairs
            if not baseline.success and condition_record.success
        )
        paired_regressions = sum(
            1
            for baseline, condition_record in pairs
            if baseline.success and not condition_record.success
        )
        baseline_failures = paired_attempts - baseline_successes
        summaries[condition] = PairedConditionSummary(
            condition=condition,
            paired_attempts=paired_attempts,
            baseline_successes=baseline_successes,
            condition_successes=condition_successes,
            paired_rescues=paired_rescues,
            paired_regressions=paired_regressions,
            success_delta=(
                (condition_successes - baseline_successes) / paired_attempts
                if paired_attempts
                else 0.0
            ),
            rescue_rate_among_baseline_failures=(
                paired_rescues / baseline_failures if baseline_failures else 0.0
            ),
            regression_rate_among_baseline_successes=(
                paired_regressions / baseline_successes if baseline_successes else 0.0
            ),
        )
    return summaries


def pairwise_condition_matrix(
    records: list[ExperimentRecord],
) -> dict[tuple[str, str], PairwiseConditionComparison]:
    by_condition: dict[str, dict[tuple[str, int | None], ExperimentRecord]] = {}
    for record in records:
        key = (record.task_id, record.seed)
        by_condition.setdefault(record.condition, {})[key] = record

    matrix: dict[tuple[str, str], PairwiseConditionComparison] = {}
    for condition_a, condition_b in combinations(sorted(by_condition), 2):
        records_a = by_condition[condition_a]
        records_b = by_condition[condition_b]
        common_keys = sorted(records_a.keys() & records_b.keys())
        pairs = [(records_a[key], records_b[key]) for key in common_keys]
        paired_attempts = len(pairs)
        condition_a_successes = sum(1 for record_a, _ in pairs if record_a.success)
        condition_b_successes = sum(1 for _, record_b in pairs if record_b.success)
        a_beats_b = sum(
            1 for record_a, record_b in pairs if record_a.success and not record_b.success
        )
        b_beats_a = sum(
            1 for record_a, record_b in pairs if not record_a.success and record_b.success
        )
        ties_success = sum(
            1 for record_a, record_b in pairs if record_a.success and record_b.success
        )
        ties_failure = sum(
            1
            for record_a, record_b in pairs
            if not record_a.success and not record_b.success
        )
        matrix[(condition_a, condition_b)] = PairwiseConditionComparison(
            condition_a=condition_a,
            condition_b=condition_b,
            paired_attempts=paired_attempts,
            condition_a_successes=condition_a_successes,
            condition_b_successes=condition_b_successes,
            a_beats_b=a_beats_b,
            b_beats_a=b_beats_a,
            ties_success=ties_success,
            ties_failure=ties_failure,
            success_delta_a_minus_b=(
                (condition_a_successes - condition_b_successes) / paired_attempts
                if paired_attempts
                else 0.0
            ),
        )
    return matrix


def write_condition_summary_csv(
    summaries: dict[str, ConditionSummary],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["condition", "attempts", "successes", "success_rate", "mean_reward"])
        for condition in sorted(summaries):
            summary = summaries[condition]
            writer.writerow(
                [
                    summary.condition,
                    summary.attempts,
                    summary.successes,
                    f"{summary.success_rate:.4f}",
                    f"{summary.mean_reward:.4f}",
                ]
            )
    return path


def write_paired_condition_summary_csv(
    summaries: dict[str, PairedConditionSummary],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "condition",
                "paired_attempts",
                "baseline_successes",
                "condition_successes",
                "paired_rescues",
                "paired_regressions",
                "success_delta",
                "rescue_rate_among_baseline_failures",
                "regression_rate_among_baseline_successes",
            ]
        )
        for condition in sorted(summaries):
            summary = summaries[condition]
            writer.writerow(
                [
                    summary.condition,
                    summary.paired_attempts,
                    summary.baseline_successes,
                    summary.condition_successes,
                    summary.paired_rescues,
                    summary.paired_regressions,
                    f"{summary.success_delta:.4f}",
                    f"{summary.rescue_rate_among_baseline_failures:.4f}",
                    f"{summary.regression_rate_among_baseline_successes:.4f}",
                ]
            )
    return path


def write_per_run_outcomes_csv(
    records: list[ExperimentRecord],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "experiment_id",
                "task_id",
                "seed",
                "condition",
                "success",
                "final_reward",
                "db_reward",
                "communicate_reward",
                "nl_assertion_reward",
                "result_path",
            ]
        )
        for record in sorted(records, key=lambda item: (int(item.task_id), item.condition, item.seed or -1)):
            writer.writerow(
                [
                    record.experiment_id,
                    record.task_id,
                    "" if record.seed is None else record.seed,
                    record.condition,
                    1 if record.success else 0,
                    _format_optional_float(record.reward),
                    _format_optional_float(record.db_reward),
                    _format_optional_float(record.communicate_reward),
                    _format_optional_float(record.nl_assertion_reward),
                    str(record.result_path),
                ]
            )
    return path


def write_pairwise_condition_matrix_csv(
    matrix: dict[tuple[str, str], PairwiseConditionComparison],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "condition_a",
                "condition_b",
                "paired_attempts",
                "condition_a_successes",
                "condition_b_successes",
                "a_beats_b",
                "b_beats_a",
                "ties_success",
                "ties_failure",
                "success_delta_a_minus_b",
            ]
        )
        for key in sorted(matrix):
            comparison = matrix[key]
            writer.writerow(
                [
                    comparison.condition_a,
                    comparison.condition_b,
                    comparison.paired_attempts,
                    comparison.condition_a_successes,
                    comparison.condition_b_successes,
                    comparison.a_beats_b,
                    comparison.b_beats_a,
                    comparison.ties_success,
                    comparison.ties_failure,
                    f"{comparison.success_delta_a_minus_b:.4f}",
                ]
            )
    return path


def write_task_stability_csv(
    summaries: dict[str, TaskStability],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["task_id", "attempts", "successes", "failures", "group"])
        for task_id in sorted(summaries, key=int):
            summary = summaries[task_id]
            writer.writerow(
                [
                    summary.task_id,
                    summary.attempts,
                    summary.successes,
                    summary.failures,
                    summary.group,
                ]
            )
    return path


def _condition_from_path(result_path: Path, default_condition: str) -> str:
    for part in result_path.parts:
        if part.startswith("condition_"):
            return part.removeprefix("condition_")
    return default_condition


def _breakdown_value(reward_breakdown: dict, key: str) -> float | None:
    value = reward_breakdown.get(key)
    if value is None:
        value = reward_breakdown.get(key.lower())
    return _as_float(value)


def _as_float(value) -> float | None:
    if value is None:
        return None
    return float(value)


def _as_int(value) -> int | None:
    if value is None:
        return None
    return int(value)


def _format_optional_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"
