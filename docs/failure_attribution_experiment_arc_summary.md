# Failure Attribution Experiment Arc Summary

Date: 2026-06-28

## Executive Summary

이 문서는 Who&When PoC부터 tau2 binding experiment까지의 실험 흐름을
하나의 연구 arc로 정리한다.

North Star:

```text
Can precise failure attribution become a better self-improvement signal
than coarse reflection or generic in-context memory?
```

현재까지의 가장 정직한 결론:

```text
Precise attribution as prose memory/card is weak and often does not separate
from generic reminders.

Precise attribution becomes more promising when converted into an enforceable
finalization check / verifier / intervention constraint.
```

즉, 실험의 방향은 다음처럼 이동했다.

```text
failure attribution -> advisory memory
  weak / noisy / content-insensitive

failure attribution -> binding post-condition check
  limited positive signal in selected tau2 tasks
```

보고서에서의 핵심 문장:

```text
Failure attribution is more useful as a source of enforceable checks than as
plain prose advice.
```

## High-Level Timeline

| Stage | Benchmark | Main interface | What it tested | Main result |
| --- | --- | --- | --- | --- |
| Exp1-3 | Who&When | trace-prefix runtime card | Can gold attribution alter next-step behavior? | yes, but same-trace/judge-coupled and weak for thesis |
| Exp5.2-5.5 | tau2 retail | prose runtime memory | Can attribution-derived memory improve fresh task retry? | memory is live, but oracle prose does not beat generic reliably |
| Exp6A-6B | tau2 retail | binding finalization check | Is enforcement a better lever than prose? | yes, binding can rescue selected failures |
| Exp6C | tau2 retail | precise binding check | Does precision matter under enforcement? | limited positive: precise > mode/coarse/wrong/no gate in 3-task pilot |

## Experiment 1: Who&When Feasibility Smoke

### Question

```text
If a gold Who&When attribution is converted into a runtime card, does it reduce
same-failure recurrence at the gold decisive step?
```

### Setup

Benchmark:

```text
Who&When local clone
trace-prefix repair
gold intervention point
single next-action regeneration
```

Conditions:

```text
no_guidance
strong_generic_guideline
sanitized_raw_gold_explanation
oracle_runtime_card
wrong_mismatched_card
```

### Result

```text
condition                     repair success   recurrence
no_guidance                   0.1000           0.9000
strong_generic_guideline      0.2000           0.8000
sanitized_raw_gold            0.3000           0.6000
oracle_runtime_card           0.6000           0.2000
wrong_mismatched_card         0.8000           0.2000
```

### Interpretation

Supported:

```text
Runtime guidance can change same-trace next-action behavior.
Gold attribution-derived cards can improve over no guidance in this local
trace-prefix setting.
```

Not supported:

```text
Attribution-specific utility.
```

Reason:

```text
The wrong/mismatched card outperformed the oracle card.
The negative control collapsed.
```

Role in arc:

```text
Feasibility smoke. It proved the apparatus can move behavior, not that precise
attribution is the active ingredient.
```

## Experiment 2: Who&When Specificity Gate

### Question

```text
Does an oracle_specific_card beat coarse reflection, broad verification,
raw gold explanation, and hard mismatch?
```

### Main Fixes Over Exp1

```text
1. Removed shared "failed trajectory" prompt contamination.
2. Replaced mode-level oracle card with oracle_specific_card.
3. Replaced weak mismatch with hard_mismatched_card.
4. Added broad verification and coarse reflection baselines.
```

### Result

```text
condition                    repair success   recurrence
oracle_specific_card         0.6364           0.2727
broad_verification_card      0.2273           0.6364
hard_mismatched_card         0.2727           0.6818
```

Key contrasts:

```text
oracle_specific - broad_verification = +0.4091
oracle_specific - hard_mismatch      = +0.3637
```

### Interpretation

At first, this looked like a strong specificity signal.

But the later audit found a major validity risk:

```text
oracle_specific_card included compact gold mistake_reason.
diagnostic judge also saw the same gold diagnostic explanation.
card and judge shared the same gold diagnosis.
```

Supported:

```text
Better controls than Exp1.
Same-trace oracle_specific guidance can outperform broad/mismatch controls.
```

Not safely supported:

```text
The effect is cleanly attribution-specific.
```

Role in arc:

```text
Specificity smoke, but still vulnerable to literal gold diagnosis leakage and
judge-card coupling.
```

## Experiment 3: Who&When Abstraction and Judge Ablation

### Question

```text
If literal gold reason is removed, does the repair signal survive with only:
failure-mode pattern + missing-check type + abstract corrective action?
```

### Setup

Conditions:

```text
broad_verification_card
correct_mode_only_placebo
oracle_abstracted_card
hard_mismatched_abstracted_card
```

Two judge variants were used:

```text
1. abstract-criterion judge
   Uses abstract missing-check/corrective criterion.

2. failure-anchored judge
   Does not see condition label, card text, card-derived criterion, or gold
   explanation. It compares the candidate action against the original task,
   prefix, responsible agent, and original failed action.
```

### Result

Abstract-criterion judge:

```text
condition                    repair success   recurrence
broad_verification_card      0.2727           0.5455
mode_only_placebo            0.1364           0.6364
hard_mismatch_abstracted     0.4091           0.4091
oracle_abstracted_card       0.6364           0.0455
```

Failure-anchored judge:

```text
condition                    repair success   recurrence
broad_verification_card      0.5455           0.3636
mode_only_placebo            0.4545           0.4545
hard_mismatch_abstracted     0.4545           0.5000
oracle_abstracted_card       0.6364           0.2727
```

Judge gap:

```text
abstract-criterion judge:
  oracle - broad = +0.3637
  oracle - hard_mismatch = +0.2273

failure-anchored judge:
  oracle - broad = +0.0909
  oracle - hard_mismatch = +0.1819
```

### Interpretation

Supported:

```text
Some oracle-vs-mismatch signal survives abstraction.
```

But:

```text
The signal shrinks under the failure-anchored judge.
The same-trace setting still measures local action repair, not task success.
Repair_success was highly tied to whether the candidate produced a concrete
action.
```

Role in arc:

```text
Who&When remains useful as diagnostic PoC, but not enough for the main
self-improvement claim.
```

Decision:

```text
Move to a runnable benchmark with official task reward.
```

## Experiment 4: Cross-Trace Transfer

### Intended Question

```text
Can a source failure card transfer to a held-out target trace under oracle
retrieval of the same failure mode?
```

### Status

```text
Deferred.
```

Reason:

```text
After Exp3, the main bottleneck was no longer just transfer. The project needed
a runnable benchmark where retry success could be measured with official task
reward. tau2 was prioritized.
```

Role in arc:

```text
Still a valid future Who&When probe, but not the main evidence path.
```

## tau2 Setup Smoke

### Question

```text
Can tau2-bench retail run locally, produce official reward, and accept runtime
memory injection?
```

### Result

Setup verified:

```text
tau2 retail text-mode runs work.
results.json can be parsed.
RuntimeMemoryAgent can inject a <runtime_memory> block.
Same-task retry can be run through the local runner.
```

One-task / five-task probes showed:

```text
baseline failures are easy to harvest under gpt-4.1-mini.
some failures are DB/write failures.
some failures are user-facing NL/assertion failures.
```

Role in arc:

```text
tau2 is a better vehicle than Who&When for fresh execution rescue because it
has official reward and fresh environment retry.
```

## Experiment 5.2: tau2 Retail Baseline Harvest

### Question

```text
Does tau2 retail provide enough repeated failures for a rescue experiment?
```

### Setup

```text
30 candidate tasks
3 trials per task
90 total simulations
agent/user model: gpt-4.1-mini
```

### Result

```text
official success: 22 / 90 = 0.2444
DB match:         33 / 90 = 0.3667
```

Task stability:

```text
stable_failure: 15 tasks
mixed:          14 tasks
stable_success:  1 task
```

### Interpretation

Supported:

```text
tau2 retail has enough failures and diversity for a runnable rescue PoC.
```

Not tested:

```text
Cards, attribution specificity, predicted attribution, or transfer.
```

Role in arc:

```text
Built the task pool for fresh retry experiments.
```

## Experiment 5.3: tau2 20-Case Prose Memory Rescue

### Question

```text
In fresh tau2 retries, does a hand-authored oracle missing-check memory improve
official task success more than generic or mismatched memory?
```

### Setup

```text
20 selected tasks
4 conditions
3 seeds
240 runs
```

Conditions:

```text
no_memory
generic_policy_card
oracle_single_missing_check_card
hard_mismatched_card
```

### Result

```text
condition                         successes / attempts
generic_policy_card               16 / 60 = 0.2667
oracle_single_missing_check_card  15 / 60 = 0.2500
hard_mismatched_card              13 / 60 = 0.2167
no_memory                         12 / 60 = 0.2000
```

Paired against no memory:

```text
generic: 10 rescues, 6 regressions, +0.0667 delta
oracle:   9 rescues, 6 regressions, +0.0500 delta
mismatch: 9 rescues, 8 regressions, +0.0167 delta
```

Component means:

```text
condition                         DB       NL_ASSERTION
generic_policy_card               0.5167   0.5965
oracle_single_missing_check_card  0.4000   0.6842
hard_mismatched_card              0.4667   0.6667
no_memory                         0.4500   0.5965
```

### Interpretation

Supported:

```text
Runtime memory injection is live.
Oracle prose memory can rescue some failures.
```

Not supported:

```text
Oracle prose memory beats generic policy memory.
```

Important mechanism:

```text
Oracle prose helped NL/assertion more than DB/tool state.
It may steer the agent toward explaining the missing check without reliably
completing tool-side actions.
```

Role in arc:

```text
First runnable result. It weakened the prose-memory thesis.
```

## Experiment 5.4: Targeted Tool-Completion Card Revision

### Question

```text
Can a more explicit tool-completion oracle card fix the DB/tool weakness from
Exp5.3?
```

### Setup

```text
7 tasks
5 conditions
5 seeds
175 runs
```

Conditions included:

```text
no_memory
generic_policy_card_v2
oracle_single_missing_check_v1
oracle_tool_completion_card_v2
hard_mismatched_card_v2
```

### Result

```text
condition                         success
oracle_single_missing_check_v1    14 / 35 = 0.4000
generic_policy_card_v2             8 / 35 = 0.2286
no_memory                          7 / 35 = 0.2000
oracle_tool_completion_card_v2     6 / 35 = 0.1714
hard_mismatched_card_v2            5 / 35 = 0.1429
```

### Interpretation

Supported:

```text
The narrow v1 missing-check memory still has some signal.
```

Not supported:

```text
The broader v2 tool-completion ledger helps.
```

Decision:

```text
Do not scale oracle_tool_completion_card_v2.
```

Role in arc:

```text
The fix was not "make a longer prose card." Richer branch-ledger prose can
overconstrain or distract the agent.
```

## Experiment 5.5: Variability and Saturation Pre-Check

### Question

```text
Before running a full held-out prose-memory comparison, is the task pool
informative enough and stable enough?
```

### Setup

5.5A variability calibration:

```text
5 tasks x 1 seed x 3 no-memory repeats = 15 runs
```

5.5C saturation pre-check:

```text
6 held-out tasks x 4 conditions x 3 seeds = 72 runs
```

Conditions:

```text
no_memory
generic_policy_card
failure_mode_only_card
oracle_single_missing_check_card_v1
```

### Result

Same-seed instability exists:

```text
success flip cells: 1 / 5
DB flip cells:      1 / 5
NL flip cells:      2 / 5
```

Saturation pre-check:

```text
condition                         successes / attempts
generic_policy_card               6 / 18 = 0.3333
oracle_single_missing_check_v1    6 / 18 = 0.3333
failure_mode_only_card            5 / 18 = 0.2778
no_memory                         5 / 18 = 0.2778
```

### Interpretation

Supported:

```text
The current task pool and prose-card interface cannot show a clean
oracle-vs-generic specificity gradient.
```

Not supported:

```text
Precise prose memory beats generic reminders.
```

Decision:

```text
Do not run the full 6-condition Exp5.5F prose-memory experiment on this pool.
```

Role in arc:

```text
Stopped the prose-memory track before more sunk cost.
Motivated moving from advisory prose to enforced intervention.
```

## Experiment 6A/6B: Binding Check Pilot

### Question

```text
If prose memory is weak, can a binding finalization check move official tau2
reward?
```

### Interface Change

From:

```text
task starts -> memory in system prompt -> agent may follow or ignore it
```

To:

```text
agent attempts final response -> harness checks a post-condition -> if failed,
finalization is blocked once and feedback is injected
```

### 6A Timing Smoke

```text
no_gate:                0 / 2
mismatched_money_gate:  2 / 2
```

Interpretation:

```text
The intervention is live, but this is not substantive because the gate was
intentionally mismatched.
```

### 6B Recoverability Probe

```text
5 tasks x 2 seeds x 2 conditions = 20 runs
```

Result:

```text
coarse_binding_gate: 4 / 10 = 0.4000
no_gate:             1 / 10 = 0.1000
```

Paired:

```text
rescues:     4
regressions: 1
delta:      +0.3000
```

### Interpretation

Supported:

```text
Binding finalization checks can change fresh tau2 outcomes.
```

Not yet supported:

```text
Precise attribution-derived gates beat coarse or mode-only gates.
```

Role in arc:

```text
Established enforcement as a distinct intervention lever.
```

## Experiment 6C: Binding Forcing vs Content

### Question

```text
Under the same binding mechanism, what matters:
one more turn, coarse check, mode-level check, precise attribution check, or
wrong check?
```

### Setup

```text
3 tasks x 8 seeds x 6 conditions = 144 runs
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

### Result

```text
condition                         successes / attempts   success rate
precise_attribution_binding_gate  15 / 24                0.6250
mode_only_binding_gate            11 / 24                0.4583
coarse_binding_gate               10 / 24                0.4167
wrong_binding_gate                 6 / 24                0.2500
always_continue_once_control       4 / 24                0.1667
no_gate                            2 / 24                0.0833
```

Paired against no gate:

```text
condition                         rescues   regressions   delta
precise_attribution_binding_gate  14        1             +0.5417
mode_only_binding_gate            11        2             +0.3750
coarse_binding_gate                8        0             +0.3333
wrong_binding_gate                 5        1             +0.1667
always_continue_once_control       4        2             +0.0833
```

Component means:

```text
condition                         success   DB      NL_ASSERTION
no_gate                           0.0833    0.5417  0.4167
always_continue_once_control      0.1667    0.5833  0.4167
coarse_binding_gate               0.4167    0.6667  0.6250
mode_only_binding_gate            0.4583    0.6250  0.7083
precise_attribution_binding_gate  0.6250    0.7500  0.8333
wrong_binding_gate                0.2500    0.5833  0.4583
```

Task-level matrix:

```text
task 19:
  no_gate 2/8, coarse 4/8, mode_only 2/8, precise 4/8, wrong 3/8

task 36:
  no_gate 0/8, coarse 4/8, mode_only 3/8, precise 4/8, wrong 2/8

task 95:
  no_gate 0/8, coarse 2/8, mode_only 6/8, precise 7/8, wrong 1/8
```

### Interpretation

Supported:

```text
Binding checks are a strong intervention lever.
Precise attribution-derived binding checks outperform no gate, always-continue,
wrong binding, coarse binding, and mode-only binding in this selected 3-task
pilot.
```

Important limitation:

```text
The strongest precision-positive evidence comes from task 95.
Tasks 19 and 36 show precise = coarse.
Therefore this is a limited positive result, not a broad general proof.
```

Role in arc:

```text
This is the first experiment where precision becomes meaningfully positive
after the interface changes from prose advice to binding check.
```

## Cross-Experiment Synthesis

### What We Learned

1. **Attribution can be made actionable, but the interface matters.**

   Who&When showed that gold failure analysis can change next-step behavior.
   tau2 showed that plain memory is not enough for robust task rescue.

2. **Prose memory is a weak interface.**

   Across Exp5.3, Exp5.4, and Exp5.5, oracle prose cards failed to reliably
   beat generic policy memory. They often improved NL/assertion behavior more
   than DB/tool completion.

3. **Longer or richer cards are not necessarily better.**

   Exp5.4's tool-completion v2 card underperformed the simpler v1 card.

4. **Binding checks are a better interface.**

   Exp6 showed that finalization-boundary enforcement can rescue failures that
   prose memory did not reliably rescue.

5. **Precision can matter under binding, but evidence is still narrow.**

   Exp6C found precise > mode_only/coarse/wrong/no_gate in a selected 3-task
   pilot, especially task 95.

### What We Should Not Claim

Do not claim:

```text
1. predicted attribution works
2. multi-agent who localization improves task success
3. self-improving closed-loop agent is complete
4. reusable memory retrieval works
5. precise attribution generally beats generic memory across tau2
6. Who&When same-trace repair proves downstream task utility
```

### What We Can Claim

Safe report-level claim:

```text
Gold failure attribution can be converted into runtime interventions that
change agent behavior.
```

Stronger but still bounded claim:

```text
In tau2 retail fresh retries, precise attribution rendered as prose memory does
not reliably outperform generic reminders, but precise attribution rendered as
a binding finalization check shows a limited positive signal in selected
recoverable tasks.
```

Best framing:

```text
The value of failure attribution is not simply in writing better reflection
cards. Its more promising role is to generate verifiable post-conditions and
targeted intervention constraints.
```

## Recommended Report Narrative

### 1. Motivation

Existing failure attribution work often stops at:

```text
who failed, when, and why?
```

This project asks:

```text
Can that attribution improve the next execution?
```

### 2. PoC: Who&When

Use Who&When as the fast diagnostic setting:

```text
gold attribution -> runtime guidance -> local trace-prefix repair
```

Finding:

```text
The pipeline is feasible, but same-trace repair and judge coupling make it
insufficient as final evidence.
```

### 3. Runnable Testbed: tau2

Move to tau2 because:

```text
fresh task execution
official reward
DB/NL component breakdown
```

Finding:

```text
Prose memory is live but not reliably attribution-specific.
```

### 4. Interface Pivot

The key pivot:

```text
from advisory memory
to binding verifier/check
```

Finding:

```text
Binding checks revive the signal, and precise checks outperform coarse/mode/wrong
checks in a selected small pilot.
```

### 5. Future Work

Next research questions:

```text
1. Can predicted attribution generate the right binding checks?
2. Can checks be retrieved or routed automatically?
3. Does multi-agent who attribution improve targeted intervention?
4. Can this become a closed-loop self-improving agent?
```

## Final Takeaway

The project should not be summarized as:

```text
Failure cards work.
```

It should be summarized as:

```text
Failure attribution is weak as plain advice, but promising as a source of
enforceable checks.
```

This is the clearest research direction after the full experimental arc.

