import json
import tempfile
import unittest
from pathlib import Path

from tau2_card_poc.results_io import group_task_outcomes, load_result_records


class ResultIoTests(unittest.TestCase):
    def test_loads_success_and_failure_records_from_monolithic_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            results_path = Path(tmp) / "results.json"
            results_path.write_text(
                json.dumps(
                    {
                        "info": {
                            "seed": 300,
                            "agent_info": {
                                "implementation": "llm_agent",
                                "llm": "gpt-4.1-mini",
                                "llm_args": {"temperature": 0},
                            },
                            "user_info": {
                                "implementation": "user_simulator",
                                "llm": "gpt-4.1-mini",
                                "llm_args": {"temperature": 0},
                            },
                        },
                        "tasks": [{"id": "0"}, {"id": "1"}],
                        "simulations": [
                            {
                                "id": "sim-success",
                                "task_id": "0",
                                "trial": 0,
                                "seed": 300,
                                "termination_reason": "user_stop",
                                "agent_cost": 0.01,
                                "user_cost": 0.02,
                                "reward_info": {
                                    "reward": 1.0,
                                    "reward_breakdown": {
                                        "DB": 1.0,
                                        "NL_ASSERTION": 1.0,
                                        "COMMUNICATE": 1.0,
                                    },
                                },
                                "messages": [
                                    {"role": "user", "content": "hello"},
                                    {
                                        "role": "assistant",
                                        "content": None,
                                        "tool_calls": [{"name": "get_order"}],
                                    },
                                ],
                            },
                            {
                                "id": "sim-failure",
                                "task_id": "1",
                                "trial": 0,
                                "seed": 300,
                                "termination_reason": "agent_stop",
                                "reward_info": {
                                    "reward": 0.0,
                                    "reward_breakdown": {
                                        "DB": 0.0,
                                        "COMMUNICATE": 1.0,
                                    },
                                },
                                "messages": [
                                    {
                                        "role": "assistant",
                                        "content": "I cannot help.",
                                    }
                                ],
                            },
                        ],
                    }
                )
            )

            records = load_result_records(results_path)

        self.assertEqual([r.simulation_id for r in records], ["sim-success", "sim-failure"])
        self.assertEqual([r.task_id for r in records], ["0", "1"])
        self.assertEqual([r.success for r in records], [True, False])
        self.assertEqual([r.reward for r in records], [1.0, 0.0])
        self.assertEqual(records[0].db_reward, 1.0)
        self.assertEqual(records[0].nl_assertion_reward, 1.0)
        self.assertEqual(records[1].communicate_reward, 1.0)
        self.assertEqual(records[0].tool_call_names, ["get_order"])
        self.assertEqual(records[0].agent_model, "gpt-4.1-mini")
        self.assertEqual(records[0].user_model, "gpt-4.1-mini")
        self.assertEqual(records[0].gate_trigger_count, 0)

    def test_loads_binding_gate_metrics_from_simulation_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            results_path = Path(tmp) / "results.json"
            results_path.write_text(
                json.dumps(
                    {
                        "info": {},
                        "simulations": [
                            {
                                "id": "sim-gated",
                                "task_id": "43",
                                "trial": 0,
                                "seed": 701,
                                "info": {
                                    "binding_gate_events": [
                                        {
                                            "triggered": True,
                                            "passed": False,
                                            "retry_used": True,
                                            "failed_rules": ["money amount"],
                                        },
                                        {
                                            "triggered": True,
                                            "passed": True,
                                            "retry_used": False,
                                            "failed_rules": [],
                                        },
                                    ]
                                },
                                "reward_info": {"reward": 1.0},
                                "messages": [],
                            }
                        ],
                    }
                )
            )

            records = load_result_records(results_path)

        self.assertEqual(records[0].gate_trigger_count, 2)
        self.assertEqual(records[0].gate_failure_count, 1)
        self.assertEqual(records[0].gate_retry_count, 1)
        self.assertTrue(records[0].gate_final_passed)

    def test_groups_repeated_task_attempts_by_stability(self):
        records = [
            _record("stable-success", "0", True),
            _record("stable-success-2", "0", True),
            _record("stable-failure", "1", False),
            _record("stable-failure-2", "1", False),
            _record("mixed-success", "2", True),
            _record("mixed-failure", "2", False),
        ]

        outcomes = group_task_outcomes(records)

        self.assertEqual(outcomes["0"].group, "stable_success")
        self.assertEqual(outcomes["0"].success_count, 2)
        self.assertEqual(outcomes["1"].group, "stable_failure")
        self.assertEqual(outcomes["1"].failure_count, 2)
        self.assertEqual(outcomes["2"].group, "mixed")
        self.assertEqual(outcomes["2"].total_attempts, 2)


def _record(simulation_id, task_id, success):
    from tau2_card_poc.results_io import Tau2ResultRecord

    return Tau2ResultRecord(
        simulation_id=simulation_id,
        task_id=task_id,
        trial=None,
        seed=None,
        reward=1.0 if success else 0.0,
        success=success,
        db_reward=None,
        communicate_reward=None,
        nl_assertion_reward=None,
        termination_reason=None,
        agent_cost=None,
        user_cost=None,
        agent_model=None,
        user_model=None,
        tool_call_names=[],
        message_count=0,
        gate_trigger_count=0,
        gate_failure_count=0,
        gate_retry_count=0,
        gate_final_passed=None,
    )


if __name__ == "__main__":
    unittest.main()
