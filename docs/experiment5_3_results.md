# Experiment 5.3 Results: tau2 20-Case Fresh Rescue Gate

## Summary

Experiment 5.3 ran the 20 selected tau2 retail tasks with four conditions:

```text
no_memory
generic_policy_card
oracle_single_missing_check_card
hard_mismatched_card
```

Scale:

```text
20 tasks x 4 conditions x 3 seeds = 240 runs
agent model: gpt-4.1-mini
user model: gpt-4.1-mini
reward: official tau2 reward
```

Raw simulation files are under:

```text
third_party/tau2-bench/data/simulations/exp5_3_rescue_20/
```

Committed summary artifacts:

```text
reports/exp5_3_rescue_20/condition_summary.csv
reports/exp5_3_rescue_20/paired_condition_summary.csv
reports/exp5_3_rescue_20/task_condition_matrix.csv
reports/exp5_3_rescue_20/component_summary.csv
reports/exp5_3_rescue_20/task_stability.csv
```

## Headline Result

This is not a clean GREEN result.

```text
condition                         successes / attempts   success rate
generic_policy_card               16 / 60                0.2667
oracle_single_missing_check_card  15 / 60                0.2500
hard_mismatched_card              13 / 60                0.2167
no_memory                         12 / 60                0.2000
```

The oracle card improves over no memory, but only by +3 successes out of 60
runs. It does not beat the generic policy card.

## Paired Rescue

Paired against `no_memory` on the same `(task_id, seed)`:

```text
condition                         rescues   regressions   success delta
generic_policy_card               10        6             +0.0667
oracle_single_missing_check_card  9         6             +0.0500
hard_mismatched_card              9         8             +0.0167
```

Interpretation:

```text
oracle does rescue some no-memory failures,
but generic rescues slightly more,
and oracle also regresses 6 cases where no-memory succeeded.
```

## Component Breakdown

```text
condition                         DB mean   NL_ASSERTION mean
generic_policy_card               0.5167    0.5965
oracle_single_missing_check_card  0.4000    0.6842
hard_mismatched_card              0.4667    0.6667
no_memory                         0.4500    0.5965
```

This is important. Oracle cards appear to help communication / assertion quality,
but they do not improve DB/tool-state success in aggregate. In fact, DB mean is
lowest under oracle. That means the current oracle cards may steer the agent
toward explaining the right missing check without reliably completing the
required tool-side action.

## Task-Level Pattern

Strong oracle-positive tasks:

```text
task 16:
  no_memory 1/3
  generic 0/3
  oracle 3/3
  mismatch 0/3

task 95:
  no_memory 0/3
  generic 1/3
  oracle 3/3
  mismatch 0/3
```

Weak oracle-positive tasks:

```text
task 1:
  oracle +1 over no_memory and mismatch, tied with generic

task 34:
  oracle +1 over no_memory and mismatch, but below generic
```

Warning tasks where generic beats oracle:

```text
task 34:  generic 3/3, oracle 2/3
task 36:  generic 2/3, oracle 0/3
task 41:  generic 1/3, oracle 0/3
task 103: generic 2/3, oracle 0/3
```

Warning tasks where hard mismatch beats oracle:

```text
task 19:  mismatch 2/3, oracle 0/3
task 36:  mismatch 1/3, oracle 0/3
task 41:  mismatch 2/3, oracle 0/3
task 103: mismatch 1/3, oracle 0/3
task 104: mismatch 1/3, oracle 0/3
```

Tasks with no success in any condition:

```text
2, 3, 4, 20, 28, 71, 99, 112
```

These are likely low-actionability, wrong-card, or benchmark/evaluator-hard cases.
They should not be treated as evidence that cards cannot work in general, but
they do cap this particular pilot.

## Strata Check

Using the Experiment 5.2 baseline-harvest labels:

```text
baseline stable-failure selected tasks:
  no_memory 5/36
  generic 8/36
  oracle 4/36
  mismatch 6/36

baseline mixed selected tasks:
  no_memory 7/24
  generic 8/24
  oracle 11/24
  mismatch 7/24
```

The oracle advantage comes from the mixed/diversity tasks, not from the
baseline-stable failure stratum.

Using this run's own no-memory stable-failure subset:

```text
current no-memory stable-failure tasks:
  2, 3, 4, 20, 28, 41, 71, 95, 99, 103, 112

successes:
  no_memory 0/33
  generic 4/33
  oracle 3/33
  mismatch 3/33
```

Again, oracle does not beat generic in the clean stable-failure subset.

## Interpretation

Experiment 5.3 gives a real but narrow possibility signal.

Supported:

```text
1. Runtime memory injection is live in tau2 fresh task retries.
2. Official reward can change across card conditions.
3. Some task-specific oracle missing-check cards produce clear rescues.
4. Wrong/mismatched cards can be neutral or harmful, so the intervention is not a no-op.
```

Not supported:

```text
1. Oracle cards are generally better than generic policy memory.
2. Attribution-specific memory reliably improves fresh retry success.
3. The current hand-authored oracle cards are consistently high quality.
4. This is evidence for predicted attribution utility or closed-loop self-improvement.
```

The most accurate read:

```text
The tau2 fresh-retry setting is a better PoC vehicle than Who&When prefix repair,
but the current hand-authored oracle-card implementation is not strong enough
to establish attribution-specific utility at the 20-task scale.
```

## Likely Failure Modes

The results suggest three concrete issues:

```text
1. Oracle cards sometimes target the communication/NL side but not the DB/tool-action side.
2. Generic policy memory is a strong baseline for several tau2 retail tasks.
3. Some hard mismatches are not truly orthogonal and occasionally help.
```

The DB/NL split is especially important. Future cards need to make the required
tool-side action explicit without leaking the exact solution.

## Decision

This is an AMBIGUOUS result, not a GREEN result.

Recommended next step:

```text
Do not scale this exact card set blindly.
First perform a qualitative audit of:
  - oracle-positive cases: 16, 95
  - generic-beats-oracle cases: 36, 103
  - mismatch-beats-oracle cases: 19, 41, 104

Then revise the card-generation policy around DB/tool-action completion and
rerun a smaller targeted rescue check.
```

Claim boundary:

```text
This experiment supports continued investigation of failure-derived runtime
memory, but it does not yet support the thesis that precise attribution-derived
cards outperform generic memory in runnable task rescue.
```
