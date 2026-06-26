from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    return key, value


def load_dotenv(path: Path | None = None, *, override: bool = False) -> None:
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(line)
        if parsed is None:
            continue
        key, value = parsed
        if override or key not in os.environ:
            os.environ[key] = value


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _as_bool(value: Any, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def _as_float(value: Any, default: float) -> float:
    if value is None or value == "":
        return default
    return float(value)


def _as_int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return float(raw)


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def _redact(value: str) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "<set>"
    return f"{value[:4]}...{value[-4:]}"


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    return _expand_env(loaded)


@dataclass(frozen=True)
class ApiSettings:
    backend: str
    openrouter_api_key: str
    openai_api_key: str
    openrouter_base_url: str
    openai_base_url: str
    openrouter_provider_order: str
    openrouter_allow_fallbacks: bool
    openrouter_http_referer: str
    openrouter_app_title: str

    @property
    def active_api_key(self) -> str:
        if self.backend == "openrouter":
            return self.openrouter_api_key
        if self.backend == "openai":
            return self.openai_api_key
        return ""

    @property
    def active_base_url(self) -> str:
        if self.backend == "openrouter":
            return self.openrouter_base_url
        if self.backend == "openai":
            return self.openai_base_url
        return ""


@dataclass(frozen=True)
class ModelSettings:
    generation_model: str
    card_model: str
    judge_model: str
    attribution_model: str
    generation_temperature: float
    recurrence_temperature: float
    card_temperature: float
    judge_temperature: float
    max_output_tokens: int


@dataclass(frozen=True)
class PathSettings:
    who_when_repo_path: Path
    data_dir: Path
    reports_dir: Path


@dataclass(frozen=True)
class Settings:
    api: ApiSettings
    models: ModelSettings
    paths: PathSettings
    experiment_seed: int

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.api.backend not in {"openrouter", "openai"}:
            errors.append("MODEL_BACKEND must be 'openrouter' or 'openai'.")
        if not self.api.active_api_key:
            errors.append(f"Missing API key for active backend: {self.api.backend}.")
        if not self.models.generation_model:
            errors.append("GENERATION_MODEL is required.")
        if not self.models.card_model:
            errors.append("CARD_MODEL is required.")
        if not self.models.judge_model:
            errors.append("JUDGE_MODEL is required.")
        if not self.models.attribution_model:
            errors.append("ATTRIBUTION_MODEL is required for future method reproduction runs.")
        if self.api.backend == "openrouter" and self.api.openrouter_allow_fallbacks:
            errors.append("OPENROUTER_ALLOW_FALLBACKS should be false for controlled runs.")
        return errors


def load_settings(*, dotenv_path: Path | None = None, override_env: bool = False) -> Settings:
    load_dotenv(dotenv_path, override=override_env)
    root = PROJECT_ROOT
    model_config = _load_yaml(root / "configs" / "models.yaml")
    models_config = model_config.get("models") or {}
    runtime_config = model_config.get("runtime") or {}
    openrouter_config = model_config.get("openrouter") or {}
    openai_config = model_config.get("openai") or {}
    provider_order = openrouter_config.get("provider_order", ["OpenAI"])
    if isinstance(provider_order, list):
        provider_order_value = ",".join(str(item) for item in provider_order if item)
    else:
        provider_order_value = str(provider_order)

    api = ApiSettings(
        backend=str(model_config.get("backend") or os.getenv("MODEL_BACKEND", "openrouter")),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openrouter_base_url=str(
            openrouter_config.get("base_url")
            or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        ),
        openai_base_url=str(
            openai_config.get("base_url") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        ),
        openrouter_provider_order=provider_order_value or os.getenv("OPENROUTER_PROVIDER_ORDER", "OpenAI"),
        openrouter_allow_fallbacks=_as_bool(
            openrouter_config.get("allow_fallbacks"),
            _get_bool("OPENROUTER_ALLOW_FALLBACKS", False),
        ),
        openrouter_http_referer=str(
            openrouter_config.get("http_referer") or os.getenv("OPENROUTER_HTTP_REFERER", "")
        ),
        openrouter_app_title=str(
            openrouter_config.get("app_title") or os.getenv("OPENROUTER_APP_TITLE", "WhoWhen Card PoC")
        ),
    )
    models = ModelSettings(
        generation_model=str(
            models_config.get("generation")
            or os.getenv("GENERATION_MODEL", "openai/gpt-4o-mini-2024-07-18")
        ),
        card_model=str(models_config.get("card") or os.getenv("CARD_MODEL", "openai/gpt-4o")),
        judge_model=str(models_config.get("judge") or os.getenv("JUDGE_MODEL", "openai/gpt-4o")),
        attribution_model=str(
            models_config.get("attribution") or os.getenv("ATTRIBUTION_MODEL", "openai/gpt-4o")
        ),
        generation_temperature=_as_float(
            runtime_config.get("generation_temperature"),
            _get_float("GENERATION_TEMPERATURE", 0.2),
        ),
        recurrence_temperature=_as_float(
            runtime_config.get("recurrence_temperature"),
            _get_float("RECURRENCE_TEMPERATURE", 0.7),
        ),
        card_temperature=_as_float(
            runtime_config.get("card_temperature"),
            _get_float("CARD_TEMPERATURE", 0.0),
        ),
        judge_temperature=_as_float(
            runtime_config.get("judge_temperature"),
            _get_float("JUDGE_TEMPERATURE", 0.0),
        ),
        max_output_tokens=_as_int(
            runtime_config.get("max_output_tokens"),
            _get_int("MAX_OUTPUT_TOKENS", 1200),
        ),
    )
    paths = PathSettings(
        who_when_repo_path=root / os.getenv("WHO_WHEN_REPO_PATH", "third_party/Agents_Failure_Attribution"),
        data_dir=root / os.getenv("DATA_DIR", "data"),
        reports_dir=root / os.getenv("REPORTS_DIR", "reports"),
    )
    return Settings(
        api=api,
        models=models,
        paths=paths,
        experiment_seed=_get_int("EXPERIMENT_SEED", 20260626),
    )


def format_settings(settings: Settings) -> str:
    return "\n".join(
        [
            f"backend: {settings.api.backend}",
            f"active_base_url: {settings.api.active_base_url}",
            f"active_api_key: {_redact(settings.api.active_api_key)}",
            f"generation_model: {settings.models.generation_model}",
            f"card_model: {settings.models.card_model}",
            f"judge_model: {settings.models.judge_model}",
            f"attribution_model: {settings.models.attribution_model}",
            f"generation_temperature: {settings.models.generation_temperature}",
            f"recurrence_temperature: {settings.models.recurrence_temperature}",
            f"card_temperature: {settings.models.card_temperature}",
            f"judge_temperature: {settings.models.judge_temperature}",
            f"openrouter_provider_order: {settings.api.openrouter_provider_order}",
            f"openrouter_allow_fallbacks: {settings.api.openrouter_allow_fallbacks}",
            f"experiment_seed: {settings.experiment_seed}",
            f"who_when_repo_path: {settings.paths.who_when_repo_path}",
        ]
    )
