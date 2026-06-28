import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from tau2.data_model.message import AssistantMessage, ToolCall, UserMessage

from tau2_card_poc.binding_gates import BindingGate, PresenceRule
from tau2_card_poc.binding_runner import (
    BindingGateAgent,
    register_binding_gate_agent,
    run_single_binding_retry,
)
from tau2_card_poc.specs import BindingRetrySpec


class SequenceBindingAgent(BindingGateAgent):
    def __init__(self, responses, **kwargs):
        super().__init__(
            tools=[],
            domain_policy="Follow retail policy.",
            llm="fake-model",
            binding_gate=kwargs.get("binding_gate"),
            condition="test_condition",
        )
        self.responses = list(responses)

    def _generate_next_message(self, message, state):
        state.messages.append(message)
        return self.responses.pop(0)


class BindingRunnerTests(unittest.TestCase):
    def test_tool_call_message_passes_without_gate_event(self):
        gate = BindingGate(
            name="money_gate",
            feedback="Missing money.",
            rules=[PresenceRule(kind="money", description="money amount")],
        )
        tool_message = AssistantMessage.text(
            "Checking the order.",
            tool_calls=[ToolCall(name="get_order_details", arguments={"order_id": "x"})],
        )
        agent = SequenceBindingAgent([tool_message], binding_gate=gate)
        state = agent.get_init_state()

        result, _ = agent.generate_next_message(UserMessage.text("Please help."), state)

        self.assertEqual(result, tool_message)
        self.assertEqual(agent.gate_events, [])

    def test_failed_final_response_gets_feedback_and_regenerated(self):
        gate = BindingGate(
            name="money_gate",
            feedback="Missing required money amount.",
            rules=[PresenceRule(kind="money", description="money amount")],
        )
        failed_final = AssistantMessage.text("The return is complete.")
        repaired_final = AssistantMessage.text("The return is complete. Refund total is $12.34.")
        agent = SequenceBindingAgent([failed_final, repaired_final], binding_gate=gate)
        state = agent.get_init_state()

        result, state = agent.generate_next_message(UserMessage.text("Please help."), state)

        self.assertEqual(result, repaired_final)
        self.assertNotIn(failed_final, state.messages)
        self.assertIn(repaired_final, state.messages)
        self.assertTrue(
            any(
                isinstance(message, UserMessage)
                and "Missing required money amount" in (message.content or "")
                for message in state.messages
            )
        )
        self.assertEqual(len(agent.gate_events), 2)
        self.assertFalse(agent.gate_events[0]["passed"])
        self.assertTrue(agent.gate_events[0]["retry_used"])
        self.assertTrue(agent.gate_events[1]["passed"])

    def test_run_single_binding_retry_writes_standard_results(self):
        calls = {}

        @dataclass
        class FakeTask:
            id: str

        class FakeSimulation:
            seed = None
            trial = None
            info = None

            def model_dump(self, mode="json"):
                return {
                    "id": "sim-1",
                    "task_id": "43",
                    "seed": self.seed,
                    "trial": self.trial,
                    "info": self.info,
                    "reward_info": {"reward": 1.0},
                    "messages": [],
                }

        def fake_task_loader(domain, task_ids, task_split_name=None):
            calls["task_loader"] = {
                "domain": domain,
                "task_ids": task_ids,
                "task_split_name": task_split_name,
            }
            return [FakeTask(id="43")]

        def fake_single_task_runner(config, task, **kwargs):
            calls["runner"] = {
                "agent": config.agent,
                "domain": config.domain,
                "log_level": config.log_level,
                "task_id": task.id,
                "seed": kwargs["seed"],
                "save_dir": kwargs["save_dir"],
            }
            return FakeSimulation()

        with tempfile.TemporaryDirectory() as tmp:
            result_path = run_single_binding_retry(
                BindingRetrySpec(
                    domain="retail",
                    task_id="43",
                    condition="coarse_binding_gate",
                    binding_gate={
                        "name": "coarse",
                        "feedback": "Re-check all requested outcomes.",
                        "rules": [{"kind": "any_text", "description": "final response"}],
                    },
                    seed=701,
                    trial=0,
                    agent_model="gpt-4.1-mini",
                    user_model="gpt-4.1-mini",
                    log_level="WARNING",
                ),
                output_dir=Path(tmp),
                task_loader=fake_task_loader,
                single_task_runner=fake_single_task_runner,
            )
            payload = json.loads(result_path.read_text())

        self.assertEqual(calls["task_loader"]["task_ids"], ["43"])
        self.assertEqual(calls["runner"]["domain"], "retail")
        self.assertTrue(calls["runner"]["agent"].startswith("binding_gate_llm_agent_"))
        self.assertEqual(payload["info"]["condition"], "coarse_binding_gate")
        self.assertEqual(payload["simulations"][0]["seed"], 701)
        self.assertEqual(
            payload["simulations"][0]["info"]["binding_gate_condition"],
            "coarse_binding_gate",
        )

    def test_register_binding_gate_agent_factory(self):
        from tau2.registry import registry

        agent_name = "binding_gate_agent_test_factory"

        registered_name = register_binding_gate_agent(
            agent_name=agent_name,
            binding_gate={
                "name": "coarse",
                "feedback": "Re-check all requested outcomes.",
                "rules": [{"kind": "any_text", "description": "final response"}],
            },
            condition="coarse_binding_gate",
        )
        factory = registry.get_agent_factory(registered_name)

        agent = factory(
            tools=[],
            domain_policy="Follow retail policy.",
            llm="gpt-4.1-mini",
            llm_args={"temperature": 0},
        )

        self.assertEqual(registered_name, agent_name)
        self.assertEqual(agent.condition, "coarse_binding_gate")
        self.assertEqual(agent.binding_gate.name, "coarse")


if __name__ == "__main__":
    unittest.main()
