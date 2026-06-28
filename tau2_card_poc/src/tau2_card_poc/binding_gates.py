from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PresenceRule:
    kind: str
    description: str
    min_count: int = 1
    keywords: tuple[str, ...] = ()


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
        matches = re.findall(r"(?:\$|usd\s*)?\b\d+(?:,\d{3})*(?:\.\d{2})\b", normalized)
        return len(matches) >= rule.min_count
    if rule.kind == "count":
        return len(re.findall(r"\b\d+\b", normalized)) >= rule.min_count
    if rule.kind == "tracking":
        has_tracking_like_token = bool(re.search(r"\b\d{9,}\b", text))
        return has_tracking_like_token
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
    if rule.kind == "keyword":
        return any(keyword.lower() in normalized for keyword in rule.keywords)
    raise ValueError(f"unsupported presence rule kind: {rule.kind}")
