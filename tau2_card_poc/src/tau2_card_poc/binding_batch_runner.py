from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tau2_card_poc.binding_manifest import (
    BindingExperimentManifest,
    iter_binding_retry_specs,
)
from tau2_card_poc.specs import BindingRetrySpec


SingleBindingRun = Callable[[BindingRetrySpec, Path], Path]


@dataclass(frozen=True)
class BindingManifestRunResult:
    task_id: str
    condition: str
    seed: int
    result_path: Path
    status: str


def binding_manifest_run_output_dir(
    output_root: str | Path,
    manifest: BindingExperimentManifest,
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


def run_binding_manifest(
    manifest: BindingExperimentManifest,
    *,
    output_root: str | Path,
    single_run: SingleBindingRun | None = None,
    resume: bool = True,
) -> list[BindingManifestRunResult]:
    if single_run is None:
        from tau2_card_poc.binding_runner import run_single_binding_retry

        runner = run_single_binding_retry
    else:
        runner = single_run
    results: list[BindingManifestRunResult] = []

    for spec in iter_binding_retry_specs(manifest):
        output_dir = binding_manifest_run_output_dir(
            output_root,
            manifest,
            task_id=spec.task_id,
            condition=spec.condition,
            seed=spec.seed,
        )
        result_path = output_dir / "results.json"
        if resume and result_path.exists():
            results.append(
                BindingManifestRunResult(
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
            BindingManifestRunResult(
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
