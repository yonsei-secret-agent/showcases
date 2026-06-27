from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from ww_card_poc.model_client import ModelClient, ModelClientError
from ww_card_poc.settings import Settings


@dataclass(frozen=True)
class GenerationRecord:
    run_id: str
    attempt: int
    case_id: str
    condition: str
    source_path: str
    responsible_agent: str
    intervention_step: int
    prefix_len: int
    model: str
    temperature: float
    seed: int
    prompt_hash: str
    output_text: str
    finish_reason: str
    usage: dict[str, Any]
    error: str
    created_at: str
    metadata: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            records.append(json.loads(stripped))
    return records


def prompt_hash(system_prompt: str, user_prompt: str) -> str:
    digest = hashlib.sha256()
    digest.update(system_prompt.encode("utf-8"))
    digest.update(b"\n---\n")
    digest.update(user_prompt.encode("utf-8"))
    return digest.hexdigest()[:16]


def generation_messages(input_record: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": str(input_record.get("system_prompt", ""))},
        {"role": "user", "content": str(input_record.get("user_prompt", ""))},
    ]


def existing_generation_keys(output_path: Path) -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()
    for record in read_jsonl(output_path):
        keys.add((str(record.get("run_id")), int(record.get("attempt", 1))))
    return keys


def filter_inputs(
    records: Iterable[dict[str, Any]],
    *,
    case_ids: set[str] | None = None,
    conditions: set[str] | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for record in records:
        if case_ids and str(record.get("case_id")) not in case_ids:
            continue
        if conditions and str(record.get("condition")) not in conditions:
            continue
        selected.append(record)
    return selected


def _temperature(settings: Settings, mode: str) -> float:
    if mode == "recurrence":
        return settings.models.recurrence_temperature
    if mode == "generation":
        return settings.models.generation_temperature
    return float(mode)


def run_generations(
    *,
    settings: Settings,
    input_path: Path,
    output_path: Path,
    repeats: int = 1,
    limit_records: int | None = None,
    case_ids: set[str] | None = None,
    conditions: set[str] | None = None,
    temperature_mode: str = "generation",
    dry_run: bool = False,
    resume: bool = True,
) -> list[GenerationRecord]:
    input_records = filter_inputs(read_jsonl(input_path), case_ids=case_ids, conditions=conditions)
    if limit_records is not None:
        input_records = input_records[:limit_records]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    done = existing_generation_keys(output_path) if resume else set()
    client = ModelClient(settings)
    temperature = _temperature(settings, temperature_mode)
    written: list[GenerationRecord] = []

    with output_path.open("a", encoding="utf-8") as handle:
        for input_record in input_records:
            run_id = str(input_record["run_id"])
            for attempt in range(1, repeats + 1):
                if (run_id, attempt) in done:
                    continue
                system_prompt = str(input_record.get("system_prompt", ""))
                user_prompt = str(input_record.get("user_prompt", ""))
                output_text = ""
                finish_reason = ""
                usage: dict[str, Any] = {}
                error = ""
                if dry_run:
                    output_text = "[DRY_RUN] Model call skipped."
                    finish_reason = "dry_run"
                else:
                    seed = settings.experiment_seed + attempt
                    try:
                        response = client.complete(
                            model=settings.models.generation_model,
                            messages=generation_messages(input_record),
                            temperature=temperature,
                            max_tokens=settings.models.max_output_tokens,
                            seed=seed,
                        )
                        output_text = response.content
                        finish_reason = response.finish_reason
                        usage = response.usage
                        usage["system_fingerprint"] = response.raw.get("system_fingerprint", "")
                    except ModelClientError as exc:
                        error = str(exc)
                if dry_run:
                    seed = settings.experiment_seed + attempt
                record = GenerationRecord(
                    run_id=run_id,
                    attempt=attempt,
                    case_id=str(input_record["case_id"]),
                    condition=str(input_record["condition"]),
                    source_path=str(input_record["source_path"]),
                    responsible_agent=str(input_record["responsible_agent"]),
                    intervention_step=int(input_record["intervention_step"]),
                    prefix_len=int(input_record["prefix_len"]),
                    model=response.model if not dry_run and not error else settings.models.generation_model,
                    temperature=temperature,
                    seed=seed,
                    prompt_hash=prompt_hash(system_prompt, user_prompt),
                    output_text=output_text,
                    finish_reason=finish_reason,
                    usage=usage,
                    error=error,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    metadata=dict(input_record.get("metadata") or {}),
                )
                handle.write(record.to_json() + "\n")
                handle.flush()
                written.append(record)
    return written
