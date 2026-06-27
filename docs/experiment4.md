# Experiment 4: Cross-Trace Transfer Lite

## 상태

```text
status: planned
type: transfer smoke
scope: Who&When trace-prefix transfer under oracle retrieval
prerequisite: Experiment 3 abstraction stress test should pass or be at least non-collapsed
```

Experiment 4는 Experiment 3가 통과했을 때 실행하는 작은 transfer probe다.

단, Experiment 3 결과에 따라 Experiment 4의 형태가 달라진다.

```text
Exp3 result: oracle_abstracted > mode_only > broad
  Run Experiment 4 as abstract failure-memory transfer.

Exp3 result: mode_only ~= oracle_abstracted > broad
  Redesign Experiment 4 as mode-routing / retrieval transfer.

Exp3 result: oracle_abstracted ~= broad
  Do not run Experiment 4 yet. Inspect renderer and broad baseline first.
```

목표는 same-trace repair가 아니라 reusable failure memory 가능성을 확인하는 것이다.

## 실험 목표

핵심 질문:

```text
source failed trace에서 만든 abstract Failure Card가
held-out target trace의 유사 실패도 줄이는가?
```

즉:

```text
local repair -> reusable memory
```

로 넘어가는 첫 실험이다.

## 왜 필요한가

Experiment 2A/3는 같은 trace의 gold decisive point에서 card를 주입한다.

이것은 중요한 unit test지만, 여전히 다음 비판을 받는다.

```text
그 실패를 보고 그 지점을 고친 것 아닌가?
미래 실행에 쓸 수 있는 memory라는 증거는 어디 있나?
```

Experiment 4는 이 비판을 줄이기 위한 cross-trace transfer smoke다.

## Claim Boundary

이 실험은 oracle retrieval upper bound다.

```text
source와 target을 gold failure-mode label로 pairing한다.
```

따라서 성공해도 다음을 주장하면 안 된다.

```text
agent가 스스로 올바른 memory를 retrieve했다.
deployable retrieval이 해결됐다.
end-to-end task rescue가 됐다.
```

가능한 표현:

```text
Under oracle retrieval of same-mode source memories,
abstract attribution-derived cards transfer to held-out target trace prefixes.
```

## 데이터 구성

target은 no-guidance recurrence pretest를 통과한 failure-prone case여야 한다.

```text
target condition:
  no_guidance same_failure_recurrence_rate >= 0.4
```

source-target pairing:

```text
source_case_id != target_case_id
source_failure_mode == target_failure_mode
avoid near-duplicate tasks if possible
```

hard mismatch pairing:

```text
mismatched_source_failure_mode orthogonal to target_failure_mode
source_case_id != target_case_id
```

## Transfer Unit

literal task detail은 transfer unit이 아니다.

```text
bad transfer unit:
  "프랑스 인구 값을 검증하라"

good transfer unit:
  "최신 factual claim을 final answer 전에 외부 source와 대조하라"
```

Experiment 4에서 transfer되는 것은 다음이어야 한다.

```text
failure-mode pattern
+ missing check type
+ abstract corrective action
```

주의:

```text
이 실험은 reusable memory 실험인 동시에
right failure-mode routing vs wrong failure-mode routing 실험일 수 있다.
```

따라서 mode-only condition을 넣어야 한다. 그래야 source card의 transfer 효과가:

```text
1. 올바른 failure mode retrieval 때문인지
2. missing-check/action abstraction 때문인지
```

분리된다.

## 조건

기본 6조건:

```text
1. no_guidance
2. coarse_reflection_from_source
3. broad_verification_card
4. raw_source_explanation
5. source_mode_only_placebo
6. source_oracle_abstracted_card
7. source_hard_mismatched_abstracted_card
```

Exp3 결과가 `mode_only ~= oracle_abstracted`라면 조건 이름과 claim을 바꾼다.

```text
primary condition:
  source_mode_only_placebo

research question:
  Does oracle failure-mode retrieval/routing transfer across traces?

not:
  Does rich abstract memory content transfer?
```

선택 조건:

```text
7. full_source_failure_context
```

`full_source_failure_context`를 넣으면 token-normalized utility를 같이 본다.

```text
utility_per_1k_tokens =
  repair_lift / input_token_count
```

## 조건 정의

### no_guidance

target prefix에 아무 memory도 넣지 않는다.

### coarse_reflection_from_source

과거 유사 실패가 있었다는 coarse signal만 준다.

금지:

```text
who
when
why
source mistake_reason
source failed action
```

### broad_verification_card

case-무관 generic card다.

목적:

```text
card format + generic nudge 효과 통제
```

### raw_source_explanation

source failure의 sanitized explanation을 prose로 제공한다.

목적:

```text
structured card가 raw explanation보다 나은지 확인
```

### source_oracle_abstracted_card

source gold attribution에서 만든 abstract card를 target에 주입한다.

핵심 조건이다.

단, 이 card는 Experiment 3의 renderer contract와 manipulation check를 통과한 renderer로 만들어야 한다.

```text
required:
  failure-mode pattern
  missing check type
  abstract corrective action

forbidden:
  source literal entity
  source answer
  source original failed action
  source exact step
```

### source_mode_only_placebo

source의 올바른 failure mode만 알려주는 card-shaped placebo다.

목적:

```text
source_mode_only - broad_verification:
  oracle retrieval / mode routing 단독 가치

source_oracle_abstracted - source_mode_only:
  missing-check/action abstraction의 추가 transfer 가치
```

이 조건이 높게 나오면, 논문 방향은 다음처럼 바뀔 수 있다.

```text
failure attribution is useful mainly as retrieval/routing signal,
not necessarily as rich memory content.
```

### source_hard_mismatched_abstracted_card

orthogonal source에서 만든 abstract card를 target에 주입한다.

목적:

```text
right memory vs wrong memory 비교
```

## 실행 규모

처음에는 lite smoke로 충분하다.

```text
target cases:
  10-12 failure-prone target traces

conditions:
  6

attempts:
  2

generations:
  10-12 × 7 × 2 = 140-168
```

Exp3에서 mode-only가 핵심으로 드러나면 조건을 줄인다.

```text
mode-routing transfer smoke:
  no_guidance
  broad_verification_card
  source_mode_only_placebo
  source_hard_mismatched_mode_only

generations:
  10-12 × 4 × 2 = 80-96
```

## Metrics

핵심 metric:

```text
transfer_specificity_lift =
  repair_rate(source_oracle_abstracted_card)
  - max(
      repair_rate(coarse_reflection_from_source),
      repair_rate(broad_verification_card),
      repair_rate(source_hard_mismatched_abstracted_card)
    )
```

mode-routing decomposition:

```text
transfer_mode_routing_lift =
  repair_rate(source_mode_only_placebo)
  - repair_rate(broad_verification_card)

transfer_abstract_action_lift =
  repair_rate(source_oracle_abstracted_card)
  - repair_rate(source_mode_only_placebo)
```

recurrence:

```text
transfer_recurrence_lift =
  recurrence_rate(source_hard_mismatched_abstracted_card)
  - recurrence_rate(source_oracle_abstracted_card)
```

negative transfer:

```text
paired_negative_transfer_vs_no_guidance =
  P(no_guidance succeeds and card condition fails)
```

추가 관찰:

```text
source_oracle_abstracted_card vs raw_source_explanation
source_oracle_abstracted_card vs full_source_failure_context
utility_per_1k_tokens if full context is included
```

## Go / No-Go

### Strong signal

```text
source_oracle_abstracted_card > broad_verification_card
source_oracle_abstracted_card > source_mode_only_placebo
source_oracle_abstracted_card > source_hard_mismatched_abstracted_card
source_oracle_abstracted_card > coarse_reflection_from_source
same-failure recurrence도 source_oracle_abstracted_card가 더 낮음
```

해석:

```text
Failure Card가 reusable failure memory로 작동할 가능성이 있다.
```

다음 단계:

```text
powered Experiment 3/4 설계
또는 runnable closed-loop mini-benchmark 설계
```

### Soft signal

```text
source_oracle_abstracted_card > no_guidance
but source_oracle_abstracted_card ~= broad_verification_card
```

해석:

```text
failure memory는 유용하지만, attribution-specific transfer인지는 약하다.
```

### Mode-routing signal

```text
source_mode_only_placebo > broad_verification_card
source_oracle_abstracted_card ~= source_mode_only_placebo
```

해석:

```text
attribution의 transfer 가치는 rich memory content보다
어떤 failure mode memory를 retrieve/apply할지 정하는 routing signal에 가까울 수 있다.
```

다음 단계:

```text
retrieval/routing experiment로 pivot
label-free failure-mode retrieval 설계
closed-loop에서는 memory content보다 intervention target/mode selection을 변수화
```

다음 단계:

```text
abstraction schema 재설계
failure mode를 더 좁게 나눔
retrieval/routing value로 thesis pivot 고려
```

### No-go

```text
source_oracle_abstracted_card ~= no_guidance
or source_hard_mismatched_abstracted_card >= source_oracle_abstracted_card
```

해석:

```text
same-trace repair는 되지만 reusable memory로 transfer되지 않을 수 있다.
```

가능한 pivot:

```text
1. Who&When-native track을 local repair benchmark로 축소
2. runnable closed-loop benchmark로 무게중심 이동
3. attribution의 가치를 memory content가 아니라 intervention targeting / routing에서 찾음
```

## 구현 요구사항

```text
1. source-target pairing table 생성
2. target_case_id, source_case_id, source_failure_mode, target_failure_mode 저장
3. near-duplicate flag 저장
4. Experiment 3 결과에 따라 transfer framing 선택
5. source_oracle_abstracted_card renderer 재사용
6. source_mode_only_placebo 조건 추가
7. source_hard_mismatched_abstracted_card selector 구현
8. oracle retrieval upper bound caveat를 report에 자동 기록
9. manipulation check와 leakage audit를 source cards에 enforcing 적용
10. case-level paired matrix 출력
11. paired negative transfer metric 추가
```

## 산출물

```text
docs/experiment4.md
who_when_card_poc/data/interim/exp4_source_target_pairs.csv
who_when_card_poc/data/runs/exp4_transfer_lite_inputs.jsonl
who_when_card_poc/data/runs/exp4_transfer_lite_generations.jsonl
who_when_card_poc/data/judgments/exp4_transfer_lite_judgments.jsonl
who_when_card_poc/reports/exp4_transfer_lite_summary.md
```

## 최종 해석 경계

Experiment 4가 성공하면 말할 수 있는 것:

```text
Under oracle retrieval, abstract attribution-derived cards can transfer across Who&When trace prefixes.
```

아직 말하면 안 되는 것:

```text
The agent self-improves end-to-end.
The agent retrieves the right memory by itself.
Predicted attribution is sufficient.
Original tasks are rescued.
```
