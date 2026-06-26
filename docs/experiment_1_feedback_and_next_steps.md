# Experiment 1 Feedback and Next Steps

## 한 줄 결론

Experiment 1은 **Who&When gold intervention point에서 runtime Failure Card가 same-failure recurrence를 줄일 수 있는지**를 보는 첫 smoke로는 성공적이다.

다만 현재 결과는 아직 **attribution-specific downstream utility**를 입증하지 못한다. 가장 큰 이유는 `wrong_mismatched_card`가 `oracle_runtime_card`보다 더 잘 나왔기 때문이다.

## 현재 실험의 정확한 이름

현재 실험은 다음 이름이 가장 정확하다.

```text
Who&When Phase 2A Gold-Intervention Runtime Card Smoke
```

아직 다음 이름으로 부르면 안 된다.

```text
Who&When Predicted Attribution Downstream Utility Experiment
```

이유는 현재 pipeline에서 `phase0_method_reproduction`, `phase2b_predicted_intervention_repair`, `phase3_cross_trace_transfer`, `phase4_replayable_subset_rescue`가 모두 꺼져 있고, `all_at_once`, `step_by_step`, `binary_search` 같은 Who&When predicted attribution method output을 아직 downstream utility 조건에 넣지 않았기 때문이다.

## 리뷰에 대한 판단

다른 에이전트의 리뷰에 대체로 동의한다.

동의하는 핵심은 다음이다.

```text
1. PoC 방향은 맞다.
2. Who&When 기반 trace-prefix repair 구성은 적절하다.
3. gold-point oracle card upper-bound signal은 나왔다.
4. 그러나 wrong_mismatched_card control이 깨졌기 때문에 attribution-specific utility claim은 아직 불가능하다.
5. predicted Who&When method를 넣기 전에 mismatch/control 설계를 먼저 고쳐야 한다.
```

내 판단도 같다.

```text
PoC as gold-point trace-prefix repair: 성공적
Attribution-specific downstream utility: 아직 미입증
Predicted attribution utility: 아직 미실험
End-to-end rescue: 아직 미실험
```

## Experiment 1이 보여준 것

Experiment 1이 실제로 지지하는 claim은 이 정도다.

```text
Gold attribution-derived runtime cards can reduce same-failure recurrence at the decisive step.
```

한국어로는:

```text
정확한 Who&When gold attribution을 runtime Failure Card로 바꾸면,
gold decisive step 직전에서 같은 실패를 반복할 가능성을 줄일 수 있다.
```

현재 결과에서 긍정적인 신호는 분명하다.

```text
Pre-Phase2 no_guidance recurrence rate: 0.7111

Phase 2A:
no_guidance              success 0.1 / recurrence 0.9
strong_generic_guideline success 0.2 / recurrence 0.8
sanitized_raw_gold       success 0.3 / recurrence 0.6
oracle_runtime_card      success 0.6 / recurrence 0.2
```

즉 oracle card는 no guidance, generic guideline, sanitized raw gold explanation보다 좋았다.

## Experiment 1이 아직 보여주지 못한 것

다음 claim은 아직 지원되지 않는다.

```text
1. 정확한 attribution이 부정확한 attribution보다 downstream utility가 높다.
2. wrong attribution은 negative transfer를 만든다.
3. Who&When predicted attribution method output이 실제로 useful하다.
4. attribution accuracy가 card utility를 예측한다.
5. card가 cross-trace로 transfer된다.
6. original task가 end-to-end로 rescue된다.
```

특히 다음 문장은 현재 결과로는 쓰면 안 된다.

```text
Accurate attribution leads to better cards than inaccurate attribution.
```

현재까지는 더 보수적으로 이렇게 써야 한다.

```text
Oracle runtime cards show a positive upper-bound signal for gold-point trace-prefix repair,
but the current smoke does not establish attribution-specific utility.
```

## 가장 큰 문제: wrong_mismatched_card

Experiment 1의 가장 큰 경고 신호는 이 결과다.

```text
oracle_runtime_card   success 0.6 / recurrence 0.2
wrong_mismatched_card success 0.8 / recurrence 0.2
```

이 결과는 `wrong_mismatched_card`가 진짜 negative control로 작동하지 않았다는 뜻이다.

가능한 원인은 다음과 같다.

```text
1. 현재 runtime cards가 너무 broadly useful하다.
2. 많은 카드가 "검증하라", "근거를 확인하라", "제약을 확인하라" 같은 verification guidance로 수렴한다.
3. failure mode heuristic이 거칠어서 서로 다른 mode라고 해도 실제 intervention은 비슷할 수 있다.
4. selected cases의 failure modes가 충분히 orthogonal하지 않다.
5. mismatched card가 "틀린 카드"라기보다 "다른 유용한 generic card"로 작동했다.
```

따라서 Experiment 1의 해석은 다음처럼 좁혀야 한다.

```text
Runtime guidance can improve trace-prefix repair.
Oracle card is one strong version of such guidance.
But current controls do not yet prove that the improvement comes from attribution specificity.
```

## 다음 실험의 핵심 질문

Experiment 2의 질문은 다음으로 바뀌어야 한다.

```text
Attribution-specific Failure Cards가 broad guidance보다 더 도움이 되는가?
```

즉 단순히 oracle card 성능을 더 올리는 것이 목표가 아니다.

중요한 것은 다음을 분리하는 것이다.

```text
A. 그냥 verification guidance라서 좋아진 것인가?
B. Who&When attribution에서 나온 failure-specific card라서 좋아진 것인가?
```

## Experiment 2에서 고쳐야 할 것

### 1. stricter mismatched control

현재 mismatch는 너무 약하다. 다음 중 하나 이상을 넣어야 한다.

```text
hard_mismatched_card:
  target failure와 수동으로 orthogonal한 card 사용

irrelevant_same_format_card:
  Runtime Failure Card 형식은 유지하지만 현재 task/action에 적용 불가능한 card 사용

anti_helpful_card:
  명백히 잘못된 방향을 주는 card
  단, harmful instruction이 아니라 task-irrelevant or invalid check 수준으로 제한

wrong_when_card:
  card content는 맞지만 intervention point가 틀린 조건

wrong_who_card:
  card content는 맞지만 responsible agent가 틀린 조건
```

### 2. oracle card를 broad card와 분리

현재 `oracle_runtime_card`는 failure-mode level canned guidance에 가깝다. 다음 두 조건을 분리해야 한다.

```text
broad_failure_mode_card:
  "verify facts", "check constraints" 같은 mode-level guidance

narrow_oracle_runtime_card:
  leakage 없이 violated requirement pattern이나 missing check type을 더 구체화한 card
```

중요한 제한은 유지해야 한다.

```text
agent-visible card에 넣으면 안 되는 것:
- exact step number
- original failed action
- gold answer
- source evidence span
- "you failed at t*" 같은 표현
```

대신 넣을 수 있는 것은 다음이다.

```text
allowed:
- failure pattern category
- missing check type
- applicable role/action context
- do / do_not / check_before_next_action
- task-specific answer가 아닌 requirement pattern
```

### 3. case-level matrix 추가

Aggregate metric만으로는 부족하다. 다음 표가 필요하다.

```text
case_id
failure_mode
no_guidance result
generic result
raw_gold result
oracle result
mismatched result
notes
```

특히 다음 그룹을 분리해서 봐야 한다.

```text
oracle만 성공한 case
oracle과 wrong이 모두 성공한 case
wrong만 성공한 case
모든 조건이 실패한 case
모든 조건이 성공한 case
```

이 분석이 있어야 `wrong_mismatched_card`가 왜 강했는지 판단할 수 있다.

### 4. sample size 확장

다음 smoke는 최소 이 정도가 적절하다.

```text
30 failure-prone cases
× 5 conditions
× 3 attempts
= 450 generations
```

가능하면 다음 분석을 붙인다.

```text
paired case-level delta:
oracle - no_guidance
oracle - generic
oracle - raw_gold
oracle - mismatched

bootstrap confidence interval
paired permutation test
```

## 아직 predicted Who&When method를 넣지 않는 이유

바로 `all_at_once`, `step_by_step`, `binary_search`를 넣는 것은 이르다.

이유는 현재 control이 아직 불안정하기 때문이다.

```text
wrong_mismatched_card가 oracle보다 강한 상태에서 predicted card를 넣으면,
predicted card가 좋아도 attribution 때문인지 generic guidance 때문인지 해석이 꼬인다.
```

추천 순서는 다음이다.

```text
Experiment 1:
  Phase 2A gold-point smoke
  positive upper-bound signal 확인
  mismatch control 문제 발견

Experiment 2:
  stricter mismatch
  narrow oracle vs broad card 분리
  case-level matrix
  30 cases × 5 conditions × 3 attempts

Experiment 3:
  Who&When predicted attribution methods 추가
  all_at_once / step_by_step / binary_search card utility 비교

Experiment 4:
  Phase 2B predicted intervention point
  predicted who/when이 실제 개입 위치 선택에도 useful한지 평가
```

## Experiment 1의 논문상 위치

Experiment 1은 paper의 최종 evidence가 아니라 feasibility and upper-bound smoke로 두는 것이 맞다.

가능한 표현:

```text
As a first feasibility smoke, we test whether gold Who&When attributions can be converted into runtime cards that reduce recurrence at the gold decisive step.
```

피해야 할 표현:

```text
We show that attribution accuracy predicts downstream repair utility.
We show that predicted Who&When methods produce useful cards.
We show end-to-end task rescue.
```

## 최종 판단

Experiment 1은 실패한 실험이 아니다.

오히려 좋은 첫 결과다.

```text
1. Who&When-native trace-prefix repair pipeline이 실제로 돈다.
2. no-guidance recurrence가 충분히 높아 effect를 측정할 수 있다.
3. oracle runtime card가 no-guidance/raw/generic보다 좋은 signal을 보인다.
4. 동시에 mismatched control 문제가 드러나 다음 실험 설계 방향이 명확해졌다.
```

따라서 다음 단계의 목표는 oracle 성능을 더 크게 만드는 것이 아니라, 다음 질문에 답하는 것이다.

```text
이 개선은 단순 broad verification guidance 때문인가,
아니면 attribution-specific Failure Card 때문인가?
```
