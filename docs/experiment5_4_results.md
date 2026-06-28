# Experiment 5.4 Results: Targeted Tool-Completion Card Revision

Date: 2026-06-28

## Goal

Experiment 5.4 tested whether the weak DB/tool-side performance in Exp5.3 could
be improved by replacing the prior `oracle_single_missing_check_card_v1` with a
more explicit `oracle_tool_completion_card_v2`.

The central question was:

```text
Does an audit-anchored tool-completion card improve fresh tau2 retail task
success beyond generic runtime memory and the prior oracle single-check card?
```

## Setup

```text
domain: retail
agent model: gpt-4.1-mini
user model: gpt-4.1-mini
tasks: 16, 95, 36, 103, 19, 41, 104
seeds: 501, 502, 503, 504, 505
conditions: 5
total runs: 175
```

The run used fresh tau2 task execution, not prefix repair. Success is official
tau2 reward `1.0`.

Before the main run, a same-seed determinism probe found instability:

```text
success disagreement: 1 / 3 repeated no-memory cells
component disagreement: at least 2 / 3 repeated no-memory cells
```

Therefore this result should be read as condition-rate and task-level evidence,
not as deterministic same-seed rescue.

## Aggregate Result

```text
condition                         success
oracle_single_missing_check_v1     14 / 35 = 0.4000
generic_policy_card_v2              8 / 35 = 0.2286
no_memory                           7 / 35 = 0.2000
oracle_tool_completion_card_v2      6 / 35 = 0.1714
hard_mismatched_card_v2             5 / 35 = 0.1429
```

Component means:

```text
condition                         DB       NL_ASSERTION
no_memory                         0.5714   0.4000
generic_policy_card_v2            0.5714   0.4857
oracle_single_missing_check_v1    0.5143   0.6571
oracle_tool_completion_card_v2    0.4857   0.5143
hard_mismatched_card_v2           0.5143   0.4857
```

## Task Matrix

```text
task  no_memory  generic_v2  oracle_v1  oracle_v2  mismatch_v2
16    1/5        1/5         3/5        1/5        0/5
19    3/5        1/5         0/5        1/5        2/5
36    1/5        2/5         1/5        1/5        0/5
41    1/5        1/5         2/5        0/5        2/5
95    0/5        1/5         5/5        3/5        1/5
103   1/5        0/5         1/5        0/5        0/5
104   0/5        2/5         2/5        0/5        0/5
```

## Decision

Exp5.4 is **RED for the v2 tool-completion card**.

It fails the pre-registered direction in three ways:

```text
1. oracle_v2 < oracle_v1 overall.
2. oracle_v2 < generic_v2 overall.
3. oracle_v2 does not produce repair-set wins over generic_v2.
```

`oracle_v2` strictly beats `generic_v2` only on task `95`, a retention task
where oracle memory already worked in Exp5.3. It does not fix the repair set.

The result is **not a RED for the overall research direction**. The prior
single-check oracle card is the best condition in this run:

```text
oracle_v1 - no_memory  = +7 successes / 35
oracle_v1 - generic_v2 = +6 successes / 35
oracle_v1 - oracle_v2  = +8 successes / 35
```

So the more conservative reading is:

```text
Precise missing-check memory can move official tau2 reward in a useful
direction, but broad branch-ledger completion cards overcorrect and may degrade
the agent.
```

## Interpretation

Exp5.3 suggested that oracle cards helped NL assertions more than DB/tool-side
completion. Exp5.4 tested a natural repair: make the oracle card more explicit
about tool-side branch completion.

That repair did not work. The v2 card appears to have added too much process
structure or shifted attention away from the decisive missing check.

The surprising useful signal is that the simpler v1 card became clearly better
than both no-memory and generic memory under five seeds. This suggests the
active ingredient may be a narrow failure-derived check, not a full branch
ledger.

## What This Supports

Supported:

```text
1. Runtime memory injection in tau2 fresh execution is live.
2. Official reward changes by memory condition.
3. The hand-authored oracle single-missing-check upper bound remains promising.
4. The proposed tool-completion ledger v2 should not be scaled.
```

Not supported:

```text
1. Tool-completion ledger cards are better than single-check oracle cards.
2. Oracle v2 beats generic memory.
3. Current results prove predicted attribution utility.
4. Current results prove multi-agent who/when utility.
```

## Next Step

Do not scale `oracle_tool_completion_card_v2`.

The next experiment should preserve the narrow v1 missing-check content and add
only minimal action binding, rather than a broad branch ledger. It should also
include the missing North Star baselines:

```text
coarse_reflection_memory
raw_failure_explanation_memory
```

A reasonable next targeted design is:

```text
no_memory
generic_policy_card_v2
coarse_reflection_memory
raw_failure_explanation_memory
oracle_single_missing_check_card_v1
oracle_minimal_action_binding_card
hard_mismatched_card
```

The hypothesis should be narrower:

```text
Does a precise missing-check attribution, rendered as a short action-binding
memory, outperform coarse reflection and generic policy memory?
```

This keeps the promising v1 signal while directly testing whether the value is
really attribution-specific rather than generic runtime prompting.
