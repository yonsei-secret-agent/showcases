# Experiment 5.4 Determinism Probe Results

Date: 2026-06-28

## Goal

Before running Experiment 5.4, test whether same `(task_id, seed, no_memory)`
cells are stable enough to support strong paired interpretation.

This probe repeats three no-memory cells twice:

```text
tasks: 16, 36, 103
seed: 501
conditions: no_memory_probe_a, no_memory_probe_b
```

## Result

The probe found non-trivial same-seed instability.

```text
task 16: success 0 vs 0, but DB component 1.0 vs 0.0
task 36: success 0 vs 1
task 103: success 0 vs 0
```

Summary:

```text
success disagreement: 1 / 3 cells
component disagreement: at least 2 / 3 cells
```

Source artifacts:

```text
reports/exp5_4_determinism_probe/per_run_outcomes.csv
reports/exp5_4_determinism_probe/pairwise_condition_matrix.csv
```

## Interpretation

Same-seed pairing is useful but not deterministic in this tau2 setup. A single
success flip under identical task, seed, model, and no-memory condition means
Experiment 5.4 should not use a hard paired GREEN rule on only three seeds.

This does not invalidate the tau2 setup. It changes the analysis target:

```text
Do not claim deterministic same-seed rescue.
Estimate condition success rates and task-level patterns with more repetitions.
```

## Decision

Run Experiment 5.4 with five seeds instead of three:

```text
501, 502, 503, 504, 505
```

Use the original Exp5.3 seeds `501-503` for continuity checks, and use all five
seeds for primary condition-rate and per-task analysis.

GREEN must be interpreted conservatively:

```text
oracle_v2 must show task-level improvement on repair tasks,
not only aggregate lift or retention-task wins.
```

If the five-seed run is still split, the result should be YELLOW/AMBIGUOUS, not
treated as a negative result for the broader research direction.
