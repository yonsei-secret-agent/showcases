from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tau2_card_poc.experiment_manifest import (
    ExperimentManifest,
    iter_memory_retry_specs,
)
from tau2_card_poc.memory_runner import MemoryRetrySpec, run_single_memory_retry


SingleRun = Callable[[MemoryRetrySpec, Path], Path]


@dataclass(frozen=True)
class ManifestRunResult:
    task_id: str
    condition: str
    seed: int
    result_path: Path
    status: str


def manifest_run_output_dir(
    output_root: str | Path,
    manifest: ExperimentManifest,
    *,
    task_id: str,
    condition: str,
    seed: int,
) -> Path:
    return (
        Path(output_root)
        / _slug(manifest.experiment_id)
        / f"task_{_slug(task_id)}"
        / f"condition_{_slug(condition)}"
        / f"seed_{seed}"
    )


def run_manifest(
    manifest: ExperimentManifest,
    *,
    output_root: str | Path,
    single_run: SingleRun | None = None,
    resume: bool = True,
) -> list[ManifestRunResult]:
    runner = single_run or run_single_memory_retry
    results: list[ManifestRunResult] = []

    for spec in iter_memory_retry_specs(manifest):
        output_dir = manifest_run_output_dir(
            output_root,
            manifest,
            task_id=spec.task_id,
            condition=spec.condition,
            seed=spec.seed,
        )
        result_path = output_dir / "results.json"
        if resume and result_path.exists():
            results.append(
                ManifestRunResult(
                    task_id=spec.task_id,
                    condition=spec.condition,
                    seed=spec.seed,
                    result_path=result_path,
                    status="skipped",
                )
            )
            continue

        written_path = runner(spec, output_dir=output_dir)
        results.append(
            ManifestRunResult(
                task_id=spec.task_id,
                condition=spec.condition,
                seed=spec.seed,
                result_path=written_path,
                status="ran",
            )
        )
    return results


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", str(value)).strip("_").lower()
    return slug or "empty"
