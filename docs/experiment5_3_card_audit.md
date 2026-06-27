# Experiment 5.3 Card Audit

## Status

```text
status: pre-run audit completed
date: 2026-06-27
manifest: tau2_card_poc/experiments/exp5_3_rescue_20.json
selected tasks: 20
conditions: no_memory, generic_policy_card, oracle_single_missing_check_card, hard_mismatched_card
```

## Purpose

This audit records why each `oracle_single_missing_check_card` is considered
attribution-derived rather than arbitrary.

The cards are based on Experiment 5.2 baseline harvest artifacts:

```text
source:
  third_party/tau2-bench/data/simulations/exp5_2_baseline_harvest_30/results.json

evidence used:
  - task request
  - official reward breakdown
  - failed expected action checks
  - NL_ASSERTION component when present
  - representative failed final assistant response
```

The cards are still oracle upper-bound cards. They are not predicted by an
automatic attribution model yet.

## Automated Checks

Manifest consistency:

```text
spec_count: 240
task_count: 20
condition_count: 4
seed_count: 3
empty_specs: 60  # no_memory only
```

Leakage pattern checks on oracle/mismatch cards:

```text
order_id pattern: 0
long numeric id pattern: 0
runtime_memory XML tag pattern: 0
```

These checks catch direct leakage of order IDs, product/item IDs, payment IDs,
and runtime-memory tag injection. They do not prove the absence of semantic
leakage, so the cards should still be read before running the full 240-run
experiment.

## Oracle Card Basis

| task | baseline signal | oracle missing-check pattern |
| --- | --- | --- |
| 1 | DB failed on exchange; final response exchanged a near-match item despite a user fallback. | Check exact replacement feature constraints before exchanging; if unavailable, follow fallback. |
| 2 | DB and NL failed; return branch was not completed while product-count question was also present. | Verify the return branch is completed before finalizing a dual-intent count plus return task. |
| 3 | DB passed, NL failed; product-count answer omitted while modification succeeded. | Communicate the currently available variant count separately from the item modification. |
| 4 | DB passed, NL failed; same count omission pattern as task 3 across multiple pending items. | Communicate the currently available variant count separately from the item modifications. |
| 7 | DB failed on exchange after confirmation narrowed the scope. | Use the user's latest confirmation to narrow exchange scope before tool call. |
| 16 | DB/NL mixed; failed checks include refund calculation and delivered-item return. | Compute and communicate the total refund from completed cancellation/return actions. |
| 19 | DB passed, NL failed; savings amounts requested by the user were not communicated. | Compute and communicate the separate requested savings amounts. |
| 20 | DB failed on product-detail checks and bulk pending-order modification. | Check product details and select eligible most-expensive variants while preserving the hard constraint. |
| 27 | DB failed and run transferred instead of completing the feasible preferred branch. | If only one branch is feasible, perform the user's preferred exchange branch. |
| 28 | DB/NL failed; failed check is refund calculation and final amount included a blocked cancellation. | Calculate refund only from completed and allowed actions. |
| 34 | DB failed on pending-order address mutation; final response used an address inconsistent with stored target. | Use the exact stored address source rather than inventing or substituting an address. |
| 36 | DB failed on cheapest-variant order modification. | Verify cheapest substitutions satisfy the user's budget condition before modifying. |
| 41 | DB failed on user/profile/order address and item mutations. | Apply confirmed address correction to every required record, not just one. |
| 71 | DB failed after user narrowed final scope during confirmation. | Treat latest confirmation as the final scope and mutate only that scope. |
| 95 | DB mostly passed but NL failed; user asked for item-level and total exchange difference. | Communicate per-item exchange differences and combined amount. |
| 98 | DB failed on several exchange/cancel actions in a multi-order request. | Map every requested action to its order and complete each required tool call. |
| 99 | DB mixed; multi-order exchange actions were partially missed. | Complete exchange tool calls for each relevant order before summarizing. |
| 103 | DB/NL failed; delivered returns, pending modifications, and tracking were conflated. | Split delivered returns, pending modifications, and tracking lookup into separate branches. |
| 104 | DB/NL failed; delivered returns across different orders were skipped or only partially handled. | Enumerate all matching delivered items across orders before pending modifications. |
| 112 | DB mixed; pending item modifications across multiple orders were partially completed. | Complete all requested item modifications across orders before finalizing. |

## Hard Mismatch Rule

The `hard_mismatched_card` condition uses an orthogonal failure pattern per
task. It intentionally avoids broad guidance such as:

```text
verify evidence
check policy
complete all user goals
double-check tool arguments
```

This matters because earlier Who&When experiments showed that broad
verification cards can accidentally repair many tasks and collapse the
negative control.

## Claim Boundary

If Experiment 5.3 succeeds, it supports only this upper-bound claim:

```text
Oracle attribution-derived single-check cards can improve fresh tau2 retry
success on a curated 20-case retail subset.
```

It still does not prove:

```text
predicted attribution works
cross-task transfer works
multi-agent who attribution is useful
closed-loop self-improvement is complete
```
