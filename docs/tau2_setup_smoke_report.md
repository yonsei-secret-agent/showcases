# tau2-bench Setup Smoke Report

## Status

```text
date: 2026-06-27
benchmark: sierra-research/tau2-bench
commit: 8ebb749
domain: retail
model:
  agent: gpt-4.1-mini
  user: gpt-4.1-mini
temperature:
  agent: 0
  user: 0
seed: 300
```

## What Was Verified

```text
1. tau2-bench cloned under third_party/tau2-bench.
2. uv sync completed for core text-mode dependencies.
3. uv run tau2 check-data passed.
4. retail text-mode run works with the existing local OpenAI key.
5. results.json can be parsed by tau2_card_poc.results_io.
6. tau2_card_poc can register a runtime-memory LLMAgent wrapper.
7. same-task retry can be run through a reusable memory runner.
```

## One-Task Smoke

Command shape:

```bash
uv run tau2 run \
  --domain retail \
  --agent-llm gpt-4.1-mini \
  --user-llm gpt-4.1-mini \
  --agent-llm-args '{"temperature": 0}' \
  --user-llm-args '{"temperature": 0}' \
  --num-trials 1 \
  --num-tasks 1 \
  --max-concurrency 1 \
  --seed 300 \
  --timeout 300 \
  --save-to retail_smoke_001
```

Result:

```text
task 0:
  final reward: 1.0
  DB: 1.0
  NL_ASSERTION: 1.0
  agent cost: about $0.0075
  user cost: about $0.0018
```

## Five-Task Baseline Probe

Command shape:

```bash
uv run tau2 run \
  --domain retail \
  --agent-llm gpt-4.1-mini \
  --user-llm gpt-4.1-mini \
  --agent-llm-args '{"temperature": 0}' \
  --user-llm-args '{"temperature": 0}' \
  --num-trials 1 \
  --num-tasks 5 \
  --max-concurrency 1 \
  --seed 300 \
  --timeout 300 \
  --save-to retail_probe_5_once
```

Result summary:

| task_id | reward | DB | NL_ASSERTION | observed failure |
| --- | ---: | ---: | ---: | --- |
| 0 | 1.0 | 1.0 | 1.0 | none |
| 1 | 0.0 | 0.0 | 1.0 | missed required write action / DB state mismatch |
| 2 | 0.0 | 1.0 | 0.0 | communicated 12 available t-shirt options instead of 10 |
| 3 | 0.0 | 1.0 | 0.0 | communicated 12 available t-shirt options instead of 10 |
| 4 | 0.0 | 0.0 | 0.0 | DB state mismatch and communicated 12 instead of 10 |

Aggregate:

```text
success: 1 / 5
failure: 4 / 5
average reward: 0.2
average agent cost: about $0.0093
average user cost: about $0.0021
```

## Immediate Interpretation

This is a useful pilot setting.

```text
1. Baseline failures are easy to harvest with gpt-4.1-mini on retail.
2. Several failures are actionably attributable.
3. Tasks 2-4 show a repeated failure pattern:
   the agent counts all product variants instead of only available variants.
4. Task 1 shows a different DB/write failure pattern.
```

This is enough to justify implementing a small retry-memory runner.

## Task 2 Sanity Retry

After the five-task probe, task 2 was rerun once without memory and once with a hand-written oracle-style memory card.

The card did not include the exact expected answer `10`.
It only stated the abstract corrective pattern:

```text
When counting product options, count only variants whose availability field
indicates that they are currently available.
Do not count unavailable variants as available options.
```

### No-Memory Retry

```text
task_id: 2
condition: no_memory_retry
reward: 0.0
DB: 0.0
NL_ASSERTION: 0.0
observed failure:
  agent again communicated 12 available t-shirt options instead of 10
  and failed the DB/write component.
```

### Oracle-Memory Retry

```text
task_id: 2
condition: oracle_memory_manual
reward: 0.0
DB: 1.0
NL_ASSERTION: 0.0
observed behavior:
  agent completed the return/write portion correctly
  but still communicated an incorrect available option count, saying 11 instead of 10.
```

Interpretation:

```text
This is not a clean final rescue.
It is a partial improvement:
  no_memory: DB 0.0, NL 0.0
  oracle_memory: DB 1.0, NL 0.0

The memory card changed behavior enough to fix the DB component,
but it did not reliably fix the counted-availability communication failure.
```

This is useful because it shows the tau2 setting is stricter than the Who&When proxy.

```text
The agent can receive a plausible attribution-derived card and still fail
unless the card is specific enough, the model follows it, and the official
task outcome is satisfied.
```

## Task 2 Paired Mini-Pilot

The first manual retry was then converted into a standard runner path:

```text
module:
  tau2_card_poc.memory_runner

mechanism:
  RuntimeMemoryAgent appends a <runtime_memory> block to the normal tau2
  LLMAgent system prompt.

important control:
  no_guidance and oracle_failure_card were rerun with the same task id,
  same model pair, and paired seeds 301 / 302 / 303.
```

Runtime memory used for the oracle condition:

```text
Failure Card: Count availability from explicit availability fields.
Before answering availability-count questions, inspect every product variant
and count only variants whose availability field says they are currently
available. Do not count variants that are listed in the catalog but marked
unavailable. If the task also requires a return or order update, complete
that required tool action after giving the corrected availability count.
```

This card is still an oracle upper-bound card.
It was written after inspecting the baseline failure pattern.
It does not contain the exact expected answer `10`, but it does encode the
specific missing check.

Paired official outcomes for the first two conditions:

| trial | seed | no_guidance reward | no_guidance DB | no_guidance NL_ASSERTION | oracle reward | oracle DB | oracle NL_ASSERTION |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 301 | 0.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 |
| 1 | 302 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 |
| 2 | 303 | 0.0 | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |

Aggregate:

```text
no_guidance:
  official success: 0 / 3
  average reward: 0.00
  DB success: 2 / 3
  NL_ASSERTION success: 0 / 3

oracle_failure_card:
  official success: 1 / 3
  average reward: 0.33
  DB success: 3 / 3
  NL_ASSERTION success: 1 / 3
```

Interpretation:

```text
This is a small positive rescue signal, not a stable result.

Positive:
  - no_guidance never solved task 2 under paired seeds.
  - oracle memory produced one full official success.
  - oracle memory improved DB reliability from 2/3 to 3/3.

Still weak:
  - oracle memory failed the final NL_ASSERTION in 2/3 attempts.
  - the dominant failure remains availability-count communication.
  - n=3 is only a sanity check and cannot support a paper claim.
```

Research implication:

```text
tau2 is a stricter and more useful next PoC than Who&When-only repair,
because the same card must satisfy the full task outcome, not just a local
judge criterion.

The result is sufficient to justify a slightly broader pilot,
but not sufficient to claim that attribution-derived cards reliably rescue
tasks.
```

## Task 2 Four-Condition Control Check

Two additional controls were added on the same paired seeds:

```text
generic_policy_checklist:
  a broad memory reminding the agent to verify facts, handle all user goals,
  and complete required order/account actions.

hard_mismatched_card:
  a cancellation-eligibility card that is intentionally orthogonal to the
  availability-count failure.
```

The condition set is still tiny, but it directly checks whether the oracle
result is just a generic memory-block effect.

Official outcomes:

| trial | seed | condition | reward | DB | NL_ASSERTION |
| ---: | ---: | --- | ---: | ---: | ---: |
| 0 | 301 | no_guidance | 0.0 | 1.0 | 0.0 |
| 0 | 301 | generic_policy_checklist | 0.0 | 1.0 | 0.0 |
| 0 | 301 | oracle_failure_card | 0.0 | 1.0 | 0.0 |
| 0 | 301 | hard_mismatched_card | 0.0 | 1.0 | 0.0 |
| 1 | 302 | no_guidance | 0.0 | 0.0 | 0.0 |
| 1 | 302 | generic_policy_checklist | 0.0 | 1.0 | 0.0 |
| 1 | 302 | oracle_failure_card | 0.0 | 1.0 | 0.0 |
| 1 | 302 | hard_mismatched_card | 0.0 | 1.0 | 0.0 |
| 2 | 303 | no_guidance | 0.0 | 1.0 | 0.0 |
| 2 | 303 | generic_policy_checklist | 0.0 | 1.0 | 0.0 |
| 2 | 303 | oracle_failure_card | 1.0 | 1.0 | 1.0 |
| 2 | 303 | hard_mismatched_card | 0.0 | 0.0 | 0.0 |

Aggregate:

```text
no_guidance:
  official success: 0 / 3
  DB success: 2 / 3
  NL_ASSERTION success: 0 / 3

generic_policy_checklist:
  official success: 0 / 3
  DB success: 3 / 3
  NL_ASSERTION success: 0 / 3

oracle_failure_card:
  official success: 1 / 3
  DB success: 3 / 3
  NL_ASSERTION success: 1 / 3

hard_mismatched_card:
  official success: 0 / 3
  DB success: 2 / 3
  NL_ASSERTION success: 0 / 3
```

Interpretation:

```text
This is the first tau2 signal that the specific missing-check card can rescue
an official task outcome in a fresh environment.

The signal is still weak:
  - it is one task only;
  - it uses an oracle upper-bound card;
  - success depends on 1 of 3 seeds;
  - generic memory improved DB reliability but did not fix the NL assertion;
  - the dominant availability-count failure remains hard for gpt-4.1-mini.

What it does show:
  - no_guidance and generic memory did not solve the task under these paired
    seeds;
  - the hard mismatched card did not accidentally solve the task;
  - the oracle card produced one full task-level rescue under the official
    tau2 evaluator.
```

This is enough for a team-facing PoC signal, but not enough for a research
claim. The next stage should broaden across tasks before making any general
statement.

Next retry experiment should include:

```text
1. no_memory_retry
2. generic_policy_checklist
3. oracle_failure_card
4. wrong_or_mismatched_card

and should report component-level transitions:
  DB fail -> DB success
  NL fail -> NL success
  final reward fail -> final reward success
```

## Important Caveats

The five-task probe is not a stable-failure set yet.

```text
Each task was run only once.
The next baseline harvest should run each candidate task at least 3 times.
```

The current retail tasks use `DB + NL_ASSERTION` in `reward_basis`.

```text
NL_ASSERTION is still a judged component,
but it is task-outcome oriented and does not see the Failure Card text.
It is less circular than the Who&When repair judge,
but not the same as a purely programmatic DB-only metric.
```

## Next Step

Implement a retry runner that can inject a memory/card into the agent system prompt.

Initial target:

```text
task_id: 2 or 3
failure pattern:
  count only available product variants before communicating options

conditions:
  no_memory_retry
  generic_policy_checklist
  oracle_failure_card
  wrong_or_mismatched_card
```
