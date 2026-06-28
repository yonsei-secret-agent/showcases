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


if __name__ == "__main__":
    unittest.main()
