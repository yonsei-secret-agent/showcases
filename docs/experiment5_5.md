# Experiment 5.5 Plan: Narrow Missing-Check Memory Final Gate

## Status

Planned. Do not run until this plan has been reviewed.

## Role In The Report

Exp5.5 is the final planned test of the **runtime prose-memory card** hypothesis.

The report should not depend on Exp5.5 producing a GREEN result. The report's
core deliverable is a clean answer to this question:

```text
When failure attribution is converted into prose runtime memory, is precise
attribution content the active ingredient, or are generic/coarse reminders
enough?
```

Therefore Exp5.5 is not another card-tuning iteration. It is the last gate
before either:

```text
1. continuing to predicted attribution, if precise missing-check memory clearly
   beats coarse/generic/mode-only baselines, or
2. pivoting to routing/retrieval/intervention selection, if prose content does
   not separate from coarse baselines.
```

Do not run a `card_v3` experiment after Exp5.5 unless the report outline shows
that a specific unresolved claim cannot be answered any other way.

## Why This Experiment Exists

Experiment 5.4 gave two useful signals:

```text
oracle_single_missing_check_card_v1    14 / 35 = 0.4000
generic_policy_card_v2                  8 / 35 = 0.2286
no_memory                               7 / 35 = 0.2000
oracle_tool_completion_card_v2          6 / 35 = 0.1714
hard_mismatched_card_v2                 5 / 35 = 0.1429
```

The result was RED for the broad `oracle_tool_completion_card_v2`. Longer
branch-ledger cards appear to overconstrain or distract the agent.

The strongest remaining signal is narrower:

```text
Short, precise missing-check memory may help when the failure is a missing
required user-facing assertion, calculation, count, tracking number, or price
difference.
```

However, the v1 win in Exp5.4 was partly driven by retention tasks `16` and
`95`, where oracle memory was already known to work. Exp5.5 must test whether
that signal generalizes to held-out tasks and beats the correct baselines.

## Central Question

```text
Does precise failure-attribution-derived missing-check memory outperform
generic policy memory, coarse reflection, and failure-mode-only memory on fresh
tau2 retail execution?
```

This is the first tau2 experiment that directly tests the North Star comparison:

```text
precise attribution memory
vs
coarse reflection / generic memory / failure-mode routing
```

## Claim Boundary

Exp5.5 can support:

```text
In a tau2 retail missing-communication/check stratum, oracle
attribution-derived missing-check memory improves fresh task success over
coarse and generic memory baselines.
```

Exp5.5 cannot support:

```text
1. predicted attribution utility
2. multi-agent who/when utility
3. general tau2 retail improvement across all failure modes
4. closed-loop self-improvement
5. end-to-end deployment claims
```

Those require later phases.

Important null interpretation:

```text
This missing-communication family is the place where generic reminders are
strongest. If generic or mode-only memory matches oracle, that does not prove
precise attribution is useless everywhere. It means this family may be
remindable by coarse memory, and the project should pivot toward routing or
retrieval rather than richer prose cards.
```

Single-agent caveat:

```text
tau2 tests whether why/when-style task-failure information can improve fresh
retry success. It does not test the multi-agent "who" dimension. Any report must
state that this track is a runnable single-agent rescue probe, not a full MAS
who/when attribution utility result.
```

Report-facing framing:

```text
If Exp5.5 is YELLOW or RED, the finding is not "the project failed." The finding
is that prose memory content is probably not the best interface for precise
failure attribution in this setting. The next bet becomes using attribution to
select the right memory, check, intervention point, or credit target.
```

## Phase 5.5A: Variability Calibration

### Motivation

Exp5.4 found same-seed instability:

```text
success disagreement: 1 / 3 repeated no-memory cells
component disagreement: at least 2 / 3 repeated no-memory cells
```

Therefore Exp5.5 must first estimate how much tau2 varies under repeated
identical runs.

### Design

Run repeated no-memory cells before the main experiment:

```text
5-10 selected (task_id, seed, no_memory) cells
x 3 repeats each
= 15-30 runs
```

Use tasks that cover:

```text
1. a known retention-like communication task
2. a held-out missing-assertion candidate
3. a mixed/winnable task
4. a likely stable-failure task
```

### What To Measure

```text
success flip rate
DB component flip rate
NL_ASSERTION component flip rate
mean reward variance
trace-level qualitative source of variation
```

### Decision

If same-seed instability is low:

```text
use paired seed analysis as secondary support
```

If same-seed instability is non-trivial:

```text
do not make deterministic paired-rescue claims
use condition rates, per-task rates, and bootstrap/CI-style uncertainty
estimate the needed seed count before scaling
```

This phase does not decide the research direction. It decides how to interpret
the main experiment.

### Report Reliability Gate

The report must explicitly account for tau2 variability.

If calibration finds substantial same-seed flips:

```text
1. do not present paired seed deltas as deterministic rescue
2. report task-level matrices and uncertainty
3. phrase results as condition-rate evidence
4. include the calibration result before any headline table
```

The credibility of the report is capped by how honestly this variability is
handled.

### Power / Scale Check

After calibration, estimate whether the intended main run can detect the
primary contrast:

```text
oracle_single_missing_check_card_v1 - failure_mode_only_card
```

Use the observed success/component flip rate to set a practical uncertainty
band. Then estimate how many seeds are needed to detect a plausible effect size:

```text
target effect: +0.15 to +0.20 success-rate gap on held-out tasks
primary contrast: oracle_v1 vs failure_mode_only
secondary contrast: oracle_v1 vs coarse_reflection
```

This target margin is binding. Later decision rules must not treat a tiny
positive difference as a win. In this document, `beats` means:

```text
condition A - condition B >= the pre-registered practical margin
and the calibrated uncertainty band or CI excludes zero
```

If interval estimation is not implemented, replace it with an explicit
task-level rule before running, for example:

```text
A has at least K more strict held-out task wins than B,
with K chosen from the calibration result and not after seeing outcomes.
```

If the estimated seed requirement is far above budget:

```text
do not call Exp5.5 a decision run
run only a descriptive saturation/pre-check pass
or pivot without spending on a large ambiguous run
```

Do not treat `5 seeds` or `6-7 seeds` as automatically sufficient. The seed
count must be justified by the calibration result.

## Phase 5.5B: Task Pool Construction

### Target Failure Family

Exp5.5 is not a general retail rescue experiment. It targets one failure family:

```text
The agent completes or nearly completes the DB/tool side, but misses a required
user-facing check, calculation, amount, count, tracking number, price
difference, or explicit communication.
```

Examples:

```text
refund total omitted
per-item price difference omitted
total amount due omitted
available product count omitted or misstated
tracking number omitted
required status/amount communication omitted after tool actions
```

### Inclusion Criteria

Use MUST/SHOULD criteria. Do not include a task that fails a MUST criterion.

MUST:

```text
1. prior no-memory or baseline run shows DB=1, NL_ASSERTION=0 or equivalent
2. the failure is not primarily exact variant/tool-argument selection
3. the task is not all-condition unwinnable under current model
4. the oracle card can be written inside the valid information band:
   more specific than task text + mode-only memory,
   but less specific than exact answer/tool arguments
```

SHOULD:

```text
1. required communication/check is explicit in the task
2. missing check can be described without leaking exact answer/tool args
3. the card can be written as a short missing-check memory
4. the target failure is not recoverable by a generic final-response reminder
```

### Exclusion Criteria

Exclude:

```text
1. exact tool-argument dominated failures
2. policy/evaluator conflict cases
3. full branch-planning failures where DB actions are mostly missing
4. tasks only recoverable by giving the exact answer
5. tasks where the required communication is ambiguous
```

### Retention Anchors

Use tasks `16` and `95` only as anchors:

```text
They verify that the known positive family still behaves as expected.
They must not drive the headline claim.
```

Headline results must be reported with anchors excluded:

```text
held-out missing-check tasks only
```

### Recommended Size

Preferred:

```text
8-10 held-out missing-check tasks
+ optional anchors 16, 95
```

Minimum useful run:

```text
6 held-out missing-check tasks
+ anchors 16, 95
```

If fewer than 6 held-out tasks can be identified, do not run Exp5.5 yet. First
harvest more candidates.

## Phase 5.5C: Specificity Feasibility and Saturation Pre-Check

Before the full condition set, check whether the experiment can actually
separate precise attribution from generic reminders.

### Specificity Feasibility Audit

This is the lower-bound half of the information-band audit. The oracle card
must not merely restate what a strong mode-only card plus the task already
implies.

For each candidate task, compare:

```text
task text + failure_mode_only_card
vs
task text + oracle_single_missing_check_card_v1
```

Use an operational blind check:

```text
Give a reviewer or separate LLM only the task text and failure_mode_only_card.
Ask it to write the missing-check memory.

Then compare that memory with oracle_v1.
```

If task text + mode-only is enough to recover the same actionable memory:

```text
the precise-vs-mode comparison is null by construction
drop that task from the decision pool or reframe it as mode-routing evidence
```

If this happens for most held-out tasks, do not run the full Exp5.5 decision
experiment. Reframe as failure-mode routing / retrieval.

This audit should happen before model calls. It prevents spending on a contrast
that the cards cannot express under the leakage constraints. Some tasks have an
empty valid information band: for example, if "include the tracking number" is
already fully specified by the mode-only memory and the only more specific
information is the exact tracking number, there is no non-leaky oracle card to
test.

### Saturation Pre-Check

Run a small pre-check on held-out candidates:

```text
conditions:
  no_memory
  generic_policy_card
  failure_mode_only_card
  oracle_single_missing_check_card_v1

scale:
  4-6 held-out candidate tasks
  x 4 conditions
  x calibrated seed count, or 3 seeds if only doing a cheap descriptive pass
```

Use seeds that are a subset of the planned full-run seeds. If the pre-check
passes and the full run proceeds, fold these completed runs into the final
analysis instead of discarding them.

Decision:

```text
If generic_policy_card or failure_mode_only_card already captures nearly all
recoverable cases, GREEN is structurally unlikely. Stop the full required-
condition run and pivot toward routing/retrieval.

If there is a visible specificity gradient
  no_memory < generic <= mode_only < oracle_v1
then run the full experiment.
```

The pre-check is not the final result. It is a stop/go filter for whether the
larger run can answer the intended question.

If the pre-check saturates:

```text
do not tune another prose card
write the report around saturation and pivot to a routing/retrieval mini-probe
```

## Phase 5.5D: Conditions

Use six required conditions.

```text
1. no_memory
2. generic_policy_card
3. coarse_reflection_memory
4. failure_mode_only_card
5. oracle_single_missing_check_card_v1
6. strict_hard_mismatched_card
```

Optional diagnostic condition:

```text
sanitized_raw_failure_note
```

Do not include the optional raw note in GREEN/RED decision rules unless it is
clearly distinguishable from oracle and mode-only memory after audit.

### Format Constraint

All memory conditions must be short and format-matched.

Use this schema:

```text
Memory:
  <one-sentence failure risk>

Action:
  <one-sentence action/check to perform before final response>

Do not:
  <one-sentence anti-pattern>
```

Rules:

```text
1. no long branch ledger
2. no full task decomposition
3. no exact order/item/payment IDs
4. no exact answer values
5. no original failed action quote
6. approximate length matching across memory conditions
```

### Condition Definitions

#### 1. no_memory

No runtime memory.

#### 2. generic_policy_card

Broad reliability memory that applies across retail tasks.

Example:

```text
Memory:
  Retail tasks can fail when the final response omits a required result.

Action:
  Before final response, verify that every requested result has been
  communicated.

Do not:
  Do not stop after completing tools if the user also requested an amount,
  count, status, or explanation.
```

#### 3. coarse_reflection_memory

Failure-aware but no who/when/why detail.

Use a strong, fair version of reflection. The goal is not to strawman
reflection, but to test whether precise attribution adds value beyond a
credible coarse self-reflection memory.

Example:

```text
Memory:
  A previous attempt on a similar task failed.

Action:
  Reflect briefly on what required result might be missing before finalizing.

Do not:
  Do not assume the task is complete just because some tool action succeeded.
```

#### 4. failure_mode_only_card

Correct broad mode, no task-specific missing check.

Example:

```text
Memory:
  This is a missing-required-communication risk.

Action:
  Check whether the final response should include a required amount, count,
  tracking number, or comparison.

Do not:
  Do not finalize without a required user-facing result.
```

Purpose:

```text
separates precise attribution content from failure-mode routing
```

#### 5. oracle_single_missing_check_card_v1

The current best-performing oracle condition.

It should name the specific missing check type, but not the exact answer.

Example:

```text
Memory:
  This task can fail if the completed return/exchange actions are not converted
  into the requested total amount.

Action:
  Before final response, compute and communicate the requested total from the
  completed tool actions.

Do not:
  Do not provide only a generic confirmation when the user asked for a total.
```

#### 6. strict_hard_mismatched_card

Same schema and length as oracle, but orthogonal to the target failure.

Requirements:

```text
1. must not mention the target missing check
2. must not be a broadly useful communication checklist
3. must be plausible retail memory but irrelevant to this task
4. must be audited before use
```

#### Optional: sanitized_raw_failure_note

This is a diagnostic-only condition.

It is not forced into the `Memory / Action / Do not` schema, because doing so
would make it no longer raw. If included, keep it short and length-bounded:

```text
Prior failure note:
  <sanitized natural-language failure explanation>
```

Use it only to inspect whether raw explanations behave similarly to oracle
cards. Do not use it as a primary GREEN gate unless the audit shows it is
meaningfully distinct from both oracle and mode-only memory.

## Phase 5.5E: Information-Band and Leakage Audit

Before running:

```text
audit every oracle card, mode-only card, mismatch card, and optional raw note
```

The valid oracle card must live inside an information band:

```text
lower bound:
  more actionable than task text + failure_mode_only_card

upper bound:
  less informative than the exact answer, exact tool arguments, IDs, or a direct
  solution trace
```

Reject cards that fall below the lower bound, because they do not test precise
attribution. Reject cards that exceed the upper bound, because they leak the
solution.

Block cards that include:

```text
exact answer values
order IDs
item IDs
payment IDs
tracking numbers
exact tool arguments
original failed action quotes
future success/failure labels
```

Also perform a blind recoverability check:

```text
Given only the card and the task text, can a reviewer infer the exact answer or
tool arguments?
```

If yes:

```text
rewrite or drop the card
```

Also perform the lower-bound blind check from Phase 5.5C. If a reviewer can
produce an equivalent card from task text + mode-only memory, drop the task from
the decision pool or classify it as mode-routing evidence, not precise
attribution evidence.

## Phase 5.5F: Scale

Preferred run:

```text
10 held-out tasks x 6 required conditions x calibrated seed count
+ optional anchors 16, 95
+ optional sanitized_raw_failure_note diagnostic
```

Smaller acceptable run:

```text
8 held-out tasks x 6 required conditions x calibrated seed count
+ optional anchors 16, 95
```

If variability calibration is high:

```text
do not blindly increase to 6-7 seeds
first estimate whether the target contrast can be detected within budget
```

If the required seed count is too high, run only the saturation pre-check and
label the result descriptive. Do not over-read an underpowered main run.

## Primary Metrics

Report separately for:

```text
1. held-out tasks only
2. anchor tasks 16/95 only
3. combined set
```

Primary:

```text
official_success_rate
primary attribution contrast:
  oracle_v1 - failure_mode_only

secondary north-star contrast:
  oracle_v1 - coarse_reflection

confirmatory guards:
  oracle_v1 - generic_policy
  oracle_v1 - strict_mismatch
```

Mechanism:

```text
DB_mean
NL_ASSERTION_mean
DB_retention_rate
DB_regression_rate
NL_rescue_rate among DB-passing failures
DB_pass_NL_fail count
DB_fail_NL_pass count
```

Task-level:

```text
task x condition success matrix
strict task wins/losses
anchor-excluded strict wins
negative transfer cases
anchor reproduction check for 16/95
```

Uncertainty:

```text
bootstrap or permutation-style intervals if implementation is available
otherwise report raw task-level counts and avoid statistical overclaim
```

## Decision Rules

### GREEN

Proceed to predicted attribution or a larger tau2 run only if:

```text
Primary gates:
1. oracle_v1 beats failure_mode_only on held-out tasks
2. oracle_v1 beats coarse_reflection on held-out tasks

Confirmatory guards:
3. generic_policy does not beat oracle_v1 by the calibrated margin
4. strict_hard_mismatch does not beat oracle_v1 by the calibrated margin
5. DB retention is not worse than no_memory/generic beyond the calibrated
   variability band
6. the result is not driven by anchors 16/95
7. anchors 16/95 reproduce the expected oracle-positive behavior within the
   calibrated variability band
```

Interpretation:

```text
Precise missing-check attribution appears to add value beyond broad mode routing
and coarse reflection for this failure family, without losing to generic memory
or strict mismatched memory.
```

If anchors `16/95` fail to reproduce their prior oracle-positive behavior far
outside the calibrated variability band, mark the run noise-dominated and do not
call it GREEN even if the aggregate table looks favorable.

### YELLOW

Continue, but reframe, if:

```text
oracle_v1 > no_memory
but oracle_v1 does not beat failure_mode_only by the pre-registered margin
or oracle_v1 does not beat coarse_reflection by the pre-registered margin
or oracle_v1 ~= generic_policy
```

Interpretation:

```text
Runtime memory helps, but the useful signal may be failure-mode routing or a
generic communication reminder rather than precise attribution content.
```

Next move:

```text
pivot toward retrieval/routing experiments
```

Do not run:

```text
oracle_card_v3
longer checklist card
more detailed prose card
another same-family card wording iteration
```

### RED

Stop the runtime prose-card track if:

```text
oracle_v1 <= generic_policy
or oracle_v1 <= failure_mode_only
or strict_hard_mismatch matches oracle_v1
or oracle_v1 causes DB regression
```

Interpretation:

```text
Precise attribution content is not the active ingredient in this runtime memory
form.
```

Next move:

```text
use attribution as retrieval/routing/intervention-selection signal instead of
as prose memory content
```

Do not run another prose-card repair experiment unless a concrete report claim
requires it and the alternative routing/retrieval probe cannot answer that
claim.

## Expected Outcomes

Most likely:

```text
YELLOW
```

Reason:

```text
v1 was strong in Exp5.4, but much of the signal came from retention tasks.
failure_mode_only or generic communication reminders may capture much of the
benefit.
```

This is still useful. It tells us whether to keep pushing precise memory
content or pivot to attribution-guided retrieval/routing.

## If GREEN

Next:

```text
1. add predicted attribution-derived cards
2. keep intervention/task execution fixed
3. compare predicted card utility against oracle card utility
4. test whether attribution quality predicts utility
```

## If YELLOW or RED

Do not tune more prose cards.

Pivot to:

```text
1. retrieval/routing:
   use attribution to select which memory/check to apply

2. intervention selection:
   use attribution to decide when/where to intervene

3. policy-check selection:
   use attribution to select a validator or checklist, not to write prose

4. training/credit signal:
   use who/when/why attribution as localized credit assignment
```

## Reserved Follow-Up: Routing/Retrieval Mini-Probe

If Exp5.5 is YELLOW or RED, the next experiment should be a small pivot probe,
not a card-content variant.

Question:

```text
Can attribution improve retry success by selecting the right memory/check or
intervention target, even when prose card content itself does not separate from
generic reminders?
```

Minimal design:

```text
task pool:
  reuse the full Exp5.5 held-out family
  or use an independently selected held-out family
  do not filter to tasks where memory helped

conditions:
  no_memory
  generic_memory_pool_random_selection
  failure_mode_routed_memory
  oracle_failure_attribution_routed_memory
  strict_wrong_routing

primary contrast:
  oracle_failure_attribution_routed_memory - failure_mode_routed_memory

secondary contrast:
  oracle_failure_attribution_routed_memory - random_selection
```

Interpretation:

```text
If routed memory beats random/generic selection, attribution may be more useful
as a selection signal than as prose content.
```

This gives the final report a forward-looking result instead of ending at a
negative prose-card finding.

## Report Outline To Draft Before Running

Before implementing Exp5.5, draft the report outline and identify which gaps
Exp5.5 and the optional routing probe must fill.

Recommended outline:

```text
1. Research question
   Precise failure attribution as self-improvement signal.

2. Why existing attribution benchmarks are insufficient
   They measure localization, not downstream utility.

3. Who&When PoC
   Trace-prefix repair works as a diagnostic, but it is not deployment.

4. tau2 runnable rescue setup
   Fresh execution, official reward, runtime memory injection.

5. What we learned from Exp5.3/5.4
   Runtime memory is live.
   v2 broad ledger failed.
   v1 narrow missing-check signal is promising but retention-driven.
   Effects are mostly NL/communication, not robust DB/tool completion.

6. Exp5.5 final prose-memory gate
   Precise missing-check vs generic/coarse/mode-only.
   Variability and saturation handled explicitly.

7. Decision
   GREEN: proceed to predicted attribution content.
   YELLOW/RED: pivot to routing/retrieval/intervention selection.

8. Caveats
   single-agent tau2, no "who" dimension;
   oracle cards, not predicted attribution;
   noisy same-seed behavior;
   official reward has DB/NL components.

9. Recommendation
   Continue only if precise content separates.
   Otherwise shift attribution from "what prose to inject" to "which check,
   memory, or intervention to select."
```

The report should be written so that a null result is still an interpretable
finding, not a failed search for a positive table.

## Implementation Notes

Before implementation:

```text
1. build variability calibration manifest
2. build task candidate audit table
3. write cards only after task pool is fixed
4. enforce leakage audit
5. generate manifest from reviewed card table
6. run calibration
7. update analysis mode based on calibration
8. run main experiment
```

Do not start Exp5.5 with hand-picked positive tasks only. The held-out task pool
is the validity of the experiment.
