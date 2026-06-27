# Experiment 5.4: tau2 Tool-Side Completion Audit and Targeted Rescue

## Status

Planned.

Experiment 5.4 is the next step after Experiment 5.3. It should not be a blind
scale-up. Experiment 5.3 showed that the tau2 fresh-retry harness works, but it
did not show that attribution-derived oracle cards beat generic runtime memory.

The purpose of Experiment 5.4 is to determine whether the weak oracle result in
Experiment 5.3 was caused by a fixable card-design issue, especially failure to
push the agent through DB/tool-side completion.

## Why This Experiment Exists

Experiment 5.3 result:

```text
generic_policy_card              16 / 60 = 0.2667
oracle_single_missing_check_card 15 / 60 = 0.2500
hard_mismatched_card             13 / 60 = 0.2167
no_memory                        12 / 60 = 0.2000
```

This is not a GREEN result.

The strongest diagnostic signal was the component split:

```text
condition                        DB mean   NL_ASSERTION mean
generic_policy_card              0.5167    0.5965
oracle_single_missing_check_card 0.4000    0.6842
hard_mismatched_card             0.4667    0.6667
no_memory                        0.4500    0.5965
```

The oracle card improved communication/NL behavior but had the lowest DB mean.
This suggests that the current `oracle_single_missing_check_card` may teach the
agent what to say or check, without reliably forcing completion of the required
tool-side mutations.

Experiment 5.4 asks:

> If oracle cards are rewritten as non-leaky tool-side completion ledgers, do
> they improve official tau2 reward more than generic memory, the old oracle
> card, and hard mismatched memory?

This question has one construct-validity risk:

```text
tool-side completion ledger
can drift into
task decomposition / task scaffolding
```

If that happens, a positive result would show that task scaffolding helps, not
that failure attribution helps. Experiment 5.4 must therefore keep the v2 oracle
card anchored to the failure observed in Experiment 5.3.

## What This Experiment Is Not

Experiment 5.4 is not a paper-level proof.

It does not test predicted attribution. It does not test a closed-loop
self-improving agent. It does not test MAS `who` attribution. It is still an
oracle upper-bound runtime-memory probe in a single-agent tau2 retail setting.

Its role is to decide whether this tau2 card direction deserves a larger run.

## Primary Questions

### Q1. Was Exp5.3 oracle underperformance caused by card mis-specification?

Specifically:

```text
Did the oracle card identify the right missing check,
but fail to enforce all required DB/tool-side branches?
```

### Q2. Were Exp5.3 mismatched cards truly orthogonal?

If mismatched cards contained reusable retail subskills that happened to help,
then `oracle ~= mismatch` is not a clean negative result.

### Q3. Does a tool-side completion ledger card improve DB and official reward?

The new oracle card should make the agent track:

```text
failure-implicated branches
policy/evidence checks
required DB/tool mutations
required final communication
```

without leaking exact IDs, exact values, tool arguments, or final answers.

The ledger is not allowed to become a full task plan. It is only allowed to
wrap the failure-derived missing check in a stronger completion discipline.

## Construct Guardrail: Attribution Anchor vs Task Scaffold

Experiment 5.4 is only useful for the attribution thesis if the v2 oracle card
is derived from the audited failure, not just from the task prompt.

### Allowed Oracle v2 Shape

The oracle v2 card may include:

```text
1. the decisive missing check identified by Exp5.3 audit
2. the branch type directly implicated by that missing check
3. the tool-side completion requirement needed to avoid repeating that failure
4. the final communication requirement if it was part of the audited failure
```

Example:

```text
If the audited failure was "computed refund total but did not complete every
return/cancel action included in that total", then the v2 card may require a
ledger over refund-contributing branches.
```

### Forbidden Oracle v2 Shape

The oracle v2 card must not simply decompose the whole task into all visible
branches if those branches were not implicated by the audited failure.

Example of a drifted card:

```text
List every user request branch, solve each one, then respond.
```

That is a task scaffold, not a failure-attribution card.

### If Audit Requires Broad Task Scaffolding

If Phase 5.4B shows that the only useful intervention is broad task
decomposition, then do not label the card as `oracle_tool_completion_card_v2`.
Instead, either:

```text
1. add it as a separate `task_scaffold_card_v2` baseline, or
2. stop the card-content track and report that attribution-specific content was
   not isolated from task scaffolding.
```

This is a valid finding, but it weakens the original attribution-specific
claim.

## Phase 5.4A: Freeze Exp5.3 Into Audit-Ready Artifacts

This phase should use existing Exp5.3 raw results only. It should not call the
model API.

### Outputs

Add the following committed artifacts under:

```text
reports/exp5_3_rescue_20/
```

Required:

```text
per_run_outcomes.csv
pairwise_condition_matrix.csv
```

Optional but useful:

```text
task_pairwise_condition_matrix.csv
```

### `per_run_outcomes.csv`

Required fields:

```text
experiment_id
task_id
seed
condition
success
final_reward
db_reward
communicate_reward
nl_assertion_reward
result_path
```

Purpose:

```text
Make every Exp5.3 run auditable without reading the ignored raw simulation tree.
```

### `pairwise_condition_matrix.csv`

Compute pairwise comparisons over the same `(task_id, seed)` keys.

Required fields:

```text
condition_a
condition_b
paired_attempts
condition_a_successes
condition_b_successes
a_beats_b
b_beats_a
ties_success
ties_failure
success_delta_a_minus_b
```

Required contrasts:

```text
oracle_single_missing_check_card vs generic_policy_card
oracle_single_missing_check_card vs hard_mismatched_card
generic_policy_card vs hard_mismatched_card
oracle_single_missing_check_card vs no_memory
generic_policy_card vs no_memory
hard_mismatched_card vs no_memory
```

Purpose:

```text
Avoid over-reading aggregate condition means.
Show exactly where oracle wins, loses, ties, and regresses.
```

## Phase 5.4B: Qualitative Audit of Exp5.3

This phase should inspect traces and task requirements before designing new
cards. It is the gate before rerunning anything.

### Audit Set

Primary audit tasks:

```text
oracle-positive:
  16, 95

generic-beats-oracle:
  36, 103

mismatch-beats-oracle:
  19, 41, 104
```

Optional diagnostic task:

```text
20 or 28
```

Use the optional diagnostic task only to inspect whether an all-condition
failure is unwinnable, card-recoverable, or model-capability-limited.

### Audit Output

Create:

```text
docs/experiment5_4_audit.md
```

For each task, record:

```text
task_id
audit_role
representative_seed
expected_requirement_summary
decisive_failure_anchor
missing_check_from_failure
tool_completion_gap_from_failure
oracle_card_summary
generic_card_summary
mismatch_card_summary
oracle_outcome
generic_outcome
mismatch_outcome
oracle_failed_because
generic_succeeded_because
mismatch_succeeded_because
db_failure_type
nl_failure_type
oracle_card_used_correctly
oracle_caused_over_caution
mismatch_is_orthogonal
mismatch_accidentally_helpful
task_appears_card_recoverable
recommended_card_fix
```

### Audit Decision

Proceed to card v2 only if the audit supports at least one of these:

```text
1. oracle v1 often points at the right issue but fails to force tool completion.
2. generic wins because it preserves broader branch coverage that is actually
   implicated by the audited failure.
3. mismatch wins because the mismatch card is not truly orthogonal.
```

Criterion 2 must be split carefully:

```text
If generic wins because the audited failure is genuinely multi-branch and v1
under-specified the failure-implicated branches:
  proceed to an audit-anchored oracle v2.

If generic wins because it covers branches unrelated to the audited failure:
  do not proceed to oracle v2.
  Treat the result as evidence for task scaffolding or generic discipline.
```

Do not proceed directly to Exp5.4 rerun if the audit mostly shows:

```text
1. tasks are unwinnable for the current model,
2. task reward/evaluator is incompatible with the policy,
3. oracle cards are already correct but the model cannot follow them,
4. results are dominated by random user-simulator variation.
```

If those dominate, run a separate capability-ceiling probe before changing cards.

## Phase 5.4C: Card v2 Design

### Core Change

Do not replace the current single-missing-check oracle card with an unrelated
task scaffold. Convert the audited missing check into a tool-side completion
card only when the audit supports that conversion.

The current v1 card often says:

```text
Check X before final response.
```

The v2 card should say:

```text
For the branch implicated by missing check X, confirm evidence, policy, required
DB mutation, and required communication before finalizing.
```

If multiple branches are listed, each branch must be justified by the audit as
part of the observed failure. Do not add branches merely because they are visible
in the task prompt.

### Oracle v2 Schema

Use this schema for `oracle_tool_completion_card_v2`:

```text
Failure Card: <abstract failure name>

Task structure:
- Failure-implicated branch A: <abstract branch type>
- Failure-implicated branch B: <abstract branch type, if audit supports it>
- Final communication implicated by the failure: <abstract communication requirement>

Failure pattern:
The agent may explain or check the right issue, but finalize before completing
the tool-side branch that makes the check actionable.

Do:
Maintain a completion ledger for the failure-implicated branch(es). For each
listed branch, mark:
policy/evidence checked, action allowed, tool action completed, communication
completed.

Do not:
Do not treat a correct explanation, calculation, or summary as a substitute for
a missing DB-changing tool call.

Check before final response:
For every listed failure-implicated branch, can I point to the tool evidence or
tool mutation that completed it?
```

If this schema cannot be filled without listing the whole task, the card is not
an attribution-specific oracle card. Treat it as task scaffolding.

### Leakage Rules

The v2 oracle card may include abstract branch types:

```text
delivered-item return
pending-order cancellation
pending-order item modification
pending-order address modification
tracking lookup
refund-total communication
price-difference communication
available-option count communication
```

The v2 oracle card must not include:

```text
exact order IDs
exact item IDs
exact product names when they directly identify the solution
exact refund amounts
exact price differences
tracking numbers
final answer text
tool argument values
```

### Generic v2 Schema

`generic_policy_card_v2` must use the same format and approximate length as
oracle v2, but without failure-specific branch types.

Example:

```text
Failure Card: General retail branch-completion checklist

Task structure:
- Identify every user-request branch.
- For each branch, determine whether it requires lookup, policy check, DB
  mutation, calculation, or communication.

Failure pattern:
The agent may complete one branch and finalize while another required branch is
unfinished.

Do:
Maintain a branch ledger. For each branch, mark:
evidence checked, policy checked, tool action completed if required, and final
communication completed.

Do not:
Do not finalize after a partial branch, even if the final answer sounds
reasonable.

Check before final response:
Have I completed every required branch and communicated every required result?
```

### Mismatch v2

Use stricter mismatch controls than Exp5.3.

Define two categories during audit:

```text
irrelevant_benign_mismatch:
  A card about a branch type not present in the target task.
  It should not help the target task, but should also not strongly sabotage it.

wrong_but_plausible_mismatch:
  A card about a nearby retail action class, but with the wrong decisive check.
  It tests whether near-miss attribution can misdirect behavior.
```

For the first targeted rerun, choose one primary mismatch condition:

```text
hard_mismatched_card_v2
```

The audit should document which subtype each task receives.

## Phase 5.4D: Targeted Rerun

Run a small targeted rerun only after Phase 5.4A and 5.4B are complete.

### Recommended Task Set

Use 7 required audit-derived tasks plus one diagnostic slot:

```text
positive retention:
  16, 95

generic-beats-oracle repair:
  36, 103

mismatch-control repair:
  19, 41, 104

hard/no-success diagnostic:
  choose 20 or 28 only if Phase 5.4B finds the chosen task card-recoverable
```

Task `20` is the default diagnostic because it appeared in the all-condition
failure set. Replace it with `28` only if Phase 5.4B shows that `20` is clearly
unwinnable or evaluator-conflicted. If both are unwinnable, drop the diagnostic
slot or replace it with another audited card-recoverable task. Do not include a
known-dead task merely to keep the count at eight.

### Conditions

Use five conditions:

```text
no_memory
generic_policy_card_v2
oracle_single_missing_check_card_v1
oracle_tool_completion_card_v2
hard_mismatched_card_v2
```

Do not add predicted attribution yet.

Do not add cross-task transfer yet.

Do not add a larger model as a main condition yet.

### Reproduction Validity Check

Because Experiment 5.4 reuses selected tasks and seeds from Experiment 5.3, it
must check whether unchanged conditions reproduce their prior outcomes.

Before the main Exp5.4 rerun, run a cheap same-seed determinism probe:

```text
repeat 2-3 selected (task_id, seed, no_memory) cells twice
compare success outcomes and component rewards
```

Use the observed probe disagreement rate to set the reproduction threshold for
the main run. If the probe already shows unstable same-seed outcomes, paired
seed analysis is weak and the main Exp5.4 run should either:

```text
1. increase repetitions, or
2. report primarily unpaired/per-task rates instead of strong paired claims.
```

Compare these repeated `(task_id, seed, condition)` rows against Exp5.3:

```text
no_memory
oracle_single_missing_check_card_v1
```

Default threshold if the probe is stable:

```text
unchanged-condition success flips <= 5% of repeated rows
```

If the probe itself shows nonzero same-seed disagreement, set the threshold to
at least the probe disagreement rate plus one repeated row. Report both the
probe disagreement rate and the main-run reproduction disagreement rate.

If the main-run disagreement exceeds the threshold, treat paired claims as
unstable and do not mark the run GREEN.

This check is not meant to punish normal LLM variance. It is a validity check
for whether same-seed pairing is strong enough to support the interpretation.

### Seeds and Scale

Primary targeted run:

```text
7-8 tasks x 5 conditions x 3 seeds = 105-120 runs
```

Use the same seeds as Exp5.3 if possible:

```text
501, 502, 503
```

If the diagnostic slot is dropped, report the run as a 7-task targeted check
rather than backfilling with an unaudited task. If the result is split but
promising, run a second pass with two additional seeds only for non-dead tasks:

```text
504, 505
```

### Primary Metrics

Report:

```text
official success rate
DB mean
NL_ASSERTION mean
paired oracle_v2 - generic_v2
paired oracle_v2 - oracle_v1
paired oracle_v2 - hard_mismatch_v2
paired oracle_v2 - no_memory
paired regressions vs no_memory
per-task outcome matrix
unchanged-condition reproduction disagreement rate
```

Interpret DB and NL separately. A card that only raises NL while lowering DB is
not a clear rescue card.

Interpret `oracle_v2 - oracle_v1` as a diagnostic contrast only. It mixes a
format change, a completion-discipline change, and a content change. It can show
that v2 is more useful than v1, but it cannot by itself prove why v2 is better.

### Secondary Metrics

If available from traces:

```text
number of DB-mutating tool calls
number of final communication turns
whether all expected branch types were attempted
termination reason
```

These are diagnostic only unless they can be reliably computed.

## Decision Rules

### GREEN

Proceed to a larger tau2 rescue run only if aggregate and task-level checks both
pass.

Aggregate checks:

```text
oracle_tool_completion_card_v2 > generic_policy_card_v2
oracle_tool_completion_card_v2 > oracle_single_missing_check_card_v1
oracle_tool_completion_card_v2 > hard_mismatched_card_v2
DB mean under oracle_v2 is not below generic_v2
mismatch_v2 does not match or exceed oracle_v2
```

Task-level strict checks:

```text
strict_task_win(A, B) = number of tasks where A has more successes than B over
the same seeds.

strict_task_loss(A, B) = number of tasks where A has fewer successes than B over
the same seeds.

Required:
  strict_task_win(oracle_v2, generic_v2) >= 2
  strict_task_win(oracle_v2, oracle_v1) >= 2
  strict_task_loss(oracle_v2, generic_v2) <= 1
  strict_task_loss(oracle_v2, hard_mismatch_v2) <= 1
```

The `oracle_v2` wins over `generic_v2` must not come only from retention tasks
where oracle already won in Exp5.3. At least two strict wins over `generic_v2`
must occur in the repair set:

```text
repair set = 36, 103, 19, 41, 104
```

Retention tasks have a different role:

```text
16, 95 should verify that oracle_v2 does not regress clean oracle-positive cases.
They do not by themselves establish that v2 fixed the Exp5.3 failure mode.
```

Also required:

```text
no task where oracle_v2 is 0/3 while generic_v2 is at least 2/3,
unless Phase 5.4B pre-labeled that task as not card-recoverable.
```

For this small targeted run, GREEN should be interpreted as:

```text
worth scaling to a broader controlled run
```

not:

```text
paper-level evidence
```

GREEN does not authorize a same-condition scale-up by itself. The next larger
run must include the missing North Star baselines:

```text
coarse_reflection_memory
raw_failure_explanation_memory
```

Without those, the project still has not tested whether precise attribution
beats coarse self-reflection or raw failure explanation.

### YELLOW

Continue cautiously if:

```text
oracle_v2 > no_memory
but oracle_v2 ~= generic_v2
or oracle_v2 improves NL while only slightly improving DB
```

Interpretation:

```text
runtime memory helps, but attribution-specific content is still not isolated.
```

Next move would be either:

```text
1. add coarse_reflection / raw_failure_explanation baselines, or
2. pivot toward routing/retrieval rather than rich card content.
```

### RED

Do not scale the card-content track if:

```text
oracle_v2 <= generic_v2
or oracle_v2 <= hard_mismatch_v2
or oracle_v2 continues to improve NL while hurting DB
or most selected tasks remain unwinnable across all conditions
```

Interpretation:

```text
The current attribution-card mechanism is not the active ingredient for tau2
fresh rescue.
```

Next move:

```text
1. run capability-ceiling probe with a stronger agent model, or
2. pivot to attribution as retrieval/routing signal, or
3. build a controlled runnable benchmark where failure modes are programmatic.
```

## Implementation Checklist

### Task 1: Add Audit-Ready Exp5.3 Reports

Files:

```text
tau2_card_poc/src/tau2_card_poc/reporting.py
tau2_card_poc/src/tau2_card_poc/cli.py
tau2_card_poc/tests/test_reporting.py
reports/exp5_3_rescue_20/per_run_outcomes.csv
reports/exp5_3_rescue_20/pairwise_condition_matrix.csv
```

Steps:

```text
1. Add writer for per-run outcomes.
2. Add pairwise condition comparison over shared (task_id, seed).
3. Wire both into `tau2-card-poc summarize`.
4. Add tests for both writers.
5. Re-run summarization for Exp5.3.
```

### Task 2: Write Exp5.3 Qualitative Audit

Files:

```text
docs/experiment5_4_audit.md
third_party/tau2-bench/data/simulations/exp5_3_rescue_20/
```

Steps:

```text
1. Inspect representative traces for tasks 16, 95, 36, 103, 19, 41, 104.
2. Mark whether oracle v1 failed from DB omission, NL omission, over-caution,
   wrong branch focus, or model capability.
3. Mark whether mismatch was genuinely orthogonal.
4. Decide whether card v2 is justified.
```

### Task 3: Create Exp5.4 Manifest

Files:

```text
tau2_card_poc/experiments/exp5_4_tool_completion_targeted.json
docs/experiment5_4_card_audit.md
```

Steps:

```text
1. Define 7 required task IDs plus one optional audited diagnostic task.
2. Define 5 conditions.
3. Keep v1 oracle cards for comparison.
4. Add format-matched generic v2 cards.
5. Add audit-anchored oracle tool-completion v2 cards.
6. Add stricter mismatch v2 cards.
7. Audit all cards for leakage and task-scaffold drift before running.
```

### Task 4: Run Exp5.4 Targeted Rerun

Files:

```text
third_party/tau2-bench/data/simulations/exp5_4_tool_completion_targeted/
reports/exp5_4_tool_completion_targeted/
docs/experiment5_4_results.md
```

Steps:

```text
1. Run manifest with resume enabled.
2. Summarize all outputs.
3. Report condition, pairwise, task-level, DB, and NL metrics.
4. Interpret GREEN/YELLOW/RED against the decision rules above.
```

## Claim Boundary

If Experiment 5.4 is positive, the strongest supported claim is:

```text
In a targeted tau2 retail fresh-retry setting, a non-leaky oracle card that
preserves the audited failure-specific missing check while adding tool-side
completion discipline can improve official reward over the previous
single-check oracle card and generic runtime memory.
```

Do not claim:

```text
predicted attribution works
closed-loop self-improvement works
multi-agent who attribution is useful
cards transfer across tasks
the method is paper-ready
```

Those require later experiments.
