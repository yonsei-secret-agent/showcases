# Experiment 6 Results: Binding Check Pilot

Date: 2026-06-28

## Status

Experiment 6A and 6B completed.

Do not read this as a powered final test of precise attribution. It is a
mechanism pilot for a new intervention form:

```text
prose advice in the prompt
-> binding check at the finalization boundary
```

The useful result is that binding checks can move official tau2 reward in cases
where prose memory was weak. The limiting result is that coarse binding can also
break DB/tool completion or pass the wrong answer when the check is too shallow.

## What Was Run

### 6A Timing Smoke

Manifest:

```text
tau2_card_poc/experiments/exp6a_binding_smoke_user_stop.json
```

Design:

```text
1 task x 2 seeds x 2 conditions = 4 runs
```

Conditions:

```text
no_gate
mismatched_money_gate
```

The original agent-side gate was abandoned because it fired on non-final
assistant messages. The implemented production path now gates at the
user-stop boundary: when the user simulator would stop after an assistant
message, the binding wrapper evaluates the assistant response and can replace
the stop with feedback.

6A result:

```text
condition                success  gate trigger
no_gate                  0 / 2    0 / 2
mismatched_money_gate    2 / 2    2 / 2 runs
```

This result is not a substantive claim because the gate was intentionally
mismatched. It only proves the intervention is live and can change fresh tau2
execution.

### 6B No-Gate Pool Harvest

Manifest:

```text
tau2_card_poc/experiments/exp6b_binding_pool_harvest_no_gate.json
```

Design:

```text
24 candidate retail tasks
x 2 seeds
x no_gate
= 48 runs
```

Aggregate:

```text
no_gate success: 26 / 48 = 0.5417
```

This pool was too mixed for a main experiment. It contained saturated tasks,
stable dead tasks, evaluator-warning tasks, and only a few DB=1/NL=0 or
near-communication-omission candidates.

Candidate categories:

```text
cleanest DB=1/NL=0 candidate:
  19

mixed but potentially recoverable:
  36, 95, 103, 104

saturated / already solved in no_gate:
  24, 29, 38, 40, 44, 46, 47, 54, 67, 68, 89

stable failure with DB/tool failure dominant:
  16, 28, 59, 63

mixed but not clean communication-only:
  21, 30, 43

evaluator-warning / policy-conflict flagged:
  37, 38, 46, 47, 54, 67, 68
```

The harvest confirmed a recurring issue from Exp5.5: clean tau2 retail tasks
where the DB/tool side is complete but only the final user-facing assertion is
missing are relatively thin.

### 6B Recoverability Probe

Manifest:

```text
tau2_card_poc/experiments/exp6b_binding_recoverability_probe.json
```

Design:

```text
5 selected tasks
x 2 seeds
x 2 conditions
= 20 runs
```

Tasks:

```text
19, 36, 95, 103, 104
```

Conditions:

```text
no_gate
coarse_binding_gate
```

The coarse binding gates used non-answer presence checks only:

```text
19: include refund amount and combined total savings wording
36: explicitly identify most expensive item and item price
95: include each laptop exchange price difference and the total amount
103/104: include a numeric tracking number
```

No gate included exact answer values, exact order IDs, exact tool arguments, or
reward rubric text.

## 6B Recoverability Aggregate

```text
condition              successes / attempts   success rate
coarse_binding_gate    4 / 10                 0.4000
no_gate                1 / 10                 0.1000
```

Paired summary:

```text
baseline successes:      1 / 10
binding successes:       4 / 10
paired rescues:          4
paired regressions:      1
success delta:          +0.3000
rescue among failures:   4 / 9
regression among wins:   1 / 1
```

Gate summary:

```text
runs with gate trigger: 10 / 10
total gate triggers:    16
total gate failures:     7
total gate retries:      6
final gate passes:       9
```

## Task Matrix

```text
task  no_gate  coarse_binding_gate  interpretation
19    0/2      1/2                  NL rescued, but DB regression in one seed
36    0/2      1/2                  one rescue; DB failure remains in one seed
95    0/2      2/2                  cleanest binding rescue
103   0/2      0/2                  tracking/source-selection failure remains
104   1/2      0/2                  regression; tracking/source ambiguity remains
```

Component means:

```text
task  condition             DB mean  NL mean
19    no_gate               1.00     0.00
19    coarse_binding_gate   0.50     1.00

36    no_gate               0.00     1.00
36    coarse_binding_gate   0.50     1.00

95    no_gate               0.50     0.00
95    coarse_binding_gate   1.00     1.00

103   no_gate               0.00     0.50
103   coarse_binding_gate   0.00     0.00

104   no_gate               0.50     0.50
104   coarse_binding_gate   0.50     0.00
```

## Interpretation

Experiment 6 changes the story relative to Exp5.

Exp5 mostly showed:

```text
Precise prose memory is not a reliable active ingredient.
```

Exp6 shows:

```text
Binding checks at finalization can be an active ingredient.
```

The strongest positive example is task 95:

```text
no_gate:              0 / 2
coarse_binding_gate:  2 / 2
```

The gate forced the assistant to include each laptop exchange price difference
and the total amount due today. This converted the missing user-facing
breakdown into official reward success in both seeds.

But the result is not a clean endorsement of coarse binding as-is.

Task 19 shows the main risk:

```text
no_gate DB mean:             1.00
coarse_binding_gate DB mean: 0.50
no_gate NL mean:             0.00
coarse_binding_gate NL mean: 1.00
```

The gate improved the final communication but induced or exposed DB/tool-side
regression in one seed. This is the binding analogue of the Exp5 pattern:

```text
NL goes up, but DB/tool completion can go down.
```

Tasks 103 and 104 show a different limitation. A presence-only tracking gate can
ensure that some numeric tracking number appears, but it cannot ensure the
agent selected the correct order/source. These tasks should not be treated as
clean communication-only recoverability candidates.

## Decision

Experiment 6 is **GREEN for the intervention mechanism**:

```text
Binding finalization checks can change fresh tau2 outcomes and can rescue some
failures that prose memory did not reliably rescue.
```

Experiment 6 is **not GREEN for attribution precision yet**:

```text
The current probe compared no_gate against coarse task-specific binding gates.
It did not compare precise attribution-derived gates against coarse/mode-only
gates under format-matched enforcement.
```

The next and final pre-report experiment should therefore be:

```text
Exp6C: Precision Under Binding

Compare:
  no_gate
  coarse_binding_gate
  mode_only_binding_gate
  precise_attribution_binding_gate
  wrong_binding_gate

On:
  the small subset where binding is actually recoverable:
    primary: task 95
    secondary: tasks 19 and 36, with DB-regression watch
    exclude or separate: 103/104 tracking-source tasks
```

## Claim Boundary

Supported:

```text
1. The tau2 binding intervention is live at the user-stop boundary.
2. Binding checks can raise official tau2 reward in selected fresh-retry cases.
3. Prose memory failure does not imply intervention failure; enforcement is a
   distinct lever.
4. Binding checks must be audited for DB regression and source-selection
   ambiguity.
```

Not supported:

```text
1. Precise attribution-derived gates outperform coarse gates.
2. Runtime prose cards are sufficient.
3. Predicted attribution works.
4. Multi-agent who-targeting utility is tested.
5. Tracking/source-selection tasks are solved by presence-only gates.
```

## Report Implication

The report should not end with “cards failed.” A more accurate arc is:

```text
1. Prose memory is weak and often content-insensitive.
2. The active lever appears to be binding intervention at the finalization
   boundary.
3. Precision should now be tested as verifier/gate generation, not as prose
   advice.
4. tau2 is still single-agent, so MAS who-targeting remains an open next arc.
```

