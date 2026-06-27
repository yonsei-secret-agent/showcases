# Experiment 5.3: tau2 20-Case Fresh Rescue Gate

## 상태

```text
status: selected_tasks_ready
type: runnable rescue pilot
benchmark: tau2-bench retail
target scale: 20 selected tasks x 4 conditions x 3 seeds
```

## 실험 목표

Experiment 5.3은 tau2 retail에서 **실패하던 task가 attribution-derived memory/card로 fresh retry에서 성공하는지**를 본다.

핵심 질문:

```text
oracle single-missing-check card가
no memory, generic memory, hard mismatched memory보다
official tau2 reward를 더 많이 올리는가?
```

이 실험은 Who&When prefix repair와 다르다.

```text
Who&When:
  failed trajectory prefix에서 next action repair를 LLM judge로 평가

tau2:
  fresh environment에서 task를 다시 실행하고 official reward로 평가
```

## 선행 조건

Experiment 5.3은 Experiment 5.2 완료 후에만 실행한다.

필요 산출물:

```text
1. 20 selected rescue tasks
2. baseline traces for annotation
3. per-task oracle single-missing-check card
4. per-task hard mismatched card
5. leakage audit result
```

## 조건

조건 수는 의도적으로 4개로 제한한다.

```text
1. no_memory
2. generic_policy_card
3. oracle_single_missing_check_card
4. hard_mismatched_card
```

조건을 더 늘리지 않는 이유:

```text
현재 필요한 판단은 oracle이 generic/mismatch/no-memory보다 나은가 하나다.
coarse reflection, raw explanation, predicted attribution은 다음 gate로 미룬다.
```

## Card 규칙

### oracle_single_missing_check_card

반드시 하나의 attributed missing-check만 담는다.

허용:

```text
count only variants whose availability field is currently available
verify refund eligibility against policy before issuing store credit
confirm the requested order item before mutating the order
```

금지:

```text
exact answer value
exact tool arguments
full solution procedure
multiple unrelated repair instructions
generic checklist bundled with the oracle check
```

중요:

```text
task 2 pilot의 card는 availability count check와 return/write completion을 함께 담았다.
Experiment 5.3에서는 이런 번들을 금지한다.
```

### hard_mismatched_card

target failure와 직교해야 한다.

금지:

```text
verify evidence
check policy
complete all user goals
double-check tool arguments
```

이런 문장은 대부분의 task에 도움이 되므로 hard mismatch가 아니다.

좋은 mismatch 예:

```text
target:
  available product count communication failure

mismatch:
  cancellation window eligibility for pending orders
```

## 실행 구성

```text
selected tasks: 20
conditions: 4
seeds: 501, 502, 503
model:
  agent: gpt-4.1-mini
  user: gpt-4.1-mini
max steps: 200
```

총 실행 수:

```text
20 tasks x 4 conditions x 3 seeds = 240 runs
```

Template manifest:

```text
tau2_card_poc/experiments/exp5_3_rescue_20_template.json
```

## Selected 20-Task Set

Experiment 5.2 produced 24 candidate tasks with at least two baseline failures.
For Experiment 5.3, use the following 20:

```text
1, 2, 3, 4, 7, 16, 19, 20, 27, 28,
34, 36, 41, 71, 95, 98, 99, 103, 104, 112
```

Selection rule:

```text
include:
  - stable failures when they are actionable and not obviously ambiguous
  - mixed tasks when they add failure-type diversity
  - no more than 3 availability-count tasks

exclude:
  - 109, 110, 111 because they form a similar multi-update cluster with
    possible evaluator/policy tension
  - 33 because it is a weaker mixed WFH/address case covered more cleanly
    by task 34
```

Approximate distribution:

```text
availability-count / communication:
  2, 3, 4

refund / price / calculation communication:
  16, 19, 28, 95

exchange / product-variant selection:
  1, 7, 27, 98, 99

address, profile, order mutation, and multi-action DB updates:
  20, 34, 36, 41, 71, 103, 104, 112
```

Stability mix:

```text
stable baseline failures:
  2, 3, 4, 20, 27, 28, 34, 41, 71, 98, 103, 104

mixed but useful diversity cases:
  1, 7, 16, 19, 36, 95, 99, 112
```

This is intentionally not all stable failures. The stable-failure pool is
heavily weighted toward DB/write mutation tasks, so adding mixed tasks is
necessary to avoid a one-mode rescue pilot.

최종 실행 전에는 template을 복사해 task/card를 채운다.

```text
tau2_card_poc/experiments/exp5_3_rescue_20.json
```

## Primary Metrics

```text
official_success_rate
mean_reward
DB success rate
COMMUNICATE success rate
NL_ASSERTION success rate
paired rescue rate:
  no_memory fails and oracle succeeds on same task/seed
paired negative transfer:
  no_memory succeeds and card condition fails on same task/seed
oracle_vs_generic_delta
oracle_vs_mismatch_delta
```

## 결과 해석

GREEN:

```text
oracle_single_missing_check_card가
no_memory, generic_policy_card, hard_mismatched_card보다
여러 task와 여러 failure type에서 우세하다.
```

AMBIGUOUS:

```text
oracle ~= generic

해석:
  failure memory는 도움이 될 수 있지만,
  attribution-specific 효과인지 generic memory 효과인지 아직 불분명하다.
```

RED:

```text
oracle ~= no_memory
or hard_mismatched >= oracle

해석:
  task 2 seed 303 rescue는 특정 task/seed 효과였을 가능성이 높다.
```

## Claim Boundary

성공해도 가능한 claim:

```text
On a 20-case tau2 retail subset, oracle attribution-derived single-check cards
can improve fresh retry success over no-memory and generic/mismatched controls.
```

아직 주장하면 안 되는 것:

```text
predicted attribution이 충분하다.
agent가 스스로 failure attribution을 했다.
cross-task transfer가 된다.
multi-agent who attribution utility가 입증됐다.
closed-loop self-improvement가 완성됐다.
```
