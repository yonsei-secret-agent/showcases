from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from tau2_card_poc.specs import BindingRetrySpec


@dataclass(frozen=True)
class BindingExperimentCondition:
    name: str
    binding_gate: dict[str, Any] | None
    per_task_binding_gate: dict[str, dict[str, Any] | None] | None = None

    def binding_gate_for_task(self, task_id: str) -> dict[str, Any] | None:
        if self.per_task_binding_gate is None:
            return self.binding_gate
        return self.per_task_binding_gate[str(task_id)]


@dataclass(frozen=True)
class BindingExperimentManifest:
    experiment_id: str
    domain: str
    agent_model: str
    user_model: str
    task_ids: list[str]
    seeds: list[int]
    conditions: list[BindingExperimentCondition]
    task_split_name: str | None = None
    max_steps: int = 100
    max_errors: int = 10
    log_level: str = "INFO"


def load_binding_experiment_manifest(path: str | Path) -> BindingExperimentManifest:
    data = json.loads(Path(path).read_text())
    return BindingExperimentManifest(
        experiment_id=str(data["experiment_id"]),
        domain=str(data["domain"]),
        agent_model=str(data["agent_model"]),
        user_model=str(data["user_model"]),
        task_ids=[str(task_id) for task_id in data["task_ids"]],
        seeds=[int(seed) for seed in data["seeds"]],
        conditions=[
            BindingExperimentCondition(
                name=str(condition["name"]),
                binding_gate=condition.get("binding_gate"),
                per_task_binding_gate=(
                    {
                        str(task_id): binding_gate
                        for task_id, binding_gate in condition["per_task_binding_gate"].items()
                    }
                    if "per_task_binding_gate" in condition
                    else None
                ),
            )
            for condition in data["conditions"]
        ],
        task_split_name=data.get("task_split_name"),
        max_steps=int(data.get("max_steps", 100)),
        max_errors=int(data.get("max_errors", 10)),
        log_level=str(data.get("log_level", "INFO")),
    )


def iter_binding_retry_specs(
    manifest: BindingExperimentManifest,
) -> Iterator[BindingRetrySpec]:
    _validate_binding_manifest(manifest)
    for task_id in manifest.task_ids:
        for condition in manifest.conditions:
            for trial, seed in enumerate(manifest.seeds):
                yield BindingRetrySpec(
                    domain=manifest.domain,
                    task_id=task_id,
                    condition=condition.name,
                    binding_gate=condition.binding_gate_for_task(task_id),
                    seed=seed,
                    trial=trial,
                    agent_model=manifest.agent_model,
                    user_model=manifest.user_model,
                    task_split_name=manifest.task_split_name,
                    max_steps=manifest.max_steps,
                    max_errors=manifest.max_errors,
                    log_level=manifest.log_level,
                )


def _validate_binding_manifest(manifest: BindingExperimentManifest) -> None:
    condition_names = [condition.name for condition in manifest.conditions]
    if len(condition_names) != len(set(condition_names)):
        raise ValueError("duplicate condition names in binding experiment manifest")
    if not manifest.task_ids:
        raise ValueError("binding experiment manifest must include at least one task")
    if not manifest.seeds:
        raise ValueError("binding experiment manifest must include at least one seed")
    if not manifest.conditions:
        raise ValueError("binding experiment manifest must include at least one condition")

    for condition in manifest.conditions:
        if condition.per_task_binding_gate is None:
            continue
        missing_task_ids = [
            task_id
            for task_id in manifest.task_ids
            if str(task_id) not in condition.per_task_binding_gate
        ]
        if missing_task_ids:
            missing = ", ".join(missing_task_ids)
            raise ValueError(
                f"missing per-task binding gate for condition "
                f"{condition.name}: {missing}"
            )
