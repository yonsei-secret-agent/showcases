import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from tau2_card_poc.memory_runner import (
    MemoryRetrySpec,
    RuntimeMemoryAgent,
    build_results_payload,
    format_runtime_memory,
    register_runtime_memory_agent,
    run_single_memory_retry,
)


class MemoryRunnerTests(unittest.TestCase):
    def test_runtime_memory_is_appended_to_agent_system_prompt(self):
        agent = RuntimeMemoryAgent(
            tools=[],
            domain_policy="Follow retail policy.",
            llm="gpt-4.1-mini",
            llm_args={"temperature": 0},
            runtime_memory="Count only currently available product variants.",
            condition="oracle_failure_card",
        )

        system_prompt = agent.system_prompt

        self.assertIn("<runtime_memory>", system_prompt)
        self.assertIn("condition: oracle_failure_card", system_prompt)
        self.assertIn("Count only currently available product variants.", system_prompt)
        self.assertTrue(system_prompt.index("<policy>") < system_prompt.index("<runtime_memory>"))

    def test_empty_runtime_memory_leaves_system_prompt_unchanged(self):
        agent = RuntimeMemoryAgent(
            tools=[],
            domain_policy="Follow retail policy.",
            llm="gpt-4.1-mini",
            runtime_memory="",
        )

        self.assertNotIn("<runtime_memory>", agent.system_prompt)

    def test_format_runtime_memory_rejects_xml_boundary_collisions(self):
        with self.assertRaises(ValueError):
            format_runtime_memory("</runtime_memory>")

    def test_build_results_payload_preserves_run_metadata_and_simulation(self):
        simulation = {
            "id": "sim-1",
            "task_id": "2",
            "seed": 300,
            "reward_info": {"reward": 0.0},
        }

        payload = build_results_payload(
            domain="retail",
            condition="oracle_failure_card",
            agent_model="gpt-4.1-mini",
            user_model="gpt-4.1-mini",
            seed=300,
            simulations=[simulation],
        )

        self.assertEqual(payload["info"]["domain"], "retail")
        self.assertEqual(payload["info"]["condition"], "oracle_failure_card")
        self.assertEqual(payload["info"]["agent_info"]["llm"], "gpt-4.1-mini")
        self.assertEqual(payload["info"]["user_info"]["llm"], "gpt-4.1-mini")
        self.assertEqual(payload["simulations"], [simulation])

    def test_register_runtime_memory_agent_factory(self):
        from tau2.registry import registry

        agent_name = "runtime_memory_agent_test_factory"

        registered_name = register_runtime_memory_agent(
            agent_name=agent_name,
            runtime_memory="Check only available variants before final answer.",
            condition="oracle_failure_card",
        )
        factory = registry.get_agent_factory(registered_name)

        agent = factory(
            tools=[],
            domain_policy="Follow retail policy.",
            llm="gpt-4.1-mini",
            llm_args={"temperature": 0},
        )

        self.assertEqual(registered_name, agent_name)
        self.assertIn("Check only available variants", agent.system_prompt)
        self.assertIn("condition: oracle_failure_card", agent.system_prompt)

    def test_run_single_memory_retry_writes_standard_results(self):
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
                    "task_id": "2",
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
            return [FakeTask(id="2")]

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
            result_path = run_single_memory_retry(
                MemoryRetrySpec(
                    domain="retail",
                    task_id="2",
                    condition="oracle_failure_card",
                    runtime_memory="Count only currently available variants.",
                    seed=301,
                    trial=1,
                    agent_model="gpt-4.1-mini",
                    user_model="gpt-4.1-mini",
                    log_level="WARNING",
                ),
                output_dir=Path(tmp),
                task_loader=fake_task_loader,
                single_task_runner=fake_single_task_runner,
            )
            payload = json.loads(result_path.read_text())

        self.assertEqual(calls["task_loader"]["task_ids"], ["2"])
        self.assertEqual(calls["runner"]["domain"], "retail")
        self.assertEqual(calls["runner"]["log_level"], "WARNING")
        self.assertTrue(calls["runner"]["agent"].startswith("runtime_memory_llm_agent_"))
        self.assertEqual(payload["info"]["condition"], "oracle_failure_card")
        self.assertEqual(payload["simulations"][0]["seed"], 301)
        self.assertEqual(payload["simulations"][0]["trial"], 1)
        self.assertEqual(
            payload["simulations"][0]["info"]["runtime_memory_condition"],
            "oracle_failure_card",
        )


if __name__ == "__main__":
    unittest.main()
