import json
import tempfile
import unittest
from pathlib import Path

from tau2_card_poc.binding_batch_runner import (
    binding_manifest_run_output_dir,
    run_binding_manifest,
)
from tau2_card_poc.binding_manifest import (
    BindingExperimentCondition,
    BindingExperimentManifest,
)


class BindingBatchRunnerTests(unittest.TestCase):
    def test_binding_manifest_run_output_dir_is_stable(self):
        manifest = BindingExperimentManifest(
            experiment_id="exp6a",
            domain="retail",
            agent_model="gpt-4.1-mini",
            user_model="gpt-4.1-mini",
            task_ids=["43"],
            seeds=[701],
            conditions=[
                BindingExperimentCondition(name="oracle/gate", binding_gate=None),
            ],
        )

        path = binding_manifest_run_output_dir(
            Path("runs"),
            manifest,
            task_id="43",
            condition="oracle/gate",
            seed=701,
        )

        self.assertEqual(
            path,
            Path("runs") / "exp6a" / "task_43" / "condition_oracle_gate" / "seed_701",
        )

    def test_run_binding_manifest_skips_existing_results_when_resume_is_true(self):
        manifest = BindingExperimentManifest(
            experiment_id="exp6a",
            domain="retail",
            agent_model="gpt-4.1-mini",
            user_model="gpt-4.1-mini",
            task_ids=["43"],
            seeds=[701],
            conditions=[BindingExperimentCondition(name="no_gate", binding_gate=None)],
        )
        calls = []

        def fake_single_run(spec, *, output_dir):
            calls.append((spec, output_dir))
            output_dir.mkdir(parents=True, exist_ok=True)
            result_path = output_dir / "results.json"
            result_path.write_text(json.dumps({"simulations": []}))
            return result_path

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            first = run_binding_manifest(
                manifest,
                output_root=output_root,
                single_run=fake_single_run,
            )
            second = run_binding_manifest(
                manifest,
                output_root=output_root,
                single_run=fake_single_run,
            )

        self.assertEqual(len(calls), 1)
        self.assertEqual(first[0].status, "ran")
        self.assertEqual(second[0].status, "skipped")


if __name__ == "__main__":
    unittest.main()
