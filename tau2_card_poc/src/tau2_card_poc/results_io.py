from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Tau2ResultRecord:
    simulation_id: str
    task_id: str
    trial: int | None
    seed: int | None
    reward: float | None
    success: bool
    db_reward: float | None
    communicate_reward: float | None
    nl_assertion_reward: float | None
    termination_reason: str | None
    agent_cost: float | None
    user_cost: float | None
    agent_model: str | None
    user_model: str | None
    tool_call_names: list[str]
    message_count: int
    gate_trigger_count: int = 0
    gate_failure_count: int = 0
    gate_retry_count: int = 0
    gate_final_passed: bool | None = None


@dataclass(frozen=True)
class TaskOutcome:
    task_id: str
    total_attempts: int
    success_count: int
    failure_count: int
    group: str


def load_result_records(results_path: str | Path) -> list[Tau2ResultRecord]:
    data = _load_results_dict(Path(results_path))
    info = data.get("info") or {}
    agent_info = info.get("agent_info") or {}
    user_info = info.get("user_info") or {}

    records = []
    for sim in data.get("simulations") or []:
        reward_info = sim.get("reward_info") or {}
        reward = _as_float(reward_info.get("reward"))
        reward_breakdown = reward_info.get("reward_breakdown") or {}
        messages = sim.get("messages") or []
        gate_metrics = _gate_metrics(sim.get("info") or {})

        records.append(
            Tau2ResultRecord(
                simulation_id=str(sim.get("id", "")),
                task_id=str(sim.get("task_id", "")),
                trial=_as_int(sim.get("trial")),
                seed=_as_int(sim.get("seed")),
                reward=reward,
                success=reward == 1.0,
                db_reward=_breakdown_value(reward_breakdown, "DB"),
                communicate_reward=_breakdown_value(reward_breakdown, "COMMUNICATE"),
                nl_assertion_reward=_breakdown_value(
                    reward_breakdown, "NL_ASSERTION"
                ),
                termination_reason=sim.get("termination_reason"),
                agent_cost=_as_float(sim.get("agent_cost")),
                user_cost=_as_float(sim.get("user_cost")),
                agent_model=agent_info.get("llm"),
                user_model=user_info.get("llm"),
                tool_call_names=_tool_call_names(messages),
                message_count=len(messages),
                gate_trigger_count=gate_metrics["trigger_count"],
                gate_failure_count=gate_metrics["failure_count"],
                gate_retry_count=gate_metrics["retry_count"],
                gate_final_passed=gate_metrics["final_passed"],
            )
        )
    return records


def group_task_outcomes(records: list[Tau2ResultRecord]) -> dict[str, TaskOutcome]:
    grouped: dict[str, list[Tau2ResultRecord]] = {}
    for record in records:
        grouped.setdefault(record.task_id, []).append(record)

    outcomes = {}
    for task_id, task_records in grouped.items():
        success_count = sum(1 for record in task_records if record.success)
        total = len(task_records)
        failure_count = total - success_count
        if success_count == total:
            group = "stable_success"
        elif failure_count == total:
            group = "stable_failure"
        else:
            group = "mixed"
        outcomes[task_id] = TaskOutcome(
            task_id=task_id,
            total_attempts=total,
            success_count=success_count,
            failure_count=failure_count,
            group=group,
        )
    return outcomes


def _load_results_dict(path: Path) -> dict[str, Any]:
    if path.is_dir():
        path = path / "results.json"
    data = json.loads(path.read_text())

    sims_dir = path.parent / "simulations"
    if "simulations" not in data and sims_dir.is_dir():
        data["simulations"] = [
            json.loads(sim_path.read_text()) for sim_path in sorted(sims_dir.glob("*.json"))
        ]
    return data


def _breakdown_value(reward_breakdown: dict[str, Any], key: str) -> float | None:
    value = reward_breakdown.get(key)
    if value is None:
        value = reward_breakdown.get(key.lower())
    return _as_float(value)


def _tool_call_names(messages: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for message in messages:
        for call in message.get("tool_calls") or []:
            name = call.get("name") or call.get("function", {}).get("name")
            if name:
                names.append(str(name))
    return names


def _gate_metrics(info: dict[str, Any]) -> dict[str, Any]:
    events = info.get("binding_gate_events") or []
    triggered_events = [event for event in events if event.get("triggered")]
    return {
        "trigger_count": len(triggered_events),
        "failure_count": sum(
            1 for event in triggered_events if event.get("passed") is False
        ),
        "retry_count": sum(1 for event in triggered_events if event.get("retry_used")),
        "final_passed": (
            bool(triggered_events[-1].get("passed")) if triggered_events else None
        ),
    }


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
