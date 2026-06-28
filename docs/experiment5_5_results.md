# Experiment 5.5 Results: Variability and Saturation Pre-Check

## Status

Phase 5.5A and Phase 5.5C completed.

Do not run the full 6-condition Exp5.5F main experiment on this task pool.

This result should be read as a cheap stop/go gate, not as a standalone powered
test. Its value is that it prevented an expensive full run on a pool that was
not informative enough for the intended precise-vs-coarse prose-memory
contrast.

## What Was Run

### 5.5A Variability Calibration

Manifest:

```text
tau2_card_poc/experiments/exp5_5a_variability_calibration.json
```

Design:

```text
5 tasks
x 1 seed
x 3 no-memory repeats
= 15 runs
```

Tasks:

```text
16, 2, 19, 103, 54
```

### 5.5C Saturation Pre-Check

Manifest:

```text
tau2_card_poc/experiments/exp5_5c_saturation_precheck.json
```

Design:

```text
6 held-out candidate tasks
x 4 conditions
x 3 seeds
= 72 runs
```

Tasks:

```text
2, 3, 19, 43, 47, 103
```

Conditions:

```text
no_memory
generic_policy_card
failure_mode_only_card
oracle_single_missing_check_card_v1
```

## 5.5A Result: Same-Seed Instability Exists

Repeated no-memory results:

```text
task | successes / 3 | success values | DB values     | NL values
2    | 0 / 3         | 0,0,0          | 1,1,1         | 0,0,0
16   | 0 / 3         | 0,0,0          | 1,1,0         | 0,0,0
19   | 2 / 3         | 1,1,0          | 1,1,1         | 1,1,0
54   | 3 / 3         | 1,1,1          | 1,1,1         | 1,1,1
103  | 0 / 3         | 0,0,0          | 0,0,0         | 1,0,1
```

Flip counts:

```text
success flip cells: 1 / 5
DB component flip cells: 1 / 5
NL component flip cells: 2 / 5
```

Interpretation:

```text
Same-seed retry is not deterministic enough to support deterministic rescue
claims. Exp5.5 results must be read as condition-rate and task-level evidence,
not as exact paired-seed causal proof.
```

Task `54` was removed from the pre-check after calibration because it was
already 3/3 successful under no memory.

## 5.5C Aggregate Result

Condition summary:

```text
condition                         successes / attempts   success rate
generic_policy_card               6 / 18                 0.3333
oracle_single_missing_check_v1    6 / 18                 0.3333
failure_mode_only_card            5 / 18                 0.2778
no_memory                         5 / 18                 0.2778
```

Pairwise summary:

```text
oracle_v1 - generic_policy_card:      0 / 18 delta
oracle_v1 - failure_mode_only_card:  +1 / 18 delta
oracle_v1 - no_memory:               +1 / 18 delta
generic_policy_card - no_memory:     +1 / 18 delta
```

Component means:

```text
condition                         DB mean   NL_ASSERTION mean
failure_mode_only_card            0.7778    0.2778
generic_policy_card               0.7222    0.4444
no_memory                         0.6667    0.2778
oracle_single_missing_check_v1    0.6667    0.3889
```

## Task-Level Matrix

```text
task | no_memory | generic | mode_only | oracle_v1
2    | 0/3       | 0/3     | 0/3       | 0/3
3    | 0/3       | 0/3     | 0/3       | 0/3
19   | 0/3       | 0/3     | 0/3       | 0/3
43   | 2/3       | 2/3     | 2/3       | 3/3
47   | 3/3       | 2/3     | 3/3       | 3/3
103  | 0/3       | 2/3     | 0/3       | 0/3
```

Task classification:

```text
all-fail / likely not rescued by prose memory:
  2, 3, 19

already-winnable / saturated:
  47

weak oracle-specific signal:
  43

generic-only signal:
  103
```

## Candidate Pool Validity

The pre-check also found that the selected pool did not cleanly instantiate the
target family.

The intended Exp5.5 family was:

```text
DB/tool side mostly completed,
but a required user-facing communication/check is missing.
```

The actual pool was weaker:

```text
2, 3, 19:
  all conditions failed. These cells are non-informative for specificity.
  DB sometimes passed, but NL_ASSERTION never moved under prose memory.

47:
  already 3/3 successful under no memory, so it is saturated and cannot show
  rescue.

103:
  not a clean DB=1 / NL=0 communication-missing case. No-memory DB was mixed
  and oracle DB was 0/3, while generic improved both DB/NL in some seeds. This
  looks more like a broader DB/tool completion or branch-control problem than
  the target narrow missing-check family.

43:
  the only clean candidate with a weak oracle-specific signal in this pre-check.
```

Therefore, Exp5.5C is thin evidence by itself. The report should use it as part
of the cumulative pattern across Who&When, Exp5.3, Exp5.4, and Exp5.5, not as an
isolated proof that precise prose memory fails.

## Interpretation

The pre-check does not show a usable specificity gradient.

Expected GREEN pattern:

```text
no_memory < generic <= failure_mode_only < oracle_v1
```

Observed pattern:

```text
conditions are indistinguishable within the calibrated noise band

aggregate:
  no_memory and failure_mode_only: 5 / 18
  generic and oracle_v1:           6 / 18
```

This means:

```text
1. the +1/18 oracle-vs-mode and oracle-vs-no-memory deltas are too small to
   interpret as wins
2. precise missing-check prose memory does not separate from generic policy
   memory on this candidate pool
3. failure_mode_only does not improve over no_memory
4. most candidate tasks are either all-fail, saturated, or outside the intended
   narrow family
5. the only strict oracle task is task 43, while task 103 favors generic memory
```

Therefore, running the full 6-condition Exp5.5F main experiment on this pool
would likely produce another ambiguous/noisy result.

## Caveats

Task `2` and task `3` repeatedly emitted tau2 evaluator warnings about a golden
`get_product_details` action. They still completed and received reward, but
they should not be treated as clean held-out evidence without audit.

Task `47` emitted evaluator warnings for malformed order IDs in golden actions
and was already 3/3 successful under no memory. It is not useful for a rescue
gate.

One pre-check run initially crashed inside tau2 evaluator replay with:

```text
ValueError: Tool message not expected. Tool messages should always follow a tool call.
```

The same cell succeeded on resume, so this is treated as an intermittent tau2
evaluator/transcript issue, not a deterministic failed condition.

## Decision

Do not scale this prose-card condition set.

This is a YELLOW/RED pre-check result for the runtime prose-memory hypothesis on
this pool:

```text
runtime memory is live,
but this candidate pool cannot show that precise oracle prose memory is the
active ingredient.
```

The clean next move is not a new card variant. It is either:

```text
1. write the report with this as the final prose-memory gate, or
2. run the reserved routing/retrieval mini-probe, where attribution selects
   which memory/check/intervention to apply instead of writing richer prose.
```

If running the routing/retrieval mini-probe, do not reuse only the tasks where
memory happened to help in Exp5.5C. Harvest or filter a fresh pool with the
intended inclusion criteria, then set the seed count from the observed
variability. Otherwise the pivot probe will inherit the same selection and
noise problems.

## Supported Claim

```text
In tau2 retail fresh retries, short runtime memories can move official reward,
but the current precise missing-check oracle prose memory does not outperform
generic policy memory in the Exp5.5 held-out pre-check.
```

Stronger report-level claim, based on the cumulative arc rather than Exp5.5C
alone:

```text
Across the Who&When trace-prefix experiments and tau2 fresh-retry experiments,
precise attribution rendered as prose memory has repeatedly failed to separate
cleanly from coarse/generic reminders once leakage, judge coupling, task
saturation, and variability are controlled. This motivates moving the
attribution signal from prose content toward routing, retrieval, intervention
selection, or credit assignment.
```

## Not Supported

```text
1. precise attribution-derived prose memory beats generic reminders
2. failure-mode-only routing is sufficient
3. this task pool is suitable for a powered Exp5.5 main run
4. predicted attribution should be tested on this prose-memory interface next
5. Exp5.5C alone proves that precise attribution is useless
```
