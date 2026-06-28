# Experiment 6C Results: Binding Forcing vs Content

Date: 2026-06-28

## Status

Completed.

Experiment 6C resumed after the OpenAI quota issue was resolved. The runner
skipped the previously completed cells and executed the remaining task 95 gated
conditions.

```text
expected runs: 144
completed runs: 144
resume behavior: 31 ran, 113 skipped
```

Artifacts:

```text
manifest:
  tau2_card_poc/experiments/exp6c_binding_forcing_vs_content.json

simulations:
  third_party/tau2-bench/data/simulations/exp6c_binding_forcing_vs_content/

summaries:
  reports/exp6c_binding_forcing_vs_content/
```

## Question

Experiment 6B showed that binding finalization checks can rescue some fresh tau2
retail executions. Experiment 6C asks what the active ingredient is:

```text
1. merely forcing one more turn
2. broad finalization checks
3. mode-level checks
4. precise attribution-derived checks
5. wrong but equally binding checks
```

This is still an oracle/upper-bound experiment. It does not test predicted
attribution, memory retrieval, multi-agent who localization, or closed-loop
self-improvement.

## Design

```text
3 tasks x 8 seeds x 6 conditions = 144 runs
```

Tasks:

```text
19, 36, 95
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

All binding conditions use the same finalization-boundary intervention
mechanism. The conditions vary only in the check/feedback content.

## Aggregate Result

```text
condition                         successes / attempts   success rate
precise_attribution_binding_gate  15 / 24                0.6250
mode_only_binding_gate            11 / 24                0.4583
coarse_binding_gate               10 / 24                0.4167
wrong_binding_gate                 6 / 24                0.2500
always_continue_once_control       4 / 24                0.1667
no_gate                            2 / 24                0.0833
```

Paired against `no_gate`:

```text
condition                         rescues   regressions   delta
precise_attribution_binding_gate  14        1             +0.5417
mode_only_binding_gate            11        2             +0.3750
coarse_binding_gate                8        0             +0.3333
wrong_binding_gate                 5        1             +0.1667
always_continue_once_control       4        2             +0.0833
```

Pairwise contrasts:

```text
precise - mode_only: +0.1667
precise - coarse:    +0.2083
precise - wrong:     +0.3750
precise - no_gate:   +0.5417
```

## Component Breakdown

```text
condition                         success   DB      NL_ASSERTION
no_gate                           0.0833    0.5417  0.4167
always_continue_once_control      0.1667    0.5833  0.4167
coarse_binding_gate               0.4167    0.6667  0.6250
mode_only_binding_gate            0.4583    0.6250  0.7083
precise_attribution_binding_gate  0.6250    0.7500  0.8333
wrong_binding_gate                0.2500    0.5833  0.4583
```

The precise gate did not merely increase user-facing NL assertions while
destroying DB state. In aggregate it had the highest DB mean and the highest
NL assertion mean. This is different from some earlier prose-memory runs where
the intervention mostly helped NL while hurting DB/tool completion.

## Task-Level Matrix

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
  coarse_binding_gate               2 / 8
  mode_only_binding_gate            6 / 8
  precise_attribution_binding_gate  7 / 8
  wrong_binding_gate                1 / 8
```

Task 95 is the strongest precision-positive case. It is also the task where
mode-level binding already performs very well, so the precise attribution gate
adds only a small margin over mode-only on that task.

Tasks 19 and 36 show that precise and coarse binding can tie:

```text
task 19: precise = coarse = 4 / 8
task 36: precise = coarse = 4 / 8
```

This matters for interpretation. The result is not a broad proof that fine
attribution content dominates coarse binding across tasks.

## Gate Behavior

```text
condition                         trigger rate   gate failures   final passes
always_continue_once_control      24 / 24        48              0
coarse_binding_gate               24 / 24        13              24
mode_only_binding_gate            24 / 24        23              21
precise_attribution_binding_gate  24 / 24        28              20
wrong_binding_gate                24 / 24        30              15
```

Every binding condition triggered in every run because the wrapper evaluates
the user-stop boundary. The useful distinction is not trigger rate but whether
the check failed, whether the agent retried, whether the final response passed
the check, and whether official reward improved.

The always-continue control was weak:

```text
always_continue_once_control: 4 / 24
```

This argues against the strongest version of the "just one more turn" account.
However, wrong binding still achieved 6 / 24, so some benefit can come from
being forced to continue even when the check content is not correct.

## Interpretation

Supported:

```text
1. Binding finalization checks are a real intervention lever.
2. Binding checks outperform advisory prose in this tau2 retail slice.
3. Precise attribution-derived binding can outperform no gate, always-continue,
   wrong binding, coarse binding, and mode-only binding in this selected
   3-task pilot.
4. The effect is strongest on task 95, a recoverable communication/check
   omission task.
```

Not supported:

```text
1. Precise attribution is generally better than coarse binding across tau2.
2. The result is robust across many failure families.
3. Predicted attribution can produce these checks.
4. Multi-agent who localization has downstream utility.
5. Runtime prose memory is sufficient.
```

The fairest summary:

```text
Exp6C is a limited positive result for precision under binding, not a broad
positive result for prose memory or for failure attribution in general.
```

Compared with the earlier tau2 prose-memory experiments, the active ingredient
appears to have moved:

```text
less promising:
  put a failure card in the system prompt and hope the agent follows it

more promising:
  convert the failure attribution into a binding post-condition check at the
  finalization boundary
```

## Report Use

For the report, Exp6C should be used as the closing experiment:

```text
Prose memory mostly failed to separate precise attribution from generic memory.
Binding checks revived the signal in a small selected slice.
Therefore the next research direction should not be "better cards" but
"failure attribution as verifier / intervention constraint generation."
```

This preserves the original research question while moving the interface:

```text
from: attribution -> advisory memory
to:   attribution -> enforceable check / intervention guard
```

