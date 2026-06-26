# Experiment 2 Plan: Specificity Gate to Reusable Failure Memory

This is the detailed companion plan. The canonical execution doc is:

```text
docs/experiment2.md
```

## North Star

The research goal is not merely to show that an extra prompt helps.

The real question is:

```text
Does precise failure attribution create better self-improvement memory than coarse reflection?
```

In other words:

```text
Can who/when/why failure attribution be converted into compact, targeted, reusable execution memory
that helps agents avoid future failures better than generic in-context reflection?
```

This framing treats in-context learning as a baseline mechanism, not as the contribution. The
contribution is deciding **what failure information should be extracted, stored, retrieved, and
reused**.

## Why Experiment 1 Was Necessary but Insufficient

Experiment 1 showed a useful lower-level signal:

```text
Gold Who&When attribution -> runtime card -> lower same-failure recurrence at the gold step.
```

But it did not show attribution-specific utility.

The failure mode was clear:

```text
oracle_runtime_card   success 0.6 / recurrence 0.2
wrong_mismatched_card success 0.8 / recurrence 0.2
```

This means the current cards likely acted as broadly useful verification nudges rather than
attribution-specific execution memory.

Therefore Experiment 2 should not ask:

```text
Does the card beat no guidance?
```

It should ask:

```text
Does attribution-specific memory beat coarse reflection, broad verification nudges,
and hard mismatched memory?
```

## Overall Ladder

The project should climb the following ladder.

```text
Level 0. Same-trace gold-point repair
  Already done in Experiment 1.
  Shows local behavioral repair is possible.

Level 1. Attribution specificity gate
  Next immediate experiment.
  Tests whether precise attribution beats coarse reflection and generic nudge.

Level 2. Cross-trace transfer
  Tests whether a lesson from one failed trace helps a held-out similar failure.
  This is the first real reusable-memory signal.

Level 3. Predicted card content utility
  Keeps gold who/when fixed and tests whether all_at_once / step_by_step / binary_search
  predicted why/card content is useful.

Level 4. Closed-loop self-improving agent
  Built only after transfer beats coarse/generic baselines.
  First test oracle memory in fail -> attribute -> card memory -> retry / held-out improvement.

Level 5. Predicted intervention utility
  Tests predicted who/when and therefore where and to whom the system should inject memory.
```

Experiment 2 covers Levels 1 and a small probe for Level 2.

## Experiment 2A: Specificity Gate

### Goal

Test whether gold attribution-derived cards are useful because of attribution specificity, not just
because they tell the model to be careful.

Primary question:

```text
oracle_specific_card > coarse_reflection / broad_verification_card / hard_mismatched_card ?
```

### Hypotheses

```text
H1. Oracle upper-bound utility:
oracle_specific_card improves repair over no_guidance.

H2. Specificity utility:
oracle_specific_card beats coarse_reflection, broad_verification_card, and hard_mismatched_card.

H3. Structured memory utility:
oracle_specific_card beats sanitized_raw_gold_explanation.

H4. Negative control sanity:
hard_mismatched_card should not outperform oracle_specific_card.
```

### Conditions

Use the same visible card structure and similar length for all card-shaped conditions. Only the
information source should differ.

Recommended smoke condition set:

```text
1. no_guidance
2. coarse_reflection
3. broad_verification_card
4. sanitized_raw_gold_explanation
5. oracle_specific_card
6. hard_mismatched_card
```

Optional extra conditions after the first smoke:

```text
7. oracle_mode_card_current
8. length_matched_placebo_card
9. full_failed_trace_context
```

`full_failed_trace_context` is an ICL upper-bound baseline. It should be interpreted with token cost:

```text
oracle_specific_card > full_failed_trace_context:
  Strong result for structured attribution memory.

oracle_specific_card ~= full_failed_trace_context with far fewer tokens:
  Good result for compact memory.

full_failed_trace_context > oracle_specific_card:
  Not automatically fatal; report token-normalized utility and retrieval cost.
```

Condition definitions:

```text
no_guidance:
  No extra guidance and no failure-awareness signal.
  The shared base prompt must not say this is a failed trajectory.

coarse_reflection:
  Reflexion-style coarse prompt. It says this trajectory may be heading toward a mistake and asks
  the agent to reflect before the next action, but it does not provide who/when/why attribution.

broad_verification_card:
  Format-matched Runtime Failure Card with generic content:
  verify facts, re-check constraints, avoid unsupported assumptions.
  This is the H_nudge ceiling.

sanitized_raw_gold_explanation:
  Cleaned gold mistake_reason as prose, with leakage removed.
  Tests whether raw explanation is enough without card structure.

oracle_specific_card:
  Case-specific but non-leaky card derived from gold mistake_reason.
  It should extract the violated requirement pattern and missing check type.

hard_mismatched_card:
  Same card format and similar length, but sourced from an orthogonal failure mode.
  It should be genuinely inapplicable to the target prefix.
```

### Primary Readouts

```text
specificity_lift =
  repair_rate(oracle_specific_card)
  - max(
      repair_rate(coarse_reflection),
      repair_rate(broad_verification_card),
      repair_rate(hard_mismatched_card)
    )

right_vs_wrong_lift =
  repair_rate(oracle_specific_card)
  - repair_rate(hard_mismatched_card)

nudge_gap =
  repair_rate(oracle_specific_card)
  - repair_rate(broad_verification_card)

recurrence_specificity_lift =
  recurrence_rate(hard_mismatched_card)
  - recurrence_rate(oracle_specific_card)
```

### Go / No-Go Rules

Set these before running, but distinguish smoke from powered runs.

Experiment 2A smoke is not a statistical confirmation.

```text
smoke purpose:
  Check direction.
  Verify no_guidance is not failure-aware.
  Verify hard_mismatched_card does not again outperform oracle_specific_card.
  Decide whether to pay for a powered run.
```

Do not treat a +10 percentage point difference in the smoke as strong evidence. With roughly
10-12 cases x 2 attempts, proportion estimates are too noisy.

The real gate is the powered run:

```text
30 failure-prone cases
× 6 conditions
× 3 attempts
≈ 90 judgments per condition
paired bootstrap CI or paired permutation test
```

Use case-level clustered bootstrap:

```text
resample cases, not individual generations
aggregate attempts within each case before computing paired deltas
```

Attempts from the same case are correlated. Treating 90 condition records as independent would
underestimate uncertainty.

Also, n=30 cases may be underpowered for a +10 percentage point effect. A small positive nudge_gap
with CI crossing zero should be treated as inconclusive, not automatically no-go.

Primary contrast:

```text
nudge_gap =
  repair_rate(oracle_specific_card)
  - repair_rate(broad_verification_card)
```

`nudge_gap` is primary because oracle_specific_card and broad_verification_card share the same
card format. The oracle-vs-coarse-reflection contrast is still important, but it mixes content with
card-vs-prose format.

Powered strong go:

```text
oracle_specific_card repair_rate >= no_guidance + 15 percentage points
oracle_specific_card recurrence_rate <= no_guidance - 20 percentage points
oracle_specific_card repair_rate >= broad_verification_card + 10 percentage points
oracle_specific_card repair_rate >= hard_mismatched_card + 10 percentage points
hard_mismatched_card does not outperform oracle_specific_card
paired bootstrap CI for nudge_gap has lower bound > 0
```

Powered soft go:

```text
oracle_specific_card beats no_guidance
but is close to broad_verification_card
and still beats hard_mismatched_card.
```

Interpretation:

```text
Failure memory helps, but the current card is not specific enough.
Revise card renderer and repeat before predicted attribution.
```

Powered no-go:

```text
oracle_specific_card ~= broad_verification_card
or hard_mismatched_card >= oracle_specific_card.
```

Interpretation:

```text
The current effect is probably generic in-context nudging rather than attribution-specific memory.
Do not add predicted Who&When methods yet.
```

Important interpretation:

```text
Experiment 2A is a kill-gate, not a confirmation result.
Passing 2A only means the setup is worth testing in transfer.
The first strong reusable-memory evidence starts in Experiment 2B.
```

## Card Design Requirements

## Shared Prompt Requirement

Experiment 2 must remove failure-awareness from the shared base prompt.

Do not use:

```text
You are continuing a failed multi-agent trajectory from a prefix.
```

Use:

```text
You are continuing a multi-agent trajectory from a prefix.
```

Condition-specific failure awareness is allowed only in the relevant condition text:

```text
no_guidance:
  No failure signal.

coarse_reflection:
  This trajectory may be heading toward a mistake; reflect before the next action.
  No who/when/why attribution.

oracle_specific_card:
  Gold attribution-derived specific runtime memory.
```

### Oracle Specific Card

The oracle card must be more specific than the current mode-level canned card, but it must not leak
answers or hidden labels.

Suggested fields:

```text
Runtime Failure Card
Failure mode:
Violated requirement pattern:
Risky next-action pattern:
Do:
Do not:
Check before next action:
Applicable when:
```

Allowed information:

```text
- failure pattern category
- violated requirement pattern
- missing check type
- role/action context
- forward-looking do / do_not / check_before_next_action
- task-specific requirement pattern, as long as it does not reveal the final answer
```

Forbidden information:

```text
- exact mistake_step
- original failed action text
- gold answer
- evidence span from the failed action
- "you failed at step N" or future-failure wording
- benchmark labels visible to the agent
```

Leakage must be blocked, not merely logged.

```text
exact-match leakage flag:
  regenerate or drop the card
  never use it as agent-visible guidance

secondary LLM leakage check:
  run paraphrase leakage checks for oracle_specific_card
  inspect whether the card indirectly reveals the gold answer, original failed action,
  hidden step information, or benchmark labels

human/secondary audit:
  prioritize oracle_specific_card in the smoke audit
  regenerate or exclude suspicious cards
```

If oracle cards leak answers or hidden future-failure information, specificity conclusions are
invalid.

Example pattern:

```text
Failure mode:
Incomplete handling of task constraints or data cases

Violated requirement pattern:
The next action may simplify the task by applying only the first obvious rule while missing a stated
exception, edge case, or output constraint.

Do:
Before producing the next action, enumerate the constraints from the original task and check whether
the planned action satisfies each one.

Do not:
Do not proceed with a simplified calculation or extraction rule until edge cases and exceptions have
been checked.

Check before next action:
Which stated constraint or exception could invalidate the next action?
```

### Broad Verification Card

This card should be deliberately generic and format-matched.

It should not mention the case, task, role, failure mode, or any gold attribution.

Purpose:

```text
Measure the ceiling of "just be careful / verify before acting."
```

### Hard Mismatched Card

Hard mismatch must be stricter than Experiment 1.

Do not choose merely "a different inferred failure mode" if the corrective action is still broadly
useful.

Use orthogonal corrective-action pairings:

```text
target fabricated data -> mismatch navigation drift card
target unverified factual claim -> mismatch routing/handoff card
target constraint violation -> mismatch premature finalization card
target premature finalization -> mismatch table constraint card
target navigation drift -> mismatch numerical verification card
```

If possible, keep a small pairing table:

```text
target_case_id
target_failure_mode
mismatch_source_case_id
mismatch_failure_mode
why_orthogonal
```

## Case Selection

Experiment 1 had too much failure-mode monoculture. Experiment 2 must stratify cases.

Target failure-mode buckets:

```text
unsupported assumption / fabricated data
unverified factual claim
constraint or format violation
premature finalization
navigation drift / irrelevant action
handoff or routing error
```

Smoke target:

```text
20 candidate cases for no-guidance pretest
10-12 failure-prone cases selected for main smoke
at least 3-4 failure-mode buckets represented
2 attempts per condition
```

Main target after smoke:

```text
50-60 candidate cases for no-guidance pretest
30 failure-prone cases selected for main run
5-6 failure-mode buckets represented
3 attempts per condition
```

If algorithm-generated cases are insufficient for some buckets, allow a controlled hand-crafted
subset, but tag these cases explicitly:

```text
dataset_type
has_system_prompt
history_len
role_reconstruction_method
```

Per-mode metrics are descriptive by default. With 30 cases spread across 5-6 buckets, each bucket is
too small for inferential claims. If per-mode inference is required, use fewer buckets, for example:

```text
3 major modes × about 10 cases per mode
```

## Judge Changes

The judge must distinguish intention from concrete action.

Add fields:

```text
states_relevant_intent: boolean
performs_concrete_repair_action: boolean
verification_is_concrete: boolean
verification_is_stated_intent_only: boolean
task_progress: boolean
negative_transfer: boolean
recurs_same_failure: boolean
avoids_decisive_error: boolean
repair_success: boolean
repair_score: integer 0-3
rationale: short string
```

Repair success should require:

```text
avoids_decisive_error == true
negative_transfer == false
and, when the failure mode requires verification, verification_is_concrete == true
and the candidate performs a concrete relevant next action
```

Treat `task_progress` as a supporting field. In a single next-action evaluation, progress is noisy:
requesting a missing source, asking a necessary clarification, checking constraints, or routing to
the correct agent/tool may be a valid repair action even if it does not directly advance the final
answer.

Do not count a candidate as repaired if it only says:

```text
I will verify this later.
I should be careful.
I need to check the facts.
```

unless it also performs or concretely initiates the relevant action, such as requesting the needed
source, recalculating, checking a constraint list, or routing to the correct agent/tool.

Interpretation examples:

```text
"I should verify this later":
  states_relevant_intent = true
  performs_concrete_repair_action = false
  repair_success = false

"I will request the needed source now" / "Here is the constraint checklist before acting":
  performs_concrete_repair_action = true
```

Keep the judge condition-blind. The judge can see diagnostic information for evaluation, but not the
condition name.

Optional reliability check:

```text
Use a second judge on 20% of judgments or at least 30 judgments, whichever is smaller.
Report agreement on repair_success and recurs_same_failure.
```

## Required Outputs

The next runner/report should emit:

```text
condition-level metrics
case-level matrix
paired rescue metrics
paired negative transfer metrics
specificity_lift metrics
failure-mode stratified metrics
leakage summary
human/secondary audit sample
```

### Case-Level Matrix

Required table:

```text
case_id
failure_mode
attempt
no_guidance
coarse_reflection
broad_verification_card
sanitized_raw_gold_explanation
oracle_specific_card
hard_mismatched_card
notes
```

Useful qualitative buckets:

```text
oracle_only_success
oracle_and_mismatch_success
mismatch_only_success
nudge_only_success
all_success
all_failure
```

These buckets are necessary for diagnosing whether specificity is real or whether all prompts are
just nudging the model into verification behavior.

## Experiment 2B: Cross-Trace Transfer Probe

Experiment 2A is still same-trace repair. To move toward self-improving agents, run a small transfer
probe immediately after the specificity gate.

### Goal

Test whether a card derived from one failed trace helps a different held-out trace with a similar
failure pattern.

Question:

```text
Does source-failure memory transfer to target failures better than coarse reflection or generic nudge?
```

Define the transfer unit before pairing cases:

```text
transfer unit =
  failure-mode pattern
  + missing check type
  + abstract corrective action
```

Literal task details are not the transfer unit.

Examples:

```text
bad transfer unit:
  "Verify the population of France."

good transfer unit:
  "Verify external factual claims against a source before finalizing."
```

The card must be specific enough to beat generic nudges in 2A, but abstract enough to transfer in
2B. This specificity-transferability tension is the main design challenge.

### Setup

```text
source failed trace
-> source oracle_specific_card
-> held-out target trace prefix
-> target next-action regeneration
-> judge target repair / recurrence
```

### Conditions

```text
1. no_guidance
2. coarse_reflection_from_source
3. broad_verification_card
4. source_oracle_specific_card
5. source_hard_mismatched_card
6. raw_source_explanation
```

### Pairing

Use same-mode source-target pairs:

```text
source_failure_mode == target_failure_mode
source_case_id != target_case_id
```

This is an oracle retrieval upper bound: the experiment uses gold failure-mode labels to choose
source memories. It does not prove deployable memory retrieval.

Allowed claim:

```text
Under oracle retrieval of same-mode source memories, source cards transfer to held-out target traces.
```

Do not claim:

```text
The agent can retrieve the right failure memory by itself.
```

Label-free retrieval is a separate experiment:

```text
embedding retrieval
failure signature matching
predicted failure-mode classifier
```

And mismatched controls:

```text
source_failure_mode orthogonal to target_failure_mode
```

### Metrics

```text
transfer_repair_rate
transfer_recurrence_rate
source_card_vs_coarse_reflection
source_card_vs_broad_verification
source_card_vs_mismatched_source
negative_transfer_rate
```

This is the first result that can support "reusable failure memory."

## Closed-Loop Direction After Experiment 2

The final self-improving agent claim needs a runnable loop.

Minimal loop:

```text
Agent runs task
-> fails
-> attribution module analyzes trace
-> Failure Card generated
-> card stored in memory
-> future task retrieves relevant card
-> agent uses card during execution
-> success / recurrence measured
```

Possible controlled MAS:

```text
Planner -> Executor -> Reviewer
```

Failure modes:

```text
missing constraint
unverified output
premature finalization
wrong handoff
navigation drift
```

Closed-loop baselines:

```text
no_memory
coarse_reflection_memory
full_failed_trace_memory
raw_failure_explanation_memory
oracle_failure_card_memory
predicted_failure_card_memory
wrong_mismatched_memory
```

Closed-loop metrics:

```text
retry_rescue_rate
held_out_task_success_rate
same_failure_recurrence_rate
negative_transfer_rate
memory_retrieval_precision
tokens_per_success
```

This should become the eventual hero experiment, but it should not replace Experiment 2. Experiment
2B is the gate that tells us whether attribution-specific memory is worth building into the loop.

## Engineering Requirements

Before running Experiment 2:

```text
1. Add experiment_version to input, generation, and judgment records.
2. Include prompt_hash in resume keys or write versioned output paths.
3. Pass seed to model API when supported.
4. Log returned model snapshot / system_fingerprint if available.
5. Store card_text, card_source_case_id, source_failure_mode, target_failure_mode, leakage_flags,
   token counts, attempt, condition, and prompt_hash for every record.
6. Remove "failed trajectory" from shared base prompt and make failure awareness condition-specific.
7. Rerun the no_guidance recurrence pretest after changing the base prompt; Experiment 1's
   failure-prone subset is no longer valid under the neutral prompt.
8. Keep anti-leakage instructions shared across all conditions so they do not become a condition
   signal.
9. Remove any automatic hard-mismatch fallback that silently selects an arbitrary or same-mode card.
10. Keep .env and generated artifacts ignored.
```

Avoid stale resume bugs:

```text
Do not let a changed prompt/card renderer reuse old generations just because run_id and attempt match.
```

## Recommended Immediate Implementation Order

```text
0. Remove shared base-prompt failure awareness.
1. Implement v0.2 condition names and card schema.
2. Add oracle_specific_card renderer.
3. Add broad_verification_card and coarse_reflection conditions.
4. Add hard mismatch pairing table / selector with orthogonality notes.
5. Remove automatic hard-mismatch fallback.
6. Add stratified case selection by failure mode.
7. Rerun no_guidance recurrence pretest with the neutral base prompt.
8. Extend judge schema for concrete-vs-intent verification.
9. Add case-level matrix and paired metrics.
10. Run Experiment 2A smoke.
11. Write docs/who_when_phase2a_specificity_v2_smoke_results.md.
12. If Experiment 2A smoke is sane, run the powered 2A gate.
13. If powered 2A passes, run a small Experiment 2B cross-trace transfer probe.
```

## What Not To Do Yet

Do not add these until the powered Experiment 2A gate passes:

```text
Who&When predicted all_at_once / step_by_step / binary_search cards
Phase 2B predicted intervention point
full cross-trace main run
```

Do not start the expensive closed-loop runnable agent build until Experiment 2B shows transfer over
coarse/generic baselines.

Reason:

```text
If gold oracle_specific cards cannot beat coarse reflection or hard mismatch,
predicted attribution will be uninterpretable.
```

## Final Mandate

Design Experiment 2 so that the attribution-specific hypothesis can fail.

The target is not:

```text
Make oracle cards look good.
```

The target is:

```text
Try to explain away oracle card gains as coarse reflection or generic in-context nudging.
If oracle_specific still wins, the thesis becomes stronger.
If it does not, pivot the thesis toward generic failure memory or intervention-point selection.
```

This is the correct next step toward the larger paper:

```text
Failure attribution -> compact targeted memory -> improved future execution.
```
