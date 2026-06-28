import unittest

from tau2_card_poc.binding_gates import (
    BindingGate,
    PresenceRule,
    evaluate_binding_gate,
)


class BindingGateTests(unittest.TestCase):
    def test_presence_rule_requires_all_patterns(self):
        gate = BindingGate(
            name="money_summary",
            feedback="Missing money summary.",
            rules=[PresenceRule(kind="money", description="money amount")],
        )

        decision = evaluate_binding_gate(gate, "Refund total is $12.34.")

        self.assertTrue(decision.passed)
        self.assertEqual(decision.failed_rules, [])

    def test_presence_rule_reports_missing_pattern(self):
        gate = BindingGate(
            name="tracking_check",
            feedback="Missing tracking number.",
            rules=[PresenceRule(kind="tracking", description="tracking number")],
        )

        decision = evaluate_binding_gate(gate, "The order has shipped.")

        self.assertFalse(decision.passed)
        self.assertEqual(decision.failed_rules, ["tracking number"])

    def test_tracking_rule_requires_tracking_like_token_not_just_phrase(self):
        gate = BindingGate(
            name="tracking_check",
            feedback="Missing tracking number.",
            rules=[PresenceRule(kind="tracking", description="tracking number")],
        )

        decision = evaluate_binding_gate(
            gate,
            "I do not see a tracking number for that canceled order.",
        )

        self.assertFalse(decision.passed)
        self.assertEqual(decision.failed_rules, ["tracking number"])

    def test_tracking_rule_does_not_accept_order_id(self):
        gate = BindingGate(
            name="tracking_check",
            feedback="Missing tracking number.",
            rules=[PresenceRule(kind="tracking", description="tracking number")],
        )

        decision = evaluate_binding_gate(
            gate,
            "The order #W4860251 has been updated successfully.",
        )

        self.assertFalse(decision.passed)
        self.assertEqual(decision.failed_rules, ["tracking number"])

    def test_multiple_rules_must_all_pass(self):
        gate = BindingGate(
            name="compound_summary",
            feedback="Missing compound summary.",
            rules=[
                PresenceRule(kind="money", description="money amount"),
                PresenceRule(kind="status", description="status word"),
            ],
        )

        decision = evaluate_binding_gate(gate, "The refund total is $19.99.")

        self.assertFalse(decision.passed)
        self.assertEqual(decision.failed_rules, ["status word"])

    def test_any_text_requires_non_empty_text(self):
        gate = BindingGate(
            name="non_empty",
            feedback="Missing final response.",
            rules=[PresenceRule(kind="any_text", description="non-empty response")],
        )

        decision = evaluate_binding_gate(gate, "   ")

        self.assertFalse(decision.passed)
        self.assertEqual(decision.failed_rules, ["non-empty response"])

    def test_unknown_rule_kind_is_rejected(self):
        gate = BindingGate(
            name="bad_rule",
            feedback="Bad rule.",
            rules=[PresenceRule(kind="exact_answer", description="exact answer")],
        )

        with self.assertRaises(ValueError):
            evaluate_binding_gate(gate, "Anything.")

    def test_money_rule_can_require_multiple_amounts(self):
        gate = BindingGate(
            name="price_breakdown",
            feedback="Missing price breakdown.",
            rules=[
                PresenceRule(
                    kind="money",
                    description="three money amounts",
                    min_count=3,
                )
            ],
        )

        decision = evaluate_binding_gate(gate, "The total amount due today is $107.09.")

        self.assertFalse(decision.passed)
        self.assertEqual(decision.failed_rules, ["three money amounts"])

    def test_keyword_rule_requires_one_allowed_phrase(self):
        gate = BindingGate(
            name="explicit_superlative",
            feedback="Missing explicit comparison.",
            rules=[
                PresenceRule(
                    kind="keyword",
                    description="most expensive item",
                    keywords=("most expensive", "highest-priced"),
                )
            ],
        )

        decision = evaluate_binding_gate(
            gate,
            "The camera costs $481.50, and the other items are cheaper.",
        )

        self.assertFalse(decision.passed)
        self.assertEqual(decision.failed_rules, ["most expensive item"])


if __name__ == "__main__":
    unittest.main()
