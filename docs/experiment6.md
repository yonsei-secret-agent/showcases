# Experiment 6 Plan: Dynamic Binding Check Probe

## Status

Planned. This is the last proposed experiment before writing the report.

Do not implement until the plan is reviewed. Do not tune another prose card
before this experiment.

## Role In The Report

Experiment 6 is the final test of where attribution utility actually lives.

The previous tau2 experiments showed that precise attribution rendered as
runtime prose memory did not reliably separate from generic reminders. The next
question is not whether to write a better card. The next question is whether
the same attribution signal becomes useful when it is converted into a
**binding control-flow intervention**.

Report-facing question:

```text
Is failure attribution useful as advisory prose, or only when it creates a
binding post-condition check that the agent cannot ignore?
```

Exp6 should let the report end with a clear mechanism claim:

```text
1. precision matters when enforced as a validator,
2. binding matters but precision does not, or
3. neither prose nor binding is sufficient in this tau2 setting.
```

## Why This Experiment Exists

The tau2 prose-memory arc produced a consistent pattern:

```text
Exp5.3:
  runtime memory was live, but oracle prose did not beat generic cleanly.

Exp5.4:
  broad tool-completion prose backfired; narrow v1 signal was driven by a small
  retention subset.

Exp5.5:
  cheap gate showed no usable specificity gradient; current pool was too thin
  and noisy for a powered prose-memory run.
```

The shared limitation is that all of these interventions were advisory:

```text
task starts
system prompt contains runtime memory
agent may follow or ignore it
```

Exp6 changes the intervention form:

```text
agent attempts final response
harness checks a post-condition
if the check fails, finalization is blocked once and the agent must continue
```

This tests whether attribution is weak because the information is unhelpful, or
because advisory prose is the wrong interface.

## Central Question

```text
Does precise failure-attribution-derived information improve tau2 fresh retry
success when used as a binding finalization check rather than as prose memory?
```

## Hypotheses

### H_binding

```text
Any binding finalization gate improves over no_gate on recoverable
communication/check omission tasks.
```

If true, the important lever is intervention strength:

```text
advisory prompt < binding control-flow check
```

### H_precision

```text
oracle_precise_binding_gate improves over coarse_binding_gate,
mode_only_binding_gate, and wrong_precise_binding_gate.
```

If true, precise attribution is useful because it generates better validators
or post-conditions, not because it writes better prose cards.

## Claim Boundary

Exp6 can support:

```text
In tau2 retail fresh retries, attribution-derived post-condition checks can
improve success when enforced before final response.
```

Exp6 is still an oracle upper-bound experiment:

```text
The gate is derived from audited failure attribution, not from a predicted
attributor. A positive result means "precise attribution can be useful if it is
available and enforced," not that the system can already infer that attribution
online.
```

Exp6 cannot support:

```text
1. predicted attribution utility
2. multi-agent who utility
3. general tau2 improvement across all failure modes
4. cross-task memory transfer
5. closed-loop self-improvement
```

Important single-agent caveat:

```text
tau2 still tests why/when-style task-failure information in a single-agent
setting. It does not test the MAS "who" dimension. If Exp6 is positive, the
next major arc is who/when-targeted binding intervention in a multi-agent
setting.
```

## Intervention Timing

The binding check should fire only at attempted finalization:

```text
agent returns an AssistantMessage with no tool calls
```

It should not fire:

```text
1. before the first tool call
2. after every tool call
3. on intermediate user/tool messages
4. during policy lookup or ordinary reasoning turns
```

Rationale:

```text
The tau2 failure mode we are probing is omitted final communication or missed
final check after partial progress. Pre-finalization is the narrowest point that
matches the observed mechanism while avoiding broad prompt contamination.
```

## Binding Mechanism

For gated conditions, wrap the tau2 agent with a `BindingGateAgent`.

Behavior:

```text
1. Generate the next assistant message normally.
2. If the message contains tool calls, pass it through unchanged.
3. If the message is a final user-facing response, run the configured gate.
4. If the gate passes, pass the final response through.
5. If the gate fails and the retry budget is unused, do not expose the final
   response to the user. Instead append a synthetic feedback message and let
   the agent continue.
6. If the gate fails after the retry budget is used, pass the final response
   through and record gate_failed_after_retry.
```

Primary setting:

```text
max_gate_rejections = 1
```

Reason:

```text
One rejection is enough to test whether a binding check changes behavior while
limiting unnatural interaction loops.
```

Synthetic feedback format:

```text
<binding_check_feedback>
Your final response is missing a required completion check. Continue the task
and satisfy the missing requirement before finalizing.
</binding_check_feedback>
```

The feedback text must be condition-specific only through the gate type. It
must not reveal exact answer values, order IDs, product IDs, or tool arguments.

## Reward-Rubric Circularity Guard

Binding gates create a new version of the judge-card circularity risk observed
in earlier Who&When experiments.

Failure mode:

```text
oracle gate criterion = tau2 NL_ASSERTION rubric restated as a blocking check
```

If this happens, a GREEN result would mean the harness optimized directly for
the benchmark evaluator, not that attribution produced an actionable
self-improvement signal.

Rules:

```text
1. derive every oracle gate from the diagnosed failure pattern, not by reading
   the tau2 reward rubric backward
2. prefer presence checks over correctness checks
3. never require the exact answer value in the gate
4. never require exact tool arguments, IDs, or evaluator labels
5. label the experiment as an oracle-attribution upper bound
```

Safe example:

```text
Check that the final response contains two separate money summaries.
```

Unsafe example:

```text
Check that the final response contains the exact refund total required by the
NL_ASSERTION evaluator.
```

Presence checks intentionally avoid proving answer correctness. The official
tau2 reward still determines whether the answer is actually correct. This keeps
the gate from becoming a hidden copy of the evaluator.

## Gate Types

All gated arms use the same control-flow machinery. Only the check and feedback
specificity differ.

### 1. no_gate

No finalization gate. This is standard tau2 execution.

### 2. coarse_binding_gate

Generic finalization gate.

Example gate criterion:

```text
The final response must appear to address all parts of the user's request.
```

Example feedback:

```text
Your response may not cover every requested outcome. Re-check the user's
request and continue if any required result, status, amount, count, or
explanation is missing.
```

Purpose:

```text
Tests whether binding intervention alone helps, without precise attribution.
```

### 3. mode_only_binding_gate

Failure-family gate, but no task-specific post-condition.

Example gate criterion:

```text
The final response must include the required user-facing amount, count,
tracking number, status, comparison, or item detail when the task asks for one.
```

Example feedback:

```text
This task has a missing-required-communication risk. Before finalizing, check
whether the response must include an amount, count, tracking number, status,
comparison, or item detail.
```

Purpose:

```text
Separates precise attribution from broad failure-mode routing.
```

### 4. oracle_precise_binding_gate

Attribution-derived post-condition for the specific task.

Example gate criterion:

```text
The final response must include both the refund total and the remaining-order
total after the relevant tool actions.
```

Example feedback:

```text
Your response is missing a required money-summary check. Continue until the
completed tool evidence supports both required totals, then finalize.
```

Allowed information:

```text
1. required result type
2. required communication/check category
3. abstract relation among completed actions and final response
4. whether the check depends on tool evidence
```

Forbidden information:

```text
1. exact answer values
2. order IDs, item IDs, product IDs, payment IDs
3. exact tool arguments
4. original failed response text
5. gold evaluator labels
```

Purpose:

```text
Tests whether precise attribution becomes useful when transformed into a
binding verifier/post-condition.
```

### 5. wrong_precise_binding_gate

Same format and strength as `oracle_precise_binding_gate`, but with an
orthogonal wrong post-condition.

Example:

```text
Target task needs a refund-total communication.
Wrong gate checks for a tracking-number communication.
```

Purpose:

```text
Tests whether the effect is correct attribution specificity rather than merely
being blocked and asked to continue.
```

## Gate Implementation Options

Use the cheapest reliable gate first.

### Option A: Rule-Based Presence Gate

Use deterministic text checks for expected categories:

```text
contains a dollar amount
contains a count
contains a tracking-like token
mentions required status words
mentions both compared options
```

Pros:

```text
cheap, reproducible, no LLM judge circularity
```

Cons:

```text
limited semantic coverage; may miss paraphrases
```

### Option B: Card-Blind LLM Gate

Use an LLM classifier that sees:

```text
task text
final response
allowed abstract gate criterion
```

It must not see:

```text
card text
original failed trace
gold answer values
condition name
```

Pros:

```text
handles paraphrases and task-specific wording
```

Cons:

```text
adds judge variance; must be logged and audited
```

Recommended initial implementation:

```text
Use rule-based presence gates as the primary circularity-safe implementation
where possible.
Use LLM gates only for criteria that cannot be checked with simple text
patterns, and report them as a sensitivity analysis rather than the cleanest
evidence.
Always report which gate type was used per task.
```

## Task Pool

Do not reuse the Exp5.5C pool as-is.

Harvest a fresh pool from tau2 retail using the target inclusion criteria.

### Inclusion Criteria

MUST:

```text
1. baseline/no_gate often reaches a final response but misses a required
   communication/check
2. DB/tool side is feasible under the model at least some of the time
3. the missing requirement can be checked without leaking exact answer values
4. a finalization block could plausibly allow recovery
5. task is not already saturated under no_gate
6. task is not all-condition unwinnable in a cheap probe
7. oracle gate can express a non-leaky post-condition that is more specific
   than mode_only but less specific than the exact solution
```

SHOULD:

```text
1. required result is explicit in the user request
2. required result type is easy to identify: amount, count, tracking number,
   status, comparison, item detail
3. official reward contains a user-facing assertion component
4. wrong gate can be made genuinely orthogonal
5. task has a compound or non-obvious requirement where precision can matter
   beyond "include the required amount/count/status"
```

### Exclusion Criteria

Exclude:

```text
1. exact tool-argument failures
2. policy/evaluator conflict tasks
3. tasks that require giving the exact answer in the gate to be recoverable
4. tasks where no short non-leaky post-condition can be written
5. tasks that pass no_gate almost always
6. tasks that fail every gate in a small harvest probe
7. single obvious communication tasks where mode_only and oracle would be
   equivalent by construction
```

### Size

Harvest:

```text
20-30 candidate retail tasks
```

Final pool:

```text
6-8 clean tasks
```

If fewer than 5 clean tasks are found:

```text
stop and report that this tau2 retail failure surface is too thin for a
binding-check conclusion.
```

## Experimental Design

### Phase 6A: Harness Smoke

Purpose:

```text
Verify that the gate actually intercepts attempted final responses and can
force a continuation without corrupting tau2 execution.
```

Use:

```text
1-2 known tasks
2 conditions: no_gate, coarse_binding_gate
2 seeds
```

Success criteria:

```text
1. no_gate reproduces normal tau2 execution
2. gate triggers only on final responses
3. rejected final responses are not treated as user-visible final answers
4. agent can continue after feedback
5. official reward is still computed from the final transcript
```

Do not interpret Phase 6A as research evidence.

### Phase 6B: Pool Harvest

Run cheap baseline probes:

```text
20-30 candidate tasks
x no_gate
x 2-3 seeds
```

Then run a minimal recoverability probe on likely candidates:

```text
candidate tasks that show final communication/check omission
x coarse_binding_gate
x 1-2 seeds
```

Purpose:

```text
no_gate tells us that the task fails.
coarse_binding_gate tells us whether blocking finalization can plausibly
recover the failure without destroying the task.
```

Classify each task:

```text
clean communication/check omission
DB/tool failure
saturated success
all-fail
evaluator/policy conflict
exact-answer/tool-argument dominated
```

Select only clean tasks for Phase 6C.

Prefer tasks with compound requirements:

```text
two required money summaries
tracking number plus item/status detail
comparison across two options
amount plus status/action confirmation
```

Do not fill the pool with single-obvious-count or single-obvious-tracking tasks
where `mode_only_binding_gate` already says everything the oracle can say
without leaking the answer.

### Phase 6C: Binding Check Main Probe

Recommended scale:

```text
6-8 clean tasks
x 5 conditions
x 5 seeds
= 150-200 runs
```

Conditions:

```text
no_gate
coarse_binding_gate
mode_only_binding_gate
oracle_precise_binding_gate
wrong_precise_binding_gate
```

If variability remains high:

```text
increase seeds only if the pool has at least 6 clean tasks
otherwise keep the run descriptive and do not claim a powered result
```

## Metrics

Primary:

```text
official success rate
oracle_precise_binding_gate - mode_only_binding_gate
oracle_precise_binding_gate - coarse_binding_gate
oracle_precise_binding_gate - wrong_precise_binding_gate
```

Primary safety watch:

```text
DB regression rate relative to no_gate
DB regression rate after a gate rejection
```

Reason:

```text
A binding gate can raise NL_ASSERTION while causing extra tool calls that break
DB state. If this happens, Exp6 would merely reproduce the Exp5 pattern
NL-up/DB-down in a stronger intervention form.
```

Mechanism:

```text
gate_trigger_rate
gate_pass_rate
rejected_final_to_success_rate
success_rate_given_gate_trigger
success_rate_given_no_gate_trigger
DB mean
NL_ASSERTION mean
DB regression rate
NL rescue rate
false_positive_gate_rate
max_rejection_exhausted_rate
```

Trigger-frequency confound:

```text
coarse gates may fire more often than oracle gates.
wrong gates may fire on irrelevant missing details.
```

Therefore, report both:

```text
1. overall condition success rate
2. conditional success among runs where the gate fired
```

This prevents interpreting "more opportunities to retry" as specificity.

Task-level:

```text
strict task wins
oracle-only rescue tasks
coarse-only rescue tasks
wrong-gate success tasks
all-condition failure tasks
```

Report all metrics by task, not only aggregate.

## Decision Rules

### GREEN: Precision Bites Under Binding

Criteria:

```text
oracle_precise_binding_gate beats no_gate by the calibrated practical margin
oracle_precise_binding_gate beats coarse_binding_gate by the calibrated
  practical margin
oracle_precise_binding_gate beats mode_only_binding_gate by the calibrated
  practical margin
oracle_precise_binding_gate beats wrong_precise_binding_gate by the calibrated
  practical margin
oracle advantage appears on more than one task
wrong gate does not match oracle
oracle does not increase DB regression beyond the calibrated safety band
oracle advantage is not explained solely by a higher gate_trigger_rate
```

Interpretation:

```text
Precise attribution is useful when converted into binding post-condition
checks. The report should pivot from "Failure Cards" to "Failure Attribution as
Verifier Generation."
```

Next after report:

```text
test predicted attribution-derived gates
then test routing which gate to apply
then test MAS who/when-targeted binding interventions
```

### YELLOW: Binding Works, Precision Does Not Separate

Criteria:

```text
coarse/mode/oracle gates improve over no_gate
but oracle_precise_binding_gate does not beat coarse or mode_only
DB regression remains controlled
```

Interpretation:

```text
The active ingredient is binding finalization control, not precise attribution
content.
```

Report conclusion:

```text
Precise prose memory and precise binding content both fail to separate from
coarse controls in this tau2 setting. Future attribution work should focus on
when/where/who to gate, not richer content.
```

### RED: Binding Does Not Help

Criteria:

```text
all binding gates are within the calibrated uncertainty band of no_gate
or gates cause substantial DB/NL regression
or wrong gate matches/exceeds oracle
```

Interpretation:

```text
This tau2 retail rescue surface does not support the runtime intervention
thesis under the tested models and tasks.
```

Report conclusion:

```text
The PoC found no reliable downstream utility for attribution-as-prose or
attribution-as-binding-check in tau2 retail. The remaining promising direction
is MAS-specific who/when targeted intervention, not single-agent tau2 memory.
```

### STOP: Pool Too Thin

Criteria:

```text
fewer than 5 clean binding-check tasks are found
```

Interpretation:

```text
Do not force an underpowered run. Report that the target failure family was too
thin in the tau2 retail harvest, and use the existing experiments as the final
evidence for the report.
```

## Leakage and Validity Audits

Before Phase 6C:

```text
1. audit every oracle gate for exact answer leakage
2. audit every wrong gate for orthogonality
3. audit every coarse/mode gate for format and strength parity
4. verify that oracle gate contains more information than mode_only but less
   than exact solution
5. verify that the gate criterion can be checked without benchmark labels
6. verify that the gate criterion is derived from the diagnosed failure pattern,
   not copied from the tau2 reward rubric
```

For each task, store:

```text
task_id
failure_family
gate_condition
gate_criterion
feedback_text
forbidden_terms_checked
leakage_flags
gate_type: rule_based | llm_classifier
expected_nonleaky_signal
```

If a task has no valid information band:

```text
drop it from precision analysis or classify it as mode-routing evidence only.
```

## Implementation Notes

Existing code already supports static runtime prose memory through
`RuntimeMemoryAgent`. Exp6 needs a new dynamic wrapper rather than more system
prompt injection.

Likely implementation path:

```text
1. add BindingGateAgent subclass of LLMAgent
2. override generate_next_message
3. call the base generation
4. if assistant message has tool_calls, return unchanged
5. if assistant message is final text, evaluate gate
6. if gate fails and retry remains, append synthetic feedback to state and
   generate again
7. log every gate decision in simulation info or sidecar report
```

Open implementation risks:

```text
1. tau2 message schema must accept synthetic feedback without breaking replay
2. official evaluator must see only the final transcript that tau2 can replay
3. gate rejection should not create invalid tool-message ordering
4. repeated gate rejection must terminate cleanly
```

These risks are why Phase 6A exists.

## Report Integration

Exp6 should be the final experimental chapter before the report.

Report arc:

```text
1. Who&When trace-prefix repair:
   attribution-derived guidance can locally change behavior, but same-trace
   gold intervention has narrow claim boundaries.

2. Who&When specificity/abstraction:
   literal and judge-coupled signals are fragile; abstraction weakens the
   specificity claim.

3. tau2 prose memory:
   fresh execution and official reward are live, but precise prose memory does
   not separate from generic/coarse reminders.

4. Exp6 binding check:
   final test of whether attribution needs to be enforced as a verifier rather
   than injected as prose.

5. Final recommendation:
   choose among verifier-generation, binding-without-precision, or closing the
   tau2 runtime intervention track and moving to MAS who-targeted intervention.
```

## Expected Outcome

Most likely:

```text
YELLOW
```

Reason:

```text
Binding finalization checks may help recover omitted final communications, but
the coarse or mode-only gates may capture much of the benefit.
```

This is still a useful endpoint. It would show that the main lever is not
writing more precise prose, but changing the intervention from advice to
control flow.

## One-Sentence Mandate

```text
Stop tuning prose cards; test whether failure attribution becomes useful only
when it creates a binding finalization check that the agent cannot ignore.
```
