from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from tau2_card_poc.memory_runner import MemoryRetrySpec


@dataclass(frozen=True)
class ExperimentCondition:
    name: str
    runtime_memory: str


@dataclass(frozen=True)
class ExperimentManifest:
    experiment_id: str
    domain: str
    agent_model: str
    user_model: str
    task_ids: list[str]
    seeds: list[int]
    conditions: list[ExperimentCondition]
    task_split_name: str | None = None
    max_steps: int = 100
    max_errors: int = 10


def load_experiment_manifest(path: str | Path) -> ExperimentManifest:
    data = json.loads(Path(path).read_text())
    return ExperimentManifest(
        experiment_id=str(data["experiment_id"]),
        domain=str(data["domain"]),
        agent_model=str(data["agent_model"]),
        user_model=str(data["user_model"]),
        task_ids=[str(task_id) for task_id in data["task_ids"]],
        seeds=[int(seed) for seed in data["seeds"]],
        conditions=[
            ExperimentCondition(
                name=str(condition["name"]),
                runtime_memory=str(condition.get("runtime_memory", "")),
            )
            for condition in data["conditions"]
        ],
        task_split_name=data.get("task_split_name"),
        max_steps=int(data.get("max_steps", 100)),
        max_errors=int(data.get("max_errors", 10)),
    )


def iter_memory_retry_specs(manifest: ExperimentManifest) -> Iterator[MemoryRetrySpec]:
    _validate_manifest(manifest)
    for task_id in manifest.task_ids:
        for condition in manifest.conditions:
            for trial, seed in enumerate(manifest.seeds):
                yield MemoryRetrySpec(
                    domain=manifest.domain,
                    task_id=task_id,
                    condition=condition.name,
                    runtime_memory=condition.runtime_memory,
                    seed=seed,
                    trial=trial,
                    agent_model=manifest.agent_model,
                    user_model=manifest.user_model,
                    task_split_name=manifest.task_split_name,
                    max_steps=manifest.max_steps,
                    max_errors=manifest.max_errors,
                )


def _validate_manifest(manifest: ExperimentManifest) -> None:
    condition_names = [condition.name for condition in manifest.conditions]
    if len(condition_names) != len(set(condition_names)):
        raise ValueError("duplicate condition names in experiment manifest")
    if not manifest.task_ids:
        raise ValueError("experiment manifest must include at least one task")
    if not manifest.seeds:
        raise ValueError("experiment manifest must include at least one seed")
    if not manifest.conditions:
        raise ValueError("experiment manifest must include at least one condition")
