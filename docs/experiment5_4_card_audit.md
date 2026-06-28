# Experiment 5.4 Card Audit

## Status

Initial card audit complete for:

```text
tau2_card_poc/experiments/exp5_4_tool_completion_targeted.json
```

This audit checks whether the planned Experiment 5.4 cards follow the
Experiment 5.4 constraints before any model runs.

## Manifest Summary

```text
experiment_id: exp5_4_tool_completion_targeted
domain: retail
agent_model: gpt-4.1-mini
user_model: gpt-4.1-mini
tasks: 16, 95, 36, 103, 19, 41, 104
seeds: 501, 502, 503
conditions: 5
total planned runs: 105
```

Task `20` is excluded. The Exp5.4 audit found that task 20 appears dominated by
exact variant-selection / tool-argument matching rather than a tool-side
completion-ledger failure.

## Conditions

```text
no_memory
generic_policy_card_v2
oracle_single_missing_check_card_v1
oracle_tool_completion_card_v2
hard_mismatched_card_v2
```

## Leakage Check

The new `oracle_tool_completion_card_v2` and `hard_mismatched_card_v2` cards were
checked for obvious exact leakage patterns:

```text
exact order IDs
exact item IDs
exact product IDs
exact refund amounts
exact price differences
tracking numbers
payment method IDs
tool argument field names such as order_id / item_ids / new_item_ids
```

Result:

```text
No obvious exact leakage found in the new v2 oracle or mismatch cards.
```

The manifest still contains `oracle_single_missing_check_card_v1` text copied
from Exp5.3 for comparison. Those cards are intentionally unchanged.

## Scaffold-Drift Check

The v2 oracle cards were checked against the Experiment 5.4 construct guardrail:

```text
Do not decompose the whole task unless the branch was implicated by the audited
failure.
```

Summary:

```text
task 16:
  v2 stays anchored to refund-contributing cancellation/return branches and
  total refund communication.

task 95:
  v2 stays anchored to exchange tool completion and per-exchange price
  difference communication.

task 36:
  v2 stays anchored to the budget-gated pending item modification branch.

task 103:
  v2 stays anchored to pending address mutation, pending item mutation, and
  tracking communication. These are the branches where v1 completed NL but
  missed DB.

task 19:
  v2 stays anchored to feasible return action plus separate savings
  communication. This task mainly audits mismatch contamination.

task 41:
  v2 stays anchored to address-record updates plus the pending item mutation
  that v1 missed.

task 104:
  v2 stays anchored to delivered returns, pending mutation, and tracking
  communication because the audited failures split across DB and NL branches.
```

Risk:

```text
Tasks 103 and 104 are close to broad task scaffolding because their audited
failure is genuinely multi-branch. Their results should be interpreted
carefully. They are allowed in Exp5.4 because the audit showed that v1 handled
some branches while missing other required DB/tool branches.
```

## Mismatch v2 Check

The new mismatch cards are intentionally narrow and mostly irrelevant to the
target task:

```text
task 16: stored-address update only
task 95: pending-address correction only
task 36: delivered-return refund total only
task 103: catalog availability count only
task 19: pending-address fallback only
task 41: delivered-return total only
task 104: catalog availability count only
```

These are stricter than Exp5.3 mismatch cards because they explicitly say not
to apply the card to the target task's action class.

Remaining caveat:

```text
Mismatch success can still happen from model stochasticity or generic task
competence. Therefore Exp5.4 GREEN requires oracle_v2 strict wins over mismatch
and not just aggregate improvement.
```

## Retention vs Repair Roles

Retention tasks:

```text
16, 95
```

These test whether v2 preserves clean oracle-positive cases from Exp5.3.

Repair tasks:

```text
36, 103, 19, 41, 104
```

These are where GREEN evidence must come from. If oracle_v2 only wins on 16 and
95, Exp5.4 is not GREEN.

## Decision

The manifest is ready for the next validation step:

```text
same-seed determinism probe
```

Do not run the full 105-run targeted rerun until the same-seed probe confirms
that repeated no-memory cells are stable enough for paired interpretation.
