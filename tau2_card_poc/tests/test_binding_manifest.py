import json
import tempfile
import unittest
from pathlib import Path

from tau2_card_poc.binding_manifest import (
    BindingExperimentCondition,
    BindingExperimentManifest,
    iter_binding_retry_specs,
    load_binding_experiment_manifest,
)


class BindingManifestTests(unittest.TestCase):
    def test_loads_manifest_and_expands_specs(self):
        manifest_data = {
            "experiment_id": "exp6a_binding_smoke",
            "domain": "retail",
            "agent_model": "gpt-4.1-mini",
            "user_model": "gpt-4.1-mini",
            "task_ids": ["43"],
            "seeds": [701, 702],
            "conditions": [
                {"name": "no_gate", "binding_gate": None},
                {
                    "name": "coarse_binding_gate",
                    "binding_gate": {
                        "name": "coarse",
                        "feedback": "Re-check all outcomes.",
                        "rules": [{"kind": "any_text", "description": "final response"}],
                    },
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest_data))
            manifest = load_binding_experiment_manifest(manifest_path)
            specs = list(iter_binding_retry_specs(manifest))

        self.assertEqual(manifest.experiment_id, "exp6a_binding_smoke")
        self.assertEqual(len(specs), 4)
        self.assertEqual(specs[0].task_id, "43")
        self.assertEqual(specs[0].condition, "no_gate")
        self.assertIsNone(specs[0].binding_gate)
        self.assertEqual(specs[-1].condition, "coarse_binding_gate")
        self.assertEqual(specs[-1].binding_gate["name"], "coarse")
        self.assertEqual(specs[-1].seed, 702)
        self.assertEqual(specs[-1].trial, 1)

    def test_expands_per_task_binding_gate(self):
        manifest_data = {
            "experiment_id": "exp6c",
            "domain": "retail",
            "agent_model": "gpt-4.1-mini",
            "user_model": "gpt-4.1-mini",
            "task_ids": ["43", "95"],
            "seeds": [701],
            "conditions": [
                {
                    "name": "oracle_precise_binding_gate",
                    "per_task_binding_gate": {
                        "43": {
                            "name": "tracking_detail",
                            "feedback": "Missing tracking detail.",
                            "rules": [{"kind": "tracking", "description": "tracking number"}],
                        },
                        "95": {
                            "name": "money_summary",
                            "feedback": "Missing money summary.",
                            "rules": [{"kind": "money", "description": "money amount"}],
                        },
                    },
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest_data))
            manifest = load_binding_experiment_manifest(manifest_path)
            specs = list(iter_binding_retry_specs(manifest))

        self.assertEqual(specs[0].task_id, "43")
        self.assertEqual(specs[0].binding_gate["name"], "tracking_detail")
        self.assertEqual(specs[1].task_id, "95")
        self.assertEqual(specs[1].binding_gate["name"], "money_summary")

    def test_rejects_duplicate_condition_names(self):
        manifest = BindingExperimentManifest(
            experiment_id="bad",
            domain="retail",
            agent_model="gpt-4.1-mini",
            user_model="gpt-4.1-mini",
            task_ids=["43"],
            seeds=[701],
            conditions=[
                BindingExperimentCondition(name="oracle", binding_gate=None),
                BindingExperimentCondition(name="oracle", binding_gate=None),
            ],
        )

        with self.assertRaisesRegex(ValueError, "duplicate condition"):
            list(iter_binding_retry_specs(manifest))

    def test_rejects_missing_per_task_binding_gate(self):
        manifest = BindingExperimentManifest(
            experiment_id="bad",
            domain="retail",
            agent_model="gpt-4.1-mini",
            user_model="gpt-4.1-mini",
            task_ids=["43", "95"],
            seeds=[701],
            conditions=[
                BindingExperimentCondition(
                    name="oracle",
                    binding_gate=None,
                    per_task_binding_gate={"43": {"name": "x", "feedback": "", "rules": []}},
                ),
            ],
        )

        with self.assertRaisesRegex(ValueError, "missing per-task binding gate"):
            list(iter_binding_retry_specs(manifest))


if __name__ == "__main__":
    unittest.main()
