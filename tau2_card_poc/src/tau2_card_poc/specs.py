from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryRetrySpec:
    domain: str
    task_id: str
    condition: str
    runtime_memory: str
    seed: int
    trial: int
    agent_model: str
    user_model: str
    task_split_name: str | None = None
    max_steps: int = 100
    max_errors: int = 10
    log_level: str = "INFO"
