import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tau2_card_poc.cli import main


class CliTests(unittest.TestCase):
    def test_summarize_command_writes_summary_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_dir = root / "exp5_3" / "task_2" / "condition_no_memory" / "seed_401"
            result_dir.mkdir(parents=True)
            (result_dir / "results.json").write_text(
                json.dumps(
                    {
                        "info": {"condition": "no_memory"},
                        "simulations": [
                            {
                                "id": "sim",
                                "task_id": "2",
                                "seed": 401,
                                "trial": 0,
                                "reward_info": {
                                    "reward": 0.0,
                                    "reward_breakdown": {"DB": 1.0},
                                },
                                "messages": [],
                            }
                        ],
                    }
                )
            )
            out_dir = root / "reports"

            code = main(["summarize", str(root / "exp5_3"), "--out-dir", str(out_dir)])

            self.assertEqual(code, 0)
            self.assertTrue((out_dir / "condition_summary.csv").exists())
            self.assertTrue((out_dir / "paired_condition_summary.csv").exists())
            self.assertTrue((out_dir / "per_run_outcomes.csv").exists())
            self.assertTrue((out_dir / "pairwise_condition_matrix.csv").exists())
            self.assertTrue((out_dir / "task_stability.csv").exists())
            self.assertTrue((out_dir / "gate_condition_summary.csv").exists())

    def test_run_binding_manifest_command_invokes_binding_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "binding_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "experiment_id": "exp6a",
                        "domain": "retail",
                        "agent_model": "gpt-4.1-mini",
                        "user_model": "gpt-4.1-mini",
                        "task_ids": ["43"],
                        "seeds": [701],
                        "conditions": [{"name": "no_gate", "binding_gate": None}],
                    }
                )
            )
            output_root = root / "runs"

            with patch("tau2_card_poc.binding_batch_runner.run_binding_manifest") as run:
                run.return_value = []
                code = main(
                    [
                        "run-binding-manifest",
                        str(manifest_path),
                        "--output-root",
                        str(output_root),
                    ]
                )

        self.assertEqual(code, 0)
        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs["output_root"], str(output_root))


if __name__ == "__main__":
    unittest.main()
