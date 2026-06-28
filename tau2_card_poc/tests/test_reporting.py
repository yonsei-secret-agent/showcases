import json
import tempfile
import unittest
from pathlib import Path

from tau2_card_poc.reporting import (
    collect_experiment_records,
    condition_summary,
    pairwise_condition_matrix,
    paired_condition_summary,
    gate_condition_summary,
    task_stability_summary,
    write_gate_condition_summary_csv,
    write_paired_condition_summary_csv,
    write_condition_summary_csv,
    write_pairwise_condition_matrix_csv,
    write_per_run_outcomes_csv,
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

    def test_summarizes_paired_rescue_against_baseline(self):
        records = [
            _record("2", "no_memory", 401, 0.0),
            _record("2", "oracle", 401, 1.0),
            _record("3", "no_memory", 401, 1.0),
            _record("3", "oracle", 401, 0.0),
            _record("4", "no_memory", 401, 0.0),
            _record("4", "oracle", 401, 0.0),
        ]

        paired = paired_condition_summary(records, baseline_condition="no_memory")

        self.assertEqual(paired["oracle"].paired_attempts, 3)
        self.assertEqual(paired["oracle"].baseline_successes, 1)
        self.assertEqual(paired["oracle"].condition_successes, 1)
        self.assertEqual(paired["oracle"].paired_rescues, 1)
        self.assertEqual(paired["oracle"].paired_regressions, 1)
        self.assertAlmostEqual(paired["oracle"].success_delta, 0.0)
        self.assertAlmostEqual(paired["oracle"].rescue_rate_among_baseline_failures, 0.5)

    def test_writes_paired_condition_summary_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "paired.csv"
            paired = paired_condition_summary(
                [
                    _record("2", "no_memory", 401, 0.0),
                    _record("2", "oracle", 401, 1.0),
                ],
                baseline_condition="no_memory",
            )

            write_paired_condition_summary_csv(paired, out)
            text = out.read_text()

        self.assertIn("condition,paired_attempts,baseline_successes", text)
        self.assertIn("oracle,1,0,1,1,0,1.0000,1.0000,0.0000", text)

    def test_writes_per_run_outcomes_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "per_run.csv"
            records = [
                _record(
                    "2",
                    "oracle",
                    401,
                    1.0,
                    db_reward=1.0,
                    communicate_reward=None,
                    nl_assertion_reward=1.0,
                    result_path=Path("exp/task_2/condition_oracle/seed_401/results.json"),
                )
            ]

            write_per_run_outcomes_csv(records, out)
            text = out.read_text()

        self.assertIn(
            "experiment_id,task_id,seed,condition,success,final_reward,"
            "db_reward,communicate_reward,nl_assertion_reward,"
            "gate_trigger_count,gate_failure_count,gate_retry_count,"
            "gate_final_passed,result_path",
            text,
        )
        self.assertIn(
            "exp,2,401,oracle,1,1.0000,1.0000,,1.0000,0,0,0,,"
            "exp/task_2/condition_oracle/seed_401/results.json",
            text,
        )

    def test_summarizes_and_writes_gate_condition_metrics(self):
        records = [
            _record(
                "43",
                "oracle_gate",
                701,
                1.0,
                gate_trigger_count=2,
                gate_failure_count=1,
                gate_retry_count=1,
                gate_final_passed=True,
            ),
            _record(
                "43",
                "oracle_gate",
                702,
                0.0,
                gate_trigger_count=1,
                gate_failure_count=1,
                gate_retry_count=0,
                gate_final_passed=False,
            ),
        ]

        summary = gate_condition_summary(records)["oracle_gate"]

        self.assertEqual(summary.attempts, 2)
        self.assertEqual(summary.runs_with_gate_trigger, 2)
        self.assertEqual(summary.total_gate_triggers, 3)
        self.assertEqual(summary.total_gate_failures, 2)
        self.assertEqual(summary.total_gate_retries, 1)
        self.assertEqual(summary.final_gate_passes, 1)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "gate_summary.csv"
            write_gate_condition_summary_csv({"oracle_gate": summary}, out)
            text = out.read_text()

        self.assertIn("condition,attempts,runs_with_gate_trigger", text)
        self.assertIn("oracle_gate,2,2,1.0000,3,2,1,1", text)

    def test_pairwise_condition_matrix_compares_all_condition_pairs(self):
        records = [
            _record("2", "no_memory", 401, 0.0),
            _record("2", "generic", 401, 1.0),
            _record("2", "oracle", 401, 1.0),
            _record("3", "no_memory", 401, 1.0),
            _record("3", "generic", 401, 0.0),
            _record("3", "oracle", 401, 1.0),
            _record("4", "no_memory", 401, 0.0),
            _record("4", "generic", 401, 0.0),
            _record("4", "oracle", 401, 0.0),
        ]

        matrix = pairwise_condition_matrix(records)
        generic_vs_oracle = matrix[("generic", "oracle")]
        no_vs_generic = matrix[("generic", "no_memory")]

        self.assertEqual(generic_vs_oracle.paired_attempts, 3)
        self.assertEqual(generic_vs_oracle.condition_a_successes, 1)
        self.assertEqual(generic_vs_oracle.condition_b_successes, 2)
        self.assertEqual(generic_vs_oracle.a_beats_b, 0)
        self.assertEqual(generic_vs_oracle.b_beats_a, 1)
        self.assertEqual(generic_vs_oracle.ties_success, 1)
        self.assertEqual(generic_vs_oracle.ties_failure, 1)
        self.assertAlmostEqual(generic_vs_oracle.success_delta_a_minus_b, -1 / 3)
        self.assertEqual(no_vs_generic.a_beats_b, 1)
        self.assertEqual(no_vs_generic.b_beats_a, 1)

    def test_writes_pairwise_condition_matrix_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pairwise.csv"
            matrix = pairwise_condition_matrix(
                [
                    _record("2", "generic", 401, 1.0),
                    _record("2", "oracle", 401, 0.0),
                    _record("3", "generic", 401, 0.0),
                    _record("3", "oracle", 401, 0.0),
                ]
            )

            write_pairwise_condition_matrix_csv(matrix, out)
            text = out.read_text()

        self.assertIn("condition_a,condition_b,paired_attempts", text)
        self.assertIn("generic,oracle,2,1,0,1,0,0,1,0.5000", text)


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


def _record(
    task_id,
    condition,
    seed,
    reward,
    *,
    db_reward=None,
    communicate_reward=None,
    nl_assertion_reward=None,
    result_path=Path("results.json"),
    gate_trigger_count=0,
    gate_failure_count=0,
    gate_retry_count=0,
    gate_final_passed=None,
):
    from tau2_card_poc.reporting import ExperimentRecord

    return ExperimentRecord(
        experiment_id="exp",
        task_id=task_id,
        condition=condition,
        seed=seed,
        trial=0,
        reward=reward,
        success=reward == 1.0,
        db_reward=db_reward,
        communicate_reward=communicate_reward,
        nl_assertion_reward=nl_assertion_reward,
        result_path=result_path,
        gate_trigger_count=gate_trigger_count,
        gate_failure_count=gate_failure_count,
        gate_retry_count=gate_retry_count,
        gate_final_passed=gate_final_passed,
    )


if __name__ == "__main__":
    unittest.main()
