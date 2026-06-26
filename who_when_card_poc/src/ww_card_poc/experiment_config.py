from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
from typing import Any

import yaml

from ww_card_poc.settings import PROJECT_ROOT, load_dotenv


ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class ExperimentConfig:
    raw: dict[str, Any]

    @property
    def name(self) -> str:
        experiment = self.raw.get("experiment") or {}
        return str(experiment.get("name", "unnamed"))

    @property
    def phases(self) -> dict[str, bool]:
        phases = self.raw.get("phases") or {}
        return {str(key): bool(value) for key, value in phases.items()}

    @property
    def smoke(self) -> dict[str, Any]:
        return dict(self.raw.get("smoke") or {})

    def validate(self) -> list[str]:
        errors: list[str] = []
        phases = self.phases
        if "phase0_reproduction" in phases:
            errors.append(
                "Use phase0_data_audit and phase0_method_reproduction instead of "
                "phase0_reproduction."
            )
        if phases.get("phase0_method_reproduction") and not phases.get("phase0_data_audit"):
            errors.append("phase0_method_reproduction requires phase0_data_audit.")
        if phases.get("phase2a_gold_intervention_repair") and not phases.get(
            "pre_phase2_recurrence_pretest"
        ):
            errors.append("phase2a_gold_intervention_repair should follow recurrence pretest.")
        if phases.get("phase3_cross_trace_transfer") and not phases.get(
            "phase2a_gold_intervention_repair"
        ):
            errors.append("phase3_cross_trace_transfer should follow Phase 2A.")
        return errors


def load_experiment_config(
    path: Path | None = None,
    *,
    dotenv_path: Path | None = None,
    override_env: bool = False,
) -> ExperimentConfig:
    load_dotenv(dotenv_path, override=override_env)
    config_path = path or PROJECT_ROOT / "configs" / "experiment.yaml"
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    expanded = _expand_env(loaded)
    return ExperimentConfig(raw=expanded)


def format_experiment_config(config: ExperimentConfig) -> str:
    lines = [f"experiment: {config.name}", "phases:"]
    for key, value in config.phases.items():
        lines.append(f"  {key}: {value}")
    lines.append("smoke:")
    for key, value in config.smoke.items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)
