# Experiment 5.4 Audit: Exp5.3 Failure Modes Before Card v2

## Status

Initial qualitative audit complete for the planned Experiment 5.4 task set.

This audit uses existing Experiment 5.3 artifacts only. No new model runs were
performed.

Sources:

```text
reports/exp5_3_rescue_20/per_run_outcomes.csv
reports/exp5_3_rescue_20/pairwise_condition_matrix.csv
third_party/tau2-bench/data/simulations/exp5_3_rescue_20/
third_party/tau2-bench/data/tau2/domains/retail/tasks.json
tau2_card_poc/experiments/exp5_3_rescue_20.json
```

## Audit Purpose

Experiment 5.3 was AMBIGUOUS:

```text
generic_policy_card              16 / 60
oracle_single_missing_check_card 15 / 60
hard_mismatched_card             13 / 60
no_memory                        12 / 60
```

The main diagnostic was:

```text
oracle had the highest NL_ASSERTION mean,
but the lowest DB mean.
```

This audit checks whether that happened because the oracle v1 cards pointed at
the right issue but failed to force tool-side completion.

## Representative Seeds

```text
task 16  seed 502
task 95  seed 501
task 36  seed 503
task 103 seed 501
task 19  seed 501
task 41  seed 501
task 104 seed 501
task 20  seed 501
```

The selected seeds expose the clearest condition-level differences for each
task role.

## Task-Level Audit

### Task 16: Oracle-Positive Retention

Role:

```text
oracle-positive retention
```

Task requirement:

```text
Cancel all pending orders, return the received watch, and communicate the total
refund amount.
```

Expected reward components:

```text
DB: cancel two pending orders and return one delivered watch.
NL: tell the total refund amount.
```

Representative seed:

```text
502
```

Outcomes:

```text
no_memory: 0.0, DB 0.0, NL 0.0
generic:   0.0, DB 1.0, NL 0.0
oracle:    1.0, DB 1.0, NL 1.0
mismatch:  0.0, DB 1.0, NL 0.0
```

Audit:

```text
The generic and mismatch cards completed the DB side but omitted the required
total refund communication. Oracle v1 added the refund-total check and rescued
the NL side without hurting DB.
```

Interpretation:

```text
This is a clean retention case. Oracle v2 should not regress it.
It does not prove that a broader branch ledger is needed.
```

Recommended v2 treatment:

```text
Keep the refund-total missing check.
Only add a completion ledger over refund-contributing branches if it does not
weaken the explicit total-communication requirement.
```

### Task 95: Oracle-Positive Retention

Role:

```text
oracle-positive retention
```

Task requirement:

```text
Exchange two delivered laptops and communicate both per-item price differences
plus the total amount due/refund.
```

Representative seed:

```text
501
```

Outcomes:

```text
no_memory: 0.0, DB 1.0, NL 0.0
generic:   0.0, DB 0.0, NL 0.0
oracle:    1.0, DB 1.0, NL 1.0
mismatch:  0.0, DB 1.0, NL 0.0
```

Audit:

```text
No-memory and mismatch completed the exchange DB actions but failed the per-item
price-difference NL assertions. Generic over-verified and did not execute the
exchange tool calls. Oracle v1 was the only condition that satisfied both DB and
NL.
```

Interpretation:

```text
This is another retention case. It supports the value of a specific
communication/check reminder, not broad task scaffolding.
```

Recommended v2 treatment:

```text
Do not broaden this into a full branch ledger. Preserve the price-difference
communication check and ensure exchange tool completion remains explicit.
```

### Task 36: Generic Beats Oracle

Role:

```text
generic-beats-oracle repair candidate
```

Task requirement:

```text
If payment split is not possible, identify the most expensive item and price,
then modify the order by switching selected items to cheapest options if that
brings the total under budget.
```

Representative seed:

```text
503
```

Outcomes:

```text
no_memory: 0.0, DB 0.0, NL 1.0
generic:   1.0, DB 1.0, NL 1.0
oracle:    0.0, DB 0.0, NL 1.0
mismatch:  0.0, DB 0.0, NL 1.0
```

Audit:

```text
All conditions satisfied the NL assertions. The difference was DB/tool
completion. Generic executed the complete item-modification action. Oracle v1
checked the budget condition and performed modifications, but did not match the
required multi-item modification action.
```

Interpretation:

```text
This supports a targeted v2 card, but only if it remains anchored to the audited
failure: budget check must lead to the complete item-modification tool action.
```

Recommended v2 treatment:

```text
failure anchor: budget-conditioned cheapest-variant replacement
tool completion gap: incomplete or non-matching multi-item modification
v2 shape: budget check + one ledger entry requiring the complete modification
          set before final response
```

### Task 103: Generic Beats Oracle

Role:

```text
generic-beats-oracle repair candidate
```

Task requirement:

```text
Return delivered items, update a pending order address, change a pending item,
and provide a cancelled-order tracking number.
```

Representative seed:

```text
501
```

Outcomes:

```text
no_memory: 0.0, DB 1.0, NL 0.0
generic:   1.0, DB 1.0, NL 1.0
oracle:    0.0, DB 0.0, NL 1.0
mismatch:  0.0, DB 0.0, NL 1.0
```

Audit:

```text
Oracle v1 found and communicated the tracking number, but did not execute the
pending address update or pending item modification. Generic completed both DB
branches and communicated the tracking number.
```

Interpretation:

```text
This is the clearest v2 candidate. The old card over-focused on branch
separation/tracking and did not force completion of the pending-order mutation
branches.
```

Recommended v2 treatment:

```text
failure anchor: conflating delivered returns, pending mutations, and tracking
tool completion gap: tracking communicated while pending mutations were not done
v2 shape: ledger only over the failure-implicated pending mutation branches plus
          tracking communication
```

Do not turn this into a full task scaffold beyond the audited branches.

### Task 19: Mismatch Beats Oracle

Role:

```text
mismatch-control repair candidate
```

Task requirement:

```text
Return a water bottle, evaluate whether exchange of pet bed and office chair is
possible, and communicate savings for both options.
```

Representative seed:

```text
501
```

Outcomes:

```text
no_memory: 0.0, DB 0.0, NL 0.0
generic:   0.0, DB 0.0, NL 0.0
oracle:    0.0, DB 1.0, NL 0.0
mismatch:  1.0, DB 1.0, NL 1.0
```

Audit:

```text
Oracle v1 rescued the DB return branch but failed to communicate the exchange
savings. The hard mismatch unexpectedly succeeded; it likely acted as a useful
generic action/reminder rather than a clean orthogonal negative control.
```

Interpretation:

```text
This is not clean evidence against oracle content. It is mainly evidence that
the Exp5.3 mismatch control was contaminated for this task.
```

Recommended v2 treatment:

```text
Use this task to test stricter mismatch design.
Oracle v2 should preserve the separate-savings communication check and ensure
the feasible return branch remains completed.
```

### Task 41: Mismatch Beats Oracle

Role:

```text
mismatch-control repair candidate
```

Task requirement:

```text
Modify a pending jigsaw item, correct both pending-order addresses, and update
the user profile address.
```

Representative seed:

```text
501
```

Outcomes:

```text
no_memory: 0.0, DB 0.0, NL 1.0
generic:   0.0, DB 0.0, NL 1.0
oracle:    0.0, DB 0.0, NL 1.0
mismatch:  1.0, DB 1.0, NL 1.0
```

Audit:

```text
Oracle v1 completed address updates but missed or failed to match the item
modification action. The mismatch card was nominally about product count and
should have been orthogonal; the success appears likely to be stochastic or due
to the base model, not the mismatch content.
```

Interpretation:

```text
This task is useful for reproduction and stricter mismatch checks, but not as a
strong attribution-content signal.
```

Recommended v2 treatment:

```text
failure anchor: all required address records plus item modification must be done
tool completion gap: item modification omitted or not matched
v2 shape: address completion must not substitute for the pending item mutation
```

### Task 104: Mismatch Beats Oracle

Role:

```text
mismatch-control repair candidate
```

Task requirement:

```text
Return all qualifying delivered bookshelf/jigsaw/backpack items, update a
pending order item and address, and provide cancelled-order tracking number.
```

Representative seed:

```text
501
```

Outcomes:

```text
no_memory: 0.0, DB 0.0, NL 0.0
generic:   0.0, DB 1.0, NL 0.0
oracle:    0.0, DB 0.0, NL 1.0
mismatch:  1.0, DB 1.0, NL 1.0
```

Audit:

```text
Oracle v1 got the NL/tracking side but failed the pending item modification DB
action. Generic got DB but missed tracking. The mismatch succeeded, so the
current mismatch control is not a reliable negative control here.
```

Interpretation:

```text
This is a v2 candidate only if the card remains anchored to the audited failure:
tracking communication must not replace pending item/address mutation and return
completion.
```

Recommended v2 treatment:

```text
failure anchor: enumerating matching delivered returns plus pending mutation and
tracking
tool completion gap: one required DB branch omitted while NL/tracking is handled
v2 shape: ledger over the failure-implicated DB branches and tracking
communication
```

### Task 20: Hard/No-Success Diagnostic

Role:

```text
hard/no-success diagnostic
```

Task requirement:

```text
Upgrade eligible pending-order items to the most expensive variants, preserving
the shoe-size constraint, and pay with gift card if possible.
```

Representative seed:

```text
501
```

Outcomes:

```text
no_memory: 0.0, DB 0.0, NL 1.0
generic:   0.0, DB 0.0, NL 1.0
oracle:    0.0, DB 0.0, NL 1.0
mismatch:  0.0, DB 0.0, NL 1.0
```

Audit:

```text
All conditions attempted or described item modification, but all missed the DB
check. This looks less like a completion-ledger problem and more like exact
variant-selection/tool-argument difficulty.
```

Interpretation:

```text
Do not include task 20 in Exp5.4D merely to fill the diagnostic slot. It is not
currently shown to be card-recoverable by a tool-side completion ledger.
```

Recommended v2 treatment:

```text
Exclude from the first Exp5.4D targeted rerun unless a separate audit finds a
card-recoverable failure anchor. Inspect task 28 or another candidate before
choosing the optional diagnostic slot.
```

## Cross-Task Findings

### Finding 1: v2 Is Justified Only for a Subset

The audit supports v2 conversion for:

```text
36, 103, 104
```

These are cases where the old card or oracle behavior got the explanation/NL
side right but failed to complete a required DB branch.

Task 41 is a weaker v2 candidate because the mismatch success may be stochastic.
Task 19 is primarily a mismatch-control contamination case.

### Finding 2: Retention Tasks Should Not Drive GREEN

Tasks:

```text
16, 95
```

These already showed strong oracle v1 behavior. They should verify that v2 does
not regress clean wins. They should not count as the main evidence that v2 fixed
Exp5.3 failures.

### Finding 3: Exp5.3 Mismatch Was Not Clean Enough

At least tasks 19, 41, and 104 show that the hard mismatch condition sometimes
acted like a useful retail procedure or succeeded independently of card content.
Exp5.4 needs stricter mismatch design.

### Finding 4: Task 20 Is Not Ready as Diagnostic Slot

Task 20 appears dominated by exact variant-selection/tool-argument matching.
The first Exp5.4D targeted rerun should not include it unless a separate audit
finds a completion-ledger-recoverable failure.

## Decision

Proceed to card v2 design, but with constraints:

```text
1. v2 must preserve the audited missing check.
2. v2 may add a completion ledger only for failure-implicated branches.
3. v2 must not list the full task as a scaffold.
4. retention tasks 16 and 95 must not regress.
5. GREEN must come from repair tasks, not only retention tasks.
6. mismatch v2 must be redesigned before rerun.
7. task 20 should be excluded unless additional audit changes this judgment.
```

This audit supports a targeted Exp5.4D rerun, but not a broader scale-up.
