from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from tau2.agent.llm_agent import LLMAgent


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


def format_runtime_memory(memory: str, *, condition: str | None = None) -> str:
    memory = memory.strip()
    if not memory:
        return ""
    if "</runtime_memory>" in memory or "<runtime_memory" in memory:
        raise ValueError("runtime memory must not contain runtime_memory XML tags")

    lines = ["<runtime_memory>"]
    if condition:
        lines.append(f"condition: {condition}")
    lines.append(memory)
    lines.append("</runtime_memory>")
    return "\n".join(lines)


class RuntimeMemoryAgent(LLMAgent):
    def __init__(
        self,
        *,
        tools,
        domain_policy: str,
        llm: str,
        llm_args: dict | None = None,
        runtime_memory: str = "",
        condition: str | None = None,
    ):
        super().__init__(
            tools=tools,
            domain_policy=domain_policy,
            llm=llm,
            llm_args=llm_args,
        )
        self.runtime_memory = runtime_memory
        self.condition = condition

    @property
    def system_prompt(self) -> str:
        memory = format_runtime_memory(
            self.runtime_memory,
            condition=self.condition,
        )
        if not memory:
            return super().system_prompt
        return f"{super().system_prompt}\n\n{memory}"


def build_results_payload(
    *,
    domain: str,
    condition: str,
    agent_model: str,
    user_model: str,
    seed: int,
    simulations: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "info": {
            "domain": domain,
            "condition": condition,
            "seed": seed,
            "agent_info": {
                "implementation": "runtime_memory_llm_agent",
                "llm": agent_model,
            },
            "user_info": {
                "implementation": "user_simulator",
                "llm": user_model,
            },
        },
        "simulations": list(simulations),
    }


def register_runtime_memory_agent(
    *,
    agent_name: str,
    runtime_memory: str,
    condition: str | None = None,
) -> str:
    from tau2.registry import registry

    if registry.get_agent_factory(agent_name) is not None:
        return agent_name

    def create_runtime_memory_agent(tools, domain_policy, **kwargs):
        return RuntimeMemoryAgent(
            tools=tools,
            domain_policy=domain_policy,
            llm=kwargs.get("llm"),
            llm_args=kwargs.get("llm_args"),
            runtime_memory=runtime_memory,
            condition=condition,
        )

    registry.register_agent_factory(
        create_runtime_memory_agent,
        name=agent_name,
        metadata={"runtime_memory_condition": condition},
    )
    return agent_name


def run_single_memory_retry(
    spec: MemoryRetrySpec,
    *,
    output_dir: str | Path,
    task_loader=None,
    single_task_runner=None,
) -> Path:
    from tau2.data_model.simulation import TextRunConfig
    from tau2.evaluator.evaluator import EvaluationType
    from tau2.run import get_tasks, run_single_task
    from loguru import logger

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    agent_name = register_runtime_memory_agent(
        agent_name=_runtime_agent_name(spec.condition, spec.runtime_memory),
        runtime_memory=spec.runtime_memory,
        condition=spec.condition,
    )
    loader = task_loader or get_tasks
    runner = single_task_runner or run_single_task
    tasks = loader(
        spec.domain,
        task_ids=[spec.task_id],
        task_split_name=spec.task_split_name,
    )
    if len(tasks) != 1:
        raise ValueError(f"expected exactly one task for {spec.task_id}, got {len(tasks)}")

    config = TextRunConfig(
        domain=spec.domain,
        agent=agent_name,
        user="user_simulator",
        llm_agent=spec.agent_model,
        llm_args_agent={"temperature": 0.0},
        llm_user=spec.user_model,
        llm_args_user={"temperature": 0.0},
        max_steps=spec.max_steps,
        max_errors=spec.max_errors,
        log_level=spec.log_level,
        seed=spec.seed,
    )
    logger.remove()
    logger.add(sys.stderr, level=spec.log_level)
    simulation = runner(
        config,
        tasks[0],
        seed=spec.seed,
        evaluation_type=EvaluationType.ALL,
        save_dir=output_dir / "logs",
        verbose_logs=False,
    )
    simulation.seed = spec.seed
    simulation.trial = spec.trial
    simulation.info = {
        **(simulation.info or {}),
        "runtime_memory_condition": spec.condition,
        "runtime_memory_agent": agent_name,
    }

    result_path = output_dir / "results.json"
    payload = build_results_payload(
        domain=spec.domain,
        condition=spec.condition,
        agent_model=spec.agent_model,
        user_model=spec.user_model,
        seed=spec.seed,
        simulations=[simulation.model_dump(mode="json")],
    )
    result_path.write_text(json.dumps(payload, indent=2))
    return result_path


def _runtime_agent_name(condition: str, runtime_memory: str) -> str:
    clean_condition = re.sub(r"[^a-zA-Z0-9_]+", "_", condition).strip("_").lower()
    digest = hashlib.sha1(runtime_memory.encode("utf-8")).hexdigest()[:10]
    return f"runtime_memory_llm_agent_{clean_condition}_{digest}"
