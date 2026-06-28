from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from tau2.agent.llm_agent import LLMAgent
from tau2.data_model.message import AssistantMessage, UserMessage

from tau2_card_poc.binding_gates import (
    BindingGate,
    PresenceRule,
    evaluate_binding_gate,
)
from tau2_card_poc.specs import BindingRetrySpec


class BindingGateAgent(LLMAgent):
    def __init__(
        self,
        *,
        tools,
        domain_policy: str,
        llm: str,
        llm_args: dict | None = None,
        binding_gate: BindingGate | dict[str, Any] | None = None,
        condition: str | None = None,
        max_gate_rejections: int = 1,
    ):
        super().__init__(
            tools=tools,
            domain_policy=domain_policy,
            llm=llm,
            llm_args=llm_args,
        )
        self.binding_gate = binding_gate_from_dict(binding_gate)
        self.condition = condition
        self.max_gate_rejections = max_gate_rejections
        self.gate_events: list[dict[str, Any]] = []
        self._gate_rejections_used = 0

    def generate_next_message(self, message, state):
        assistant_message = self._generate_next_message(message, state)
        assistant_message = self._apply_gate_if_needed(assistant_message, state)
        state.messages.append(assistant_message)
        return assistant_message, state

    def _apply_gate_if_needed(self, assistant_message: AssistantMessage, state):
        if self.binding_gate is None:
            return assistant_message
        if not _is_final_response(assistant_message):
            return assistant_message

        decision = evaluate_binding_gate(self.binding_gate, assistant_message.content)
        if decision.passed:
            self._record_gate_event(decision, retry_used=False)
            return assistant_message

        if self._gate_rejections_used >= self.max_gate_rejections:
            self._record_gate_event(
                decision,
                retry_used=False,
                max_rejections_exhausted=True,
            )
            return assistant_message

        self._gate_rejections_used += 1
        self._record_gate_event(decision, retry_used=True)
        feedback = UserMessage.text(_binding_feedback(self.binding_gate, decision.failed_rules))
        repaired_message = self._generate_next_message(feedback, state)

        if _is_final_response(repaired_message):
            repaired_decision = evaluate_binding_gate(
                self.binding_gate,
                repaired_message.content,
            )
            self._record_gate_event(repaired_decision, retry_used=False)
        return repaired_message

    def _record_gate_event(
        self,
        decision,
        *,
        retry_used: bool,
        max_rejections_exhausted: bool = False,
    ) -> None:
        assert self.binding_gate is not None
        self.gate_events.append(
            {
                "gate_name": self.binding_gate.name,
                "triggered": True,
                "passed": decision.passed,
                "failed_rules": list(decision.failed_rules),
                "retry_used": retry_used,
                "max_rejections_exhausted": max_rejections_exhausted,
            }
        )


def binding_gate_from_dict(
    data: BindingGate | dict[str, Any] | None,
) -> BindingGate | None:
    if data is None:
        return None
    if isinstance(data, BindingGate):
        return data
    return BindingGate(
        name=str(data["name"]),
        feedback=str(data.get("feedback", "")),
        rules=[
            PresenceRule(
                kind=str(rule["kind"]),
                description=str(rule["description"]),
            )
            for rule in data.get("rules", [])
        ],
    )


def build_binding_results_payload(
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
                "implementation": "binding_gate_llm_agent",
                "llm": agent_model,
            },
            "user_info": {
                "implementation": "user_simulator",
                "llm": user_model,
            },
        },
        "simulations": list(simulations),
    }


def register_binding_gate_agent(
    *,
    agent_name: str,
    binding_gate: BindingGate | dict[str, Any] | None,
    condition: str | None = None,
    created_agents: list[BindingGateAgent] | None = None,
) -> str:
    from tau2.registry import registry

    if registry.get_agent_factory(agent_name) is not None:
        return agent_name

    def create_binding_gate_agent(tools, domain_policy, **kwargs):
        agent = BindingGateAgent(
            tools=tools,
            domain_policy=domain_policy,
            llm=kwargs.get("llm"),
            llm_args=kwargs.get("llm_args"),
            binding_gate=binding_gate,
            condition=condition,
        )
        if created_agents is not None:
            created_agents.append(agent)
        return agent

    registry.register_agent_factory(
        create_binding_gate_agent,
        name=agent_name,
        metadata={"binding_gate_condition": condition},
    )
    return agent_name


def run_single_binding_retry(
    spec: BindingRetrySpec,
    *,
    output_dir: str | Path,
    task_loader=None,
    single_task_runner=None,
) -> Path:
    from loguru import logger
    from tau2.data_model.simulation import TextRunConfig
    from tau2.evaluator.evaluator import EvaluationType
    from tau2.run import get_tasks, run_single_task

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_agents: list[BindingGateAgent] = []
    agent_name = register_binding_gate_agent(
        agent_name=_binding_agent_name(
            spec.condition,
            spec.binding_gate,
            seed=spec.seed,
            trial=spec.trial,
        ),
        binding_gate=spec.binding_gate,
        condition=spec.condition,
        created_agents=created_agents,
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
    gate_events = created_agents[-1].gate_events if created_agents else []
    simulation.seed = spec.seed
    simulation.trial = spec.trial
    simulation.info = {
        **(simulation.info or {}),
        "binding_gate_condition": spec.condition,
        "binding_gate_agent": agent_name,
        "binding_gate_events": gate_events,
    }

    result_path = output_dir / "results.json"
    payload = build_binding_results_payload(
        domain=spec.domain,
        condition=spec.condition,
        agent_model=spec.agent_model,
        user_model=spec.user_model,
        seed=spec.seed,
        simulations=[simulation.model_dump(mode="json")],
    )
    result_path.write_text(json.dumps(payload, indent=2))
    return result_path


def _is_final_response(message: AssistantMessage) -> bool:
    return not message.tool_calls and bool((message.content or "").strip())


def _binding_feedback(gate: BindingGate, failed_rules: list[str]) -> str:
    failed = ", ".join(failed_rules) if failed_rules else "the required check"
    return "\n".join(
        [
            "<binding_check_feedback>",
            gate.feedback.strip() or "Your response is missing a required completion check.",
            f"Missing check: {failed}.",
            "Continue the task and satisfy the missing requirement before finalizing.",
            "</binding_check_feedback>",
        ]
    )


def _binding_agent_name(
    condition: str,
    binding_gate: dict[str, Any] | None,
    *,
    seed: int,
    trial: int,
) -> str:
    clean_condition = re.sub(r"[^a-zA-Z0-9_]+", "_", condition).strip("_").lower()
    gate_json = json.dumps(binding_gate, sort_keys=True)
    digest = hashlib.sha1(f"{gate_json}:{seed}:{trial}".encode("utf-8")).hexdigest()[:10]
    return f"binding_gate_llm_agent_{clean_condition}_{digest}"
