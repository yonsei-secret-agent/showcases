from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PresenceRule:
    kind: str
    description: str


@dataclass(frozen=True)
class BindingGate:
    name: str
    feedback: str
    rules: list[PresenceRule]


@dataclass(frozen=True)
class BindingGateDecision:
    passed: bool
    failed_rules: list[str]


def evaluate_binding_gate(gate: BindingGate, final_response: str | None) -> BindingGateDecision:
    text = final_response or ""
    failed_rules = [
        rule.description for rule in gate.rules if not _presence_rule_passes(rule, text)
    ]
    return BindingGateDecision(passed=not failed_rules, failed_rules=failed_rules)


def _presence_rule_passes(rule: PresenceRule, text: str) -> bool:
    normalized = text.lower()
    if rule.kind == "any_text":
        return bool(text.strip())
    if rule.kind == "money":
        return bool(re.search(r"(?:\$|usd\s*)?\b\d+(?:,\d{3})*(?:\.\d{2})\b", normalized))
    if rule.kind == "count":
        return bool(re.search(r"\b\d+\b", normalized))
    if rule.kind == "tracking":
        tracking_words = ("tracking number", "tracking #", "tracking:")
        has_tracking_word = any(word in normalized for word in tracking_words)
        has_tracking_like_token = bool(re.search(r"\b[A-Z0-9]{8,}\b", text))
        return has_tracking_word or has_tracking_like_token
    if rule.kind == "status":
        status_words = (
            "pending",
            "processed",
            "cancelled",
            "canceled",
            "shipped",
            "delivered",
            "returned",
            "exchanged",
            "refunded",
            "approved",
            "denied",
        )
        return any(word in normalized for word in status_words)
    if rule.kind == "comparison":
        comparison_words = (
            "both",
            "each",
            "separate",
            "separately",
            "difference",
            "compare",
            "comparison",
            "option",
        )
        return any(word in normalized for word in comparison_words)
    raise ValueError(f"unsupported presence rule kind: {rule.kind}")
