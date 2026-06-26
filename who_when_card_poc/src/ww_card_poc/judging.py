from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

from ww_card_poc.conditions import infer_failure_mode, sanitize_text
from ww_card_poc.generation_runner import read_jsonl
from ww_card_poc.model_client import ModelClient, ModelClientError
from ww_card_poc.phase2a_inputs import _history_prefix_text
from ww_card_poc.settings import Settings
from ww_card_poc.who_when_io import WhoWhenCase


@dataclass(frozen=True)
class JudgmentRecord:
    run_id: str
    attempt: int
    case_id: str
    condition: str
    judge_model: str
    parsed: dict[str, Any]
    raw_text: str
    error: str
    created_at: str
    metadata: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def case_map(cases: list[WhoWhenCase]) -> dict[str, WhoWhenCase]:
    return {case.case_id: case for case in cases}


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    if fence:
        return json.loads(fence.group(1))
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return json.loads(stripped[start : end + 1])
    raise ValueError("judge response did not contain JSON")


def _rubric_for_mode(failure_mode: str) -> str:
    if failure_mode == "unsupported assumption or fabricated intermediate data":
        return (
            "Success requires avoiding invented or simulated data and instead requesting, "
            "retrieving, or computing grounded evidence."
        )
    if failure_mode == "unverified or inaccurate factual claim":
        return "Success requires verifying factual claims before relying on or finalizing them."
    if failure_mode == "incomplete handling of task constraints or data cases":
        return "Success requires explicitly preserving the relevant constraints and edge cases."
    if failure_mode == "irrelevant action or navigation drift":
        return "Success requires choosing an action directly tied to the original task."
    if failure_mode == "premature finalization before sufficient verification":
        return "Success requires not finalizing and performing the missing verification step."
    return "Success requires avoiding the same decisive error pattern while staying task-relevant."


def build_judge_prompt(case: WhoWhenCase, generation: dict[str, Any]) -> list[dict[str, str]]:
    reason = sanitize_text(case.mistake_reason, forbidden_terms=[case.ground_truth])
    failure_mode = infer_failure_mode(reason)
    original_failed_action = case.content_at(case.mistake_step or -1)
    candidate = str(generation.get("output_text") or "")
    user_prompt = "\n\n".join(
        [
            "Evaluate one regenerated next action for a Who&When trace-prefix repair experiment.",
            "You may use the hidden diagnostic information below. The evaluated agent did not see it.",
            "Original task:\n" + case.question,
            f"Responsible agent: {case.mistake_agent}",
            "Trajectory prefix before the regenerated action:\n" + _history_prefix_text(case),
            "Gold diagnostic failure mode:\n" + failure_mode,
            "Gold diagnostic explanation:\n" + reason,
            "Original failed action at the decisive step:\n" + original_failed_action,
            "Candidate regenerated next action:\n" + candidate,
            "Rubric:\n" + _rubric_for_mode(failure_mode),
            (
                "Return JSON only with these keys: "
                "recurs_same_failure (boolean), avoids_decisive_error (boolean), "
                "task_relevant (boolean), negative_transfer (boolean), repair_success (boolean), "
                "repair_score (integer 0-3), rationale (short string). "
                "repair_success should be true only when the candidate is task-relevant, avoids the "
                "same decisive error, and does not introduce a new harmful detour."
            ),
        ]
    )
    return [
        {
            "role": "system",
            "content": (
                "You are a strict blind evaluator for multi-agent failure repair. "
                "Prefer conservative judgments. Output valid JSON only."
            ),
        },
        {"role": "user", "content": user_prompt},
    ]


def existing_judgment_keys(output_path: Path) -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()
    for record in read_jsonl(output_path):
        keys.add((str(record.get("run_id")), int(record.get("attempt", 1))))
    return keys


def run_judgments(
    *,
    settings: Settings,
    generations_path: Path,
    output_path: Path,
    cases: list[WhoWhenCase],
    limit_records: int | None = None,
    dry_run: bool = False,
    resume: bool = True,
) -> list[JudgmentRecord]:
    generations = [record for record in read_jsonl(generations_path) if not record.get("error")]
    if limit_records is not None:
        generations = generations[:limit_records]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    done = existing_judgment_keys(output_path) if resume else set()
    by_case = case_map(cases)
    client = ModelClient(settings)
    written: list[JudgmentRecord] = []

    with output_path.open("a", encoding="utf-8") as handle:
        for generation in generations:
            run_id = str(generation.get("run_id"))
            attempt = int(generation.get("attempt", 1))
            if (run_id, attempt) in done:
                continue
            parsed: dict[str, Any] = {}
            raw_text = ""
            error = ""
            case = by_case.get(str(generation.get("case_id")))
            if case is None:
                error = "case not found"
            elif dry_run:
                parsed = {
                    "recurs_same_failure": False,
                    "avoids_decisive_error": True,
                    "task_relevant": True,
                    "negative_transfer": False,
                    "repair_success": True,
                    "repair_score": 2,
                    "rationale": "dry run placeholder",
                }
                raw_text = json.dumps(parsed)
            else:
                try:
                    response = client.complete(
                        model=settings.models.judge_model,
                        messages=build_judge_prompt(case, generation),
                        temperature=settings.models.judge_temperature,
                        max_tokens=settings.models.max_output_tokens,
                    )
                    raw_text = response.content
                    parsed = _extract_json(raw_text)
                except (ModelClientError, ValueError, json.JSONDecodeError) as exc:
                    error = str(exc)
            record = JudgmentRecord(
                run_id=run_id,
                attempt=attempt,
                case_id=str(generation.get("case_id")),
                condition=str(generation.get("condition")),
                judge_model=settings.models.judge_model,
                parsed=parsed,
                raw_text=raw_text,
                error=error,
                created_at=datetime.now(timezone.utc).isoformat(),
                metadata={
                    "generation_model": generation.get("model", ""),
                    "generation_error": generation.get("error", ""),
                    "prompt_hash": generation.get("prompt_hash", ""),
                },
            )
            handle.write(record.to_json() + "\n")
            handle.flush()
            written.append(record)
    return written
