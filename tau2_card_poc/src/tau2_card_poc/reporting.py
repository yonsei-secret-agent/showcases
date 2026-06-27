from __future__ import annotations

import csv
import json
from dataclasses import dataclass
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
