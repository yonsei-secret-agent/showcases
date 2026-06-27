import json
import tempfile
import unittest
from pathlib import Path

from tau2_card_poc.batch_runner import manifest_run_output_dir, run_manifest
from tau2_card_poc.experiment_manifest import ExperimentCondition, ExperimentManifest


class BatchRunnerTests(unittest.TestCase):
    def test_manifest_run_output_dir_is_stable_and_separate_per_cell(self):
        manifest = ExperimentManifest(
            experiment_id="exp5_3",
            domain="retail",
            agent_model="gpt-4.1-mini",
            user_model="gpt-4.1-mini",
            task_ids=["2"],
            seeds=[401],
            conditions=[ExperimentCondition(name="oracle/card", runtime_memory="x")],
        )

        path = manifest_run_output_dir(
            Path("runs"),
            manifest,
            task_id="2",
            condition="oracle/card",
            seed=401,
        )

        self.assertEqual(
            path,
            Path("runs") / "exp5_3" / "task_2" / "condition_oracle_card" / "seed_401",
        )

    def test_run_manifest_skips_existing_results_when_resume_is_true(self):
        manifest = ExperimentManifest(
            experiment_id="exp5_3",
            domain="retail",
            agent_model="gpt-4.1-mini",
            user_model="gpt-4.1-mini",
            task_ids=["2"],
            seeds=[401],
            conditions=[ExperimentCondition(name="no_memory", runtime_memory="")],
        )
        calls = []

        def fake_single_run(spec, output_dir):
            calls.append((spec, output_dir))
            output_dir.mkdir(parents=True, exist_ok=True)
            result_path = output_dir / "results.json"
            result_path.write_text(json.dumps({"simulations": []}))
            return result_path

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            first = run_manifest(manifest, output_root=output_root, single_run=fake_single_run)
            second = run_manifest(manifest, output_root=output_root, single_run=fake_single_run)

        self.assertEqual(len(calls), 1)
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].status, "ran")
        self.assertEqual(len(second), 1)
        self.assertEqual(second[0].status, "skipped")


if __name__ == "__main__":
    unittest.main()
