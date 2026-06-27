# Experiment 5.2 Results: tau2 Retail Baseline Harvest

## 상태

```text
status: completed
date: 2026-06-27
domain: retail
candidate tasks: 30
trials per task: 3
total simulations: 90
agent model: gpt-4.1-mini
user model: gpt-4.1-mini
agent/user temperature: 0
save dir: third_party/tau2-bench/data/simulations/exp5_2_baseline_harvest_30
```

## 실행 중 발견한 문제와 수정

처음 실행은 인증 오류로 실패했다.

```text
error:
  Incorrect API key provided: <your_key_here>

root cause:
  실제 키는 who_when_card_poc/.env에 있었고,
  tau2 실행 디렉터리인 third_party/tau2-bench/.env에는 placeholder가 있었다.
```

수정:

```text
OPENAI_API_KEY, OPENROUTER_API_KEY, OPENAI_BASE_URL을
who_when_card_poc/.env에서 third_party/tau2-bench/.env로 동기화했다.
```

이후 1-task auth smoke를 실행했고, 인증 문제가 해결된 것을 확인했다.

```text
task_id: 2
reward: 0.0
DB: 1.0
NL_ASSERTION: 0.0
observed failure:
  agent again reported 12 t-shirt options instead of the expected 10.
```

30-task harvest는 처음 `max-concurrency=3`으로 시작했으나 OpenAI TPM rate limit이 발생했다.

```text
error:
  Rate limit reached for gpt-4.1-mini on tokens per min

fix:
  stop run
  resume same save directory with --auto-resume and --max-concurrency 1
```

concurrency 1에서는 안정적으로 완료됐다.

## Aggregate Result

```text
total simulations: 90
official success: 22 / 90
official success rate: 0.2444
mean reward: 0.2444
DB match: 33 / 90 = 0.3667
average cost per conversation: about $0.0115
total observed cost: about $1.2852
```

This is a good harvest result for the next rescue gate.

```text
baseline is not too easy:
  success rate is only 24.4%

baseline is not completely hopeless:
  several tasks are mixed, with 1/3 or 2/3 successes

failure modes are not monocultural:
  availability-count, DB/write, refund calculation, tracking communication,
  and multi-action modification failures all appear.
```

## Task Stability

```text
stable_failure: 15 tasks
mixed: 14 tasks
stable_success: 1 task
```

Stable failures:

```text
2, 3, 4, 20, 27, 28, 34, 41, 71, 98, 103, 104, 109, 110, 111
```

Mixed tasks:

```text
0, 1, 7, 14, 16, 19, 33, 36, 43, 56, 79, 95, 99, 112
```

Stable success:

```text
15
```

Tasks with at least 2 failures:

```text
2, 3, 4, 20, 27, 28, 34, 41, 71, 98, 103, 104, 109, 110, 111,
1, 7, 16, 19, 33, 36, 95, 99, 112
```

This gives a 24-task pool for selecting the 20-case rescue set.

## Component Patterns

Availability-count communication cluster:

```text
2:
  fail 3/3
  DB 1/3
  NL 0/3

3:
  fail 3/3
  DB 3/3
  NL 0/3

4:
  fail 3/3
  DB 3/3
  NL 0/3
```

Refund/calculation/communication cluster:

```text
16:
  fail 2/3
  DB 2/3
  NL 1/3

19:
  fail 2/3
  DB 3/3
  NL 1/3

28:
  fail 3/3
  DB 0/3
  NL 0/3

95:
  fail 2/3
  DB 2/3
  NL 1/3
```

DB/write/action mutation cluster:

```text
20, 27, 34, 41, 71, 98, 103, 104, 109, 110, 111
```

Some of these are strong candidates, but tasks `109`, `110`, and `111` show possible tension between policy/tool constraints and evaluator expectations. They should be audited before inclusion in the final 20-case rescue set.

## Interpretation

Experiment 5.2 succeeded as a baseline harvest.

It shows:

```text
1. tau2 retail has enough repeated failures under the chosen model setting.
2. A 20-case rescue set is feasible.
3. Failure diversity is sufficient for a stronger PoC than task-2-only.
4. The next experiment should not add more conditions yet.
   It should annotate and rescue this 20-case pool with the 4-condition design.
```

It does not show:

```text
1. failure cards improve success
2. oracle attribution is better than generic memory
3. predicted attribution works
4. cross-task transfer works
```

## Recommended Next Step

Create `Experiment 5.3` from the 24-task pool.

Recommended selection strategy:

```text
1. Include stable failures first.
2. Cap availability-count cluster at 3-4 tasks.
3. Include refund/calculation communication cases.
4. Include DB/write mutation cases with clear actionability.
5. Exclude or mark as low-confidence any task where evaluator expectation appears to conflict with tool/policy constraints.
```

Before running rescue:

```text
1. inspect baseline traces for selected tasks
2. write one oracle_single_missing_check_card per task
3. write one hard_mismatched_card per task
4. run leakage audit
5. fill tau2_card_poc/experiments/exp5_3_rescue_20.json
```

Only after these steps should the 20-case rescue gate be run.
