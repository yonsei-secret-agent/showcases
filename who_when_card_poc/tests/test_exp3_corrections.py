from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from ww_card_poc.conditions import build_mode_only_card
from ww_card_poc.judging import build_failure_anchored_judge_prompt
from ww_card_poc.results import summarize_judgments
from ww_card_poc.who_when_io import WhoWhenCase


class Exp3CorrectionTests(unittest.TestCase):
    def test_mode_only_card_does_not_sabotage_itself(self) -> None:
        card = build_mode_only_card("unverified or inaccurate factual claim")
        rendered = card.render().lower()

        self.assertNotIn("no case-specific corrective procedure", rendered)
        self.assertNotIn("do not assume this card provides", rendered)
        self.assertNotIn("not as a detailed repair card", rendered)
        self.assertIn("failure mode: unverified or inaccurate factual claim", rendered)

    def test_summary_reports_repair_conditioned_on_concrete_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "judgments.jsonl"
            records = [
                {
                    "case_id": "case-1",
                    "condition": "condition_a",
                    "parsed": {
                        "repair_success": True,
                        "recurs_same_failure": False,
                        "task_relevant": True,
                        "states_relevant_intent": True,
                        "performs_concrete_repair_action": True,
                        "negative_transfer": False,
                        "repair_score": 3,
                    },
                },
                {
                    "case_id": "case-2",
                    "condition": "condition_a",
                    "parsed": {
                        "repair_success": False,
                        "recurs_same_failure": True,
                        "task_relevant": True,
                        "states_relevant_intent": True,
                        "performs_concrete_repair_action": True,
                        "negative_transfer": False,
                        "repair_score": 1,
                    },
                },
                {
                    "case_id": "case-3",
                    "condition": "condition_a",
                    "parsed": {
                        "repair_success": False,
                        "recurs_same_failure": True,
                        "task_relevant": True,
                        "states_relevant_intent": False,
                        "performs_concrete_repair_action": False,
                        "negative_transfer": False,
                        "repair_score": 0,
                    },
                },
            ]
            path.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )

            condition_rows, _ = summarize_judgments(path)

        row = condition_rows[0]
        self.assertEqual(row["repair_success_rate"], 0.3333)
        self.assertEqual(row["concrete_repair_action_rate"], 0.6667)
        self.assertEqual(row["repair_given_concrete_rate"], 0.5)
        self.assertEqual(row["repair_without_concrete_rate"], 0.0)

    def test_failure_anchored_judge_prompt_does_not_use_card_derived_key(self) -> None:
        case = WhoWhenCase(
            case_id="algorithm_generated:test",
            dataset_type="algorithm_generated",
            path=Path("case.json"),
            raw={
                "question": "Find the requested record.",
                "ground_truth": "GOLD_ANSWER",
                "history": [
                    {"name": "Planner", "content": "We need evidence."},
                    {"name": "Executor", "content": "I will use unverified assumed data."},
                ],
                "mistake_agent": "Executor",
                "mistake_step": "1",
                "mistake_reason": "The agent relied on unverified assumed data.",
            },
        )
        generation = {
            "output_text": "I will verify the evidence before using the data.",
            "metadata": {
                "target_missing_check_type": "CARD_DERIVED_CHECK_KEY",
                "target_abstract_corrective_action": "CARD_DERIVED_CORRECTIVE_ACTION",
            },
        }

        prompt = build_failure_anchored_judge_prompt(case, generation)
        rendered = "\n".join(message["content"] for message in prompt)

        self.assertIn("Original failed action", rendered)
        self.assertIn("I will use unverified assumed data.", rendered)
        self.assertIn("Candidate regenerated next action", rendered)
        self.assertNotIn("CARD_DERIVED_CHECK_KEY", rendered)
        self.assertNotIn("CARD_DERIVED_CORRECTIVE_ACTION", rendered)
        self.assertNotIn("Missing-check criterion", rendered)


if __name__ == "__main__":
    unittest.main()
