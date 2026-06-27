import json
import tempfile
import unittest
from pathlib import Path

from tau2_card_poc.reporting import (
    collect_experiment_records,
    condition_summary,
    task_stability_summary,
    write_condition_summary_csv,
)


class ReportingTests(unittest.TestCase):
    def test_collects_records_from_manifest_run_tree_and_summarizes_conditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_result(
                root / "exp5_3" / "task_2" / "condition_no_memory" / "seed_401",
                condition="no_memory",
                task_id="2",
                seed=401,
                reward=0.0,
                db=1.0,
                nl=0.0,
            )
            _write_result(
                root / "exp5_3" / "task_2" / "condition_oracle" / "seed_401",
                condition="oracle",
                task_id="2",
                seed=401,
                reward=1.0,
                db=1.0,
                nl=1.0,
            )

            records = collect_experiment_records(root / "exp5_3")
            summary = condition_summary(records)

        self.assertEqual(len(records), 2)
        self.assertEqual(summary["no_memory"].attempts, 1)
        self.assertEqual(summary["no_memory"].successes, 0)
        self.assertEqual(summary["oracle"].successes, 1)
        self.assertEqual(summary["oracle"].mean_reward, 1.0)

    def test_collects_records_from_monolithic_tau2_results_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results_path = root / "results.json"
            results_path.write_text(
                json.dumps(
                    {
                        "simulations": [
                            {
                                "id": "sim-2",
                                "task_id": "2",
                                "seed": 401,
                                "trial": 0,
                                "reward_info": {
                                    "reward": 0.0,
                                    "reward_breakdown": {"DB": 1.0},
                                },
                                "messages": [],
                            }
                        ]
                    }
                )
            )

            records = collect_experiment_records(root, default_condition="no_memory")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].experiment_id, root.name)
        self.assertEqual(records[0].condition, "no_memory")
        self.assertEqual(records[0].task_id, "2")

    def test_groups_baseline_records_by_task_stability(self):
        records = [
            _record("2", "no_memory", 401, 0.0),
            _record("2", "no_memory", 402, 0.0),
            _record("3", "no_memory", 401, 1.0),
            _record("3", "no_memory", 402, 0.0),
            _record("4", "no_memory", 401, 1.0),
            _record("4", "no_memory", 402, 1.0),
        ]

        stability = task_stability_summary(records)

        self.assertEqual(stability["2"].group, "stable_failure")
        self.assertEqual(stability["3"].group, "mixed")
        self.assertEqual(stability["4"].group, "stable_success")

    def test_writes_condition_summary_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "summary.csv"
            write_condition_summary_csv(
                {"oracle": condition_summary([_record("2", "oracle", 401, 1.0)])["oracle"]},
                out,
            )

            text = out.read_text()

        self.assertIn("condition,attempts,successes,success_rate,mean_reward", text)
        self.assertIn("oracle,1,1,1.0000,1.0000", text)


def _write_result(path, *, condition, task_id, seed, reward, db, nl):
    path.mkdir(parents=True, exist_ok=True)
    payload = {
        "info": {"condition": condition},
        "simulations": [
            {
                "id": f"{task_id}-{condition}-{seed}",
                "task_id": task_id,
                "seed": seed,
                "trial": 0,
                "reward_info": {
                    "reward": reward,
                    "reward_breakdown": {"DB": db, "NL_ASSERTION": nl},
                },
                "messages": [],
            }
        ],
    }
    (path / "results.json").write_text(json.dumps(payload))


def _record(task_id, condition, seed, reward):
    from tau2_card_poc.reporting import ExperimentRecord

    return ExperimentRecord(
        experiment_id="exp",
        task_id=task_id,
        condition=condition,
        seed=seed,
        trial=0,
        reward=reward,
        success=reward == 1.0,
        db_reward=None,
        communicate_reward=None,
        nl_assertion_reward=None,
        result_path=Path("results.json"),
    )


if __name__ == "__main__":
    unittest.main()
