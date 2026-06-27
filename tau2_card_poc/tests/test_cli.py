import json
import tempfile
import unittest
from pathlib import Path

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
            self.assertTrue((out_dir / "task_stability.csv").exists())


if __name__ == "__main__":
    unittest.main()
