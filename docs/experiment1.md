# Experiment 1: Who&When Gold-Point Runtime Card Smoke

## 상태

```text
status: completed
type: Who&When-native trace-prefix repair smoke
scope: gold attribution, gold intervention point, same-trace repair
```

Experiment 1은 최종 self-improving agent 실험이 아니라, 그 전에 필요한 **local repair unit test**다.

## 실험 목표

Who&When의 gold failure attribution을 runtime Failure Card로 변환했을 때, gold decisive error step 직전에서 에이전트가 같은 실패를 반복하지 않도록 만들 수 있는지 확인한다.

핵심 목표는 다음이다.

```text
Failure attribution -> Failure Card -> next-action behavior change
```

즉, 실패 원인 분석이 단순 post-hoc label에 그치지 않고 다음 행동을 바꿀 수 있는지 보는 첫 검증이다.

## 해소하려는 질문

Experiment 1이 답하려는 질문:

```text
Gold Who&When attribution에서 만든 runtime card가
gold decisive step에서 same-failure recurrence를 줄이는가?
```

Experiment 1이 답하지 않는 질문:

```text
1. predicted Who&When attribution도 유용한가?
2. 정확한 attribution이 부정확한 attribution보다 더 유용한가?
3. card가 held-out trace나 future task에 transfer되는가?
4. agent가 스스로 실패를 분석하고 memory로 저장해 발전하는가?
5. original task가 end-to-end로 rescue되는가?
```

## 실험 구상

Who&When failed trajectory를 사용한다.

각 case에서 다음 정보를 사용한다.

```text
question
history
mistake_agent
mistake_step
mistake_reason
system_prompt
```

실험 단위는 전체 task rerun이 아니라 `mistake_step` 직전 prefix다.

```text
trajectory prefix before t*
-> condition-specific guidance 주입
-> responsible agent의 next action 재생성
-> judge가 same-failure recurrence / repair success 판정
```

## 조건

Experiment 1의 조건은 다음 5개였다.

```text
1. no_guidance
2. strong_generic_guideline
3. sanitized_raw_gold_explanation
4. oracle_runtime_card
5. wrong_mismatched_card
```

각 조건의 의도:

```text
no_guidance:
  아무 guidance 없이 같은 prefix에서 next action 생성.

strong_generic_guideline:
  강한 일반 실행 지침. 검증, 제약 확인, 불확실성 처리 등을 권장.

sanitized_raw_gold_explanation:
  gold mistake_reason을 leakage 제거 후 prose 형태로 제공.

oracle_runtime_card:
  gold mistake_reason에서 failure mode를 추론해 runtime card로 변환.

wrong_mismatched_card:
  다른 case에서 만든 runtime card를 target case에 주입.
```

## 실행 과정

### 1. Who&When data audit

Who&When local clone에서 JSON trace를 읽고 case index를 만들었다.

주요 확인 항목:

```text
mistake_step 유효성
mistake_agent와 해당 step agent 일치 여부
prefix 길이
system_prompt 존재 여부
Phase 2A 구조적 적격성
```

보수적인 smoke pool은 다음 기준으로 잡았다.

```text
dataset_type == algorithm_generated
mistake_step >= 2
phase2a_status == candidate
history_len <= 10
```

### 2. Pre-Phase2 recurrence pretest

카드 효과를 보려면 no-guidance baseline이 실제로 같은 실패를 반복해야 한다.

그래서 먼저 no-guidance regeneration을 수행했다.

```text
candidate cases: 15
repeats per case: 3
generation records: 45
judge records: 45
errors: 0
```

failure-prone threshold:

```text
same_failure_recurrence_rate >= 0.4
```

관찰:

```text
11 / 15 candidate cases passed the failure-prone threshold.
```

그중 10개 case를 Phase 2A smoke에 사용했다.

### 3. Phase 2A failure-prone smoke

```text
cases: 10
conditions: 5
generation records: 50
judge records: 50
errors: 0
```

judge는 generation condition을 직접 보지 않고, original task, prefix, gold diagnostic information, candidate next action을 보고 JSON으로 판정했다.

## 관찰된 과정

Pre-Phase2에서 no-guidance recurrence가 충분히 높았다.

```text
no_guidance recurrence_rate = 0.7111
```

즉, baseline이 같은 실패를 안정적으로 반복하는 case를 선별할 수 있었다.

Phase 2A에서는 oracle card가 no-guidance, generic guideline, raw gold explanation보다 좋은 성능을 보였다.

하지만 wrong/mismatched card도 매우 강하게 작동했다.

이 현상은 Experiment 1의 가장 중요한 관찰이다.

## 결과

### Pre-Phase2 recurrence pretest

| condition | n | repair_success_rate | same_failure_recurrence_rate | mean_score |
| --- | ---: | ---: | ---: | ---: |
| no_guidance | 45 | 0.2889 | 0.7111 | 1.4222 |

### Phase 2A failure-prone smoke

| condition | n | repair_success_rate | same_failure_recurrence_rate | mean_score |
| --- | ---: | ---: | ---: | ---: |
| no_guidance | 10 | 0.1 | 0.9 | 1.1 |
| strong_generic_guideline | 10 | 0.2 | 0.8 | 1.3 |
| sanitized_raw_gold_explanation | 10 | 0.3 | 0.6 | 1.5 |
| oracle_runtime_card | 10 | 0.6 | 0.2 | 2.2 |
| wrong_mismatched_card | 10 | 0.8 | 0.2 | 2.6 |

## 결과 해석

### 긍정적 해석

Experiment 1은 다음 claim을 지지한다.

```text
Gold attribution-derived runtime cards can reduce same-failure recurrence
at the gold decisive step.
```

한국어로는:

```text
정확한 Who&When gold attribution을 runtime card로 바꾸면,
gold decisive step에서 같은 실패를 반복할 가능성을 줄일 수 있다.
```

특히 oracle card는 no-guidance 대비:

```text
repair_success_rate: 0.1 -> 0.6
same_failure_recurrence_rate: 0.9 -> 0.2
```

로 개선됐다.

### 부정적 / 제한적 해석

Experiment 1은 attribution-specific utility를 입증하지 못했다.

가장 큰 이유:

```text
wrong_mismatched_card success 0.8 > oracle_runtime_card success 0.6
```

이는 `wrong_mismatched_card`가 진짜 negative control로 작동하지 않았다는 뜻이다.

가능한 원인:

```text
1. 현재 runtime cards가 너무 broadly useful하다.
2. 많은 카드가 "검증하라", "근거를 확인하라", "제약을 확인하라"로 수렴한다.
3. selected cases가 unverified factual claim 계열에 많이 쏠렸다.
4. failure mode heuristic이 거칠어 mismatch가 실제로 orthogonal하지 않았다.
5. wrong card가 "틀린 card"가 아니라 "다른 generic verification nudge"로 작동했다.
```

따라서 Experiment 1의 안전한 결론은 다음이다.

```text
Runtime guidance can improve trace-prefix repair.
Oracle card is one strong version of such guidance.
But Experiment 1 does not prove that the improvement comes from attribution specificity.
```

## 논문상 위치

Experiment 1은 최종 evidence가 아니라 feasibility / upper-bound smoke다.

가능한 표현:

```text
As a first feasibility smoke, we test whether gold Who&When attributions can be converted into
runtime cards that reduce recurrence at the gold decisive step.
```

피해야 할 표현:

```text
We show that attribution accuracy predicts downstream repair utility.
We show that predicted Who&When methods produce useful cards.
We show end-to-end task rescue.
We show self-improving agents.
```

## 다음 결정

Experiment 1 이후 다음 실험은 predicted attribution method가 아니라 specificity gate여야 한다.

다음 질문:

```text
정확한 attribution에서 나온 card가
coarse reflection, broad verification nudge, hard mismatched card보다 좋은가?
```

이 질문이 Experiment 2의 출발점이다.

## 관련 문서와 산출물

Tracked docs:

```text
docs/who_when_phase2a_smoke_results.md
docs/experiment_1_feedback_and_next_steps.md
```

Generated local artifacts:

```text
who_when_card_poc/reports/pre_phase2_recurrence_summary.md
who_when_card_poc/reports/phase2a_failure_prone_summary_v2.md
who_when_card_poc/data/runs/pre_phase2_recurrence_generations.jsonl
who_when_card_poc/data/runs/phase2a_failure_prone_generations.jsonl
who_when_card_poc/data/judgments/pre_phase2_recurrence_judgments.jsonl
who_when_card_poc/data/judgments/phase2a_failure_prone_judgments_v2.jsonl
```
