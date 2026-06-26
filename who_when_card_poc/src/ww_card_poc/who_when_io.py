from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


ALGORITHM_DIR = Path("Who&When") / "Algorithm-Generated"
HANDCRAFTED_DIR = Path("Who&When") / "Hand-Crafted"
DIRECTED_AGENT_RE = re.compile(r"\(->\s*([^)]+)\)")


def _numeric_sort_key(path: Path) -> tuple[int, str]:
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    return (int(digits) if digits else 0, path.name)


@dataclass(frozen=True)
class WhoWhenCase:
    case_id: str
    dataset_type: str
    path: Path
    raw: dict[str, Any]

    @property
    def question(self) -> str:
        return str(self.raw.get("question", ""))

    @property
    def question_id(self) -> str:
        return str(self.raw.get("question_ID", ""))

    @property
    def ground_truth(self) -> str:
        return str(self.raw.get("ground_truth", ""))

    @property
    def history(self) -> list[dict[str, Any]]:
        history = self.raw.get("history", [])
        return history if isinstance(history, list) else []

    @property
    def mistake_agent(self) -> str:
        return str(self.raw.get("mistake_agent", ""))

    @property
    def mistake_step_raw(self) -> Any:
        return self.raw.get("mistake_step")

    @property
    def mistake_step(self) -> int | None:
        raw = self.mistake_step_raw
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str) and raw.strip().isdigit():
            return int(raw.strip())
        return None

    @property
    def mistake_reason(self) -> str:
        return str(self.raw.get("mistake_reason", ""))

    @property
    def system_prompt(self) -> dict[str, str]:
        prompt = self.raw.get("system_prompt", {})
        return prompt if isinstance(prompt, dict) else {}

    @property
    def history_len(self) -> int:
        return len(self.history)

    def agent_at(self, step: int) -> str:
        if step < 0 or step >= self.history_len:
            return ""
        entry = self.history[step]
        return str(entry.get("name") or entry.get("role") or "")

    def base_agent_at(self, step: int) -> str:
        agent = self.agent_at(step)
        return agent.split(" (", 1)[0].strip()

    def directed_target_at(self, step: int) -> str:
        agent = self.agent_at(step)
        match = DIRECTED_AGENT_RE.search(agent)
        if not match:
            return ""
        return match.group(1).strip()

    def content_at(self, step: int) -> str:
        if step < 0 or step >= self.history_len:
            return ""
        return str(self.history[step].get("content", ""))

    def prefix_before_mistake(self) -> list[dict[str, Any]]:
        step = self.mistake_step
        if step is None or step < 0 or step >= self.history_len:
            return []
        return self.history[:step]

    def distinct_history_agents(self) -> list[str]:
        agents: set[str] = set()
        for idx in range(self.history_len):
            base_agent = self.base_agent_at(idx)
            directed_target = self.directed_target_at(idx)
            if base_agent:
                agents.add(base_agent)
            if directed_target:
                agents.add(directed_target)
        return sorted(agent for agent in agents if agent)

    def system_prompt_agents(self) -> list[str]:
        return sorted(str(agent) for agent in self.system_prompt.keys())

    def mistake_step_valid(self) -> bool:
        step = self.mistake_step
        return step is not None and 0 <= step < self.history_len

    def mistake_agent_matches_step(self) -> bool:
        step = self.mistake_step
        if step is None:
            return False
        return self.mistake_agent in {self.agent_at(step), self.base_agent_at(step)}

    def mistake_agent_is_directed_target(self) -> bool:
        step = self.mistake_step
        if step is None:
            return False
        return self.mistake_agent == self.directed_target_at(step)


def discover_case_files(repo_path: Path) -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for dataset_type, relative_dir in [
        ("algorithm_generated", ALGORITHM_DIR),
        ("hand_crafted", HANDCRAFTED_DIR),
    ]:
        directory = repo_path / relative_dir
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json"), key=_numeric_sort_key):
            files.append((dataset_type, path))
    return files


def load_case(dataset_type: str, path: Path, repo_path: Path) -> WhoWhenCase:
    raw = json.loads(path.read_text(encoding="utf-8"))
    relative = path.relative_to(repo_path)
    case_id = f"{dataset_type}:{path.stem}"
    return WhoWhenCase(case_id=case_id, dataset_type=dataset_type, path=relative, raw=raw)


def load_cases(repo_path: Path) -> list[WhoWhenCase]:
    return [
        load_case(dataset_type, path, repo_path)
        for dataset_type, path in discover_case_files(repo_path)
    ]


def phase2a_status(case: WhoWhenCase) -> tuple[str, str]:
    if not case.history:
        return "blocker", "empty history"
    if not case.mistake_step_valid():
        return "blocker", "mistake_step is missing or out of range"
    if not case.mistake_agent:
        return "blocker", "mistake_agent is missing"
    if not case.mistake_agent_matches_step():
        if case.mistake_agent_is_directed_target():
            return "warning_directed_target", (
                "mistake_agent is the directed recipient, not the logged speaker at mistake_step"
            )
        return "warning", "mistake_agent does not match agent at mistake_step"
    if case.mistake_step == 0:
        return "candidate_initial_step", "prefix is empty because decisive error is step 0"
    return "candidate", "ordered history and gold intervention point are available"


def case_index_row(case: WhoWhenCase) -> dict[str, str | int | bool]:
    step = case.mistake_step
    status, note = phase2a_status(case)
    prefix_len = len(case.prefix_before_mistake())
    mistake_entry_agent = case.agent_at(step) if step is not None else ""
    return {
        "case_id": case.case_id,
        "dataset_type": case.dataset_type,
        "source_path": str(case.path),
        "question_id": case.question_id,
        "history_len": case.history_len,
        "mistake_agent": case.mistake_agent,
        "mistake_step": "" if step is None else step,
        "mistake_step_valid": case.mistake_step_valid(),
        "mistake_entry_agent": mistake_entry_agent,
        "mistake_entry_base_agent": case.base_agent_at(step) if step is not None else "",
        "mistake_entry_directed_target": case.directed_target_at(step) if step is not None else "",
        "mistake_agent_matches_step": case.mistake_agent_matches_step(),
        "mistake_agent_is_directed_target": case.mistake_agent_is_directed_target(),
        "prefix_len": prefix_len,
        "prefix_empty": prefix_len == 0,
        "has_question": bool(case.question),
        "has_ground_truth": bool(case.ground_truth),
        "has_mistake_reason": bool(case.mistake_reason),
        "system_prompt_agent_count": len(case.system_prompt_agents()),
        "history_agent_count": len(case.distinct_history_agents()),
        "phase2a_status": status,
        "phase2a_note": note,
    }
