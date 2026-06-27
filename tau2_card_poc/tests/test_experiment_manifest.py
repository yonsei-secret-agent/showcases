import json
import tempfile
import unittest
from pathlib import Path

from tau2_card_poc.experiment_manifest import (
    ExperimentCondition,
    ExperimentManifest,
    iter_memory_retry_specs,
    load_experiment_manifest,
)


class ExperimentManifestTests(unittest.TestCase):
    def test_loads_manifest_and_expands_specs(self):
        manifest_data = {
            "experiment_id": "exp5_3_rescue_test",
            "domain": "retail",
            "agent_model": "gpt-4.1-mini",
            "user_model": "gpt-4.1-mini",
            "task_ids": ["2", "3"],
            "seeds": [401, 402],
            "conditions": [
                {"name": "no_memory", "runtime_memory": ""},
                {
                    "name": "oracle_single_missing_check_card",
                    "runtime_memory": "Count only variants marked available.",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest_data))

            manifest = load_experiment_manifest(manifest_path)
            specs = list(iter_memory_retry_specs(manifest))

        self.assertEqual(manifest.experiment_id, "exp5_3_rescue_test")
        self.assertEqual(manifest.task_ids, ["2", "3"])
        self.assertEqual([condition.name for condition in manifest.conditions], [
            "no_memory",
            "oracle_single_missing_check_card",
        ])
        self.assertEqual(len(specs), 8)
        self.assertEqual(specs[0].task_id, "2")
        self.assertEqual(specs[0].condition, "no_memory")
        self.assertEqual(specs[0].runtime_memory, "")
        self.assertEqual(specs[0].seed, 401)
        self.assertEqual(specs[0].trial, 0)
        self.assertEqual(specs[-1].task_id, "3")
        self.assertEqual(specs[-1].condition, "oracle_single_missing_check_card")
        self.assertEqual(specs[-1].seed, 402)
        self.assertEqual(specs[-1].trial, 1)

    def test_rejects_duplicate_condition_names(self):
        manifest = ExperimentManifest(
            experiment_id="bad",
            domain="retail",
            agent_model="gpt-4.1-mini",
            user_model="gpt-4.1-mini",
            task_ids=["2"],
            seeds=[401],
            conditions=[
                ExperimentCondition(name="oracle", runtime_memory="a"),
                ExperimentCondition(name="oracle", runtime_memory="b"),
            ],
        )

        with self.assertRaisesRegex(ValueError, "duplicate condition"):
            list(iter_memory_retry_specs(manifest))


if __name__ == "__main__":
    unittest.main()
