# Experiment 6C Partial Results: Binding Forcing vs Content

Date: 2026-06-28

Superseded by:

```text
docs/experiment6c_results.md
```

## Status

Experiment 6C started but did not complete.

The run stopped on an OpenAI `429 insufficient_quota` error while executing
task 95. This is not an experiment logic failure. Completed cells are saved and
the manifest runner can resume from the remaining cells once the active OpenAI
project/key quota is fixed.

Current artifacts:

```text
manifest:
  tau2_card_poc/experiments/exp6c_binding_forcing_vs_content.json

partial simulations:
  third_party/tau2-bench/data/simulations/exp6c_binding_forcing_vs_content/

partial summaries:
  reports/exp6c_binding_forcing_vs_content_partial/
```

Completion state:

```text
expected runs: 144
completed runs: 113
missing runs: 31
```

All missing runs are task 95 gated conditions:

```text
task 95:
  mode_only_binding_gate: seeds 901-908
  precise_attribution_binding_gate: seeds 901-908
  wrong_binding_gate: seeds 901-908
  coarse_binding_gate: seeds 902-908
```

The task 95 `no_gate` and `always_continue_once_control` arms completed.

## What 6C Tests

6C is not another prose-card experiment. It tests whether the active ingredient
in Exp6 is:

```text
1. binding / forced continuation itself
2. broad task-level finalization checks
3. mode-level checks
4. precise attribution-derived checks
5. wrong but equally binding checks
```

Conditions:

```text
no_gate
always_continue_once_control
coarse_binding_gate
mode_only_binding_gate
precise_attribution_binding_gate
wrong_binding_gate
```

Tasks:

```text
19, 36, 95
```

Seeds:

```text
901, 902, 903, 904, 905, 906, 907, 908
```

## Partial Aggregate

Do not over-read this table because task 95 is incomplete.

```text
condition                           successes / attempts   success rate
no_gate                              2 / 24                0.0833
always_continue_once_control         4 / 24                0.1667
coarse_binding_gate                  8 / 17                0.4706
mode_only_binding_gate               5 / 16                0.3125
precise_attribution_binding_gate     8 / 16                0.5000
wrong_binding_gate                   5 / 16                0.3125
```

Gate summary:

```text
condition                         trigger rate   total failures   final passes
always_continue_once_control      24 / 24        48               0
coarse_binding_gate               17 / 17        12               17
mode_only_binding_gate            16 / 16        17               13
precise_attribution_binding_gate  16 / 16        20               12
wrong_binding_gate                16 / 16        22               8
```

## Task-Level Partial Matrix

```text
task 19:
  no_gate                           2 / 8
  always_continue_once_control      2 / 8
  coarse_binding_gate               4 / 8
  mode_only_binding_gate            2 / 8
  precise_attribution_binding_gate  4 / 8
  wrong_binding_gate                3 / 8

task 36:
  no_gate                           0 / 8
  always_continue_once_control      2 / 8
  coarse_binding_gate               4 / 8
  mode_only_binding_gate            3 / 8
  precise_attribution_binding_gate  4 / 8
  wrong_binding_gate                2 / 8

task 95:
  no_gate                           0 / 8
  always_continue_once_control      0 / 8
  coarse_binding_gate               0 / 1
  mode_only_binding_gate            0 / 0
  precise_attribution_binding_gate  0 / 0
  wrong_binding_gate                0 / 0
```

## Current Read

This is not yet a final result.

The completed task 19 and task 36 cells suggest that binding checks can move
official tau2 reward, but they do not yet show that precise attribution content
is the active ingredient:

```text
task 19:
  precise = coarse = 4 / 8
  wrong is also non-trivial at 3 / 8

task 36:
  precise = coarse = 4 / 8
  mode_only = 3 / 8
  wrong and always_continue = 2 / 8
```

This leans toward:

```text
binding / forced continuation is live
precise content is not yet cleanly separated from coarse binding
wrong gates can still rescue some runs, so specificity is not established
```

However, task 95 is the strongest prior anchor for recoverable
communication/check omission. Because task 95 gated conditions are mostly
missing, no final Exp6C conclusion should be reported yet.

## Resume Command

After the active OpenAI key/project quota is fixed, resume without `--no-resume`:

```bash
PYTHONPATH=/home/depa/showcases/tau2_card_poc/src:/home/depa/showcases/third_party/tau2-bench/src \
uv run --project third_party/tau2-bench \
python -m tau2_card_poc.cli run-binding-manifest \
  tau2_card_poc/experiments/exp6c_binding_forcing_vs_content.json \
  --output-root third_party/tau2-bench/data/simulations
```

Then refresh summaries:

```bash
PYTHONPATH=/home/depa/showcases/tau2_card_poc/src:/home/depa/showcases/third_party/tau2-bench/src \
uv run --project third_party/tau2-bench \
python -m tau2_card_poc.cli summarize \
  third_party/tau2-bench/data/simulations/exp6c_binding_forcing_vs_content \
  --out-dir reports/exp6c_binding_forcing_vs_content \
  --baseline-condition no_gate
```

## Decision Boundary

If the completed Exp6C pattern remains:

```text
precise ~= coarse
wrong or always_continue remains competitive
```

then the report should state that binding intervention is useful, but
attribution precision is not the active ingredient in this tau2 single-agent
setting.

If task 95 changes the pattern such that:

```text
precise > coarse, mode_only, wrong, always_continue
```

and the advantage is not only due to trigger/retry frequency, then Exp6C can be
reported as limited positive evidence that precision matters when attribution is
converted into a binding finalization check.
