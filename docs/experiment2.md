# Experiment 2: Specificity Gate and Reusable Failure Memory Probe

## 상태

```text
status: planned
type: next experiment spec
scope: attribution specificity gate, then small cross-trace transfer probe
```

Experiment 2는 아직 실행 전이다.

이 문서는 실행자가 바로 구현할 수 있도록 목표, 질문, 조건, 관찰 항목, 판정 기준, 결과 기록 템플릿을 정리한다.

## 실험 목표

Experiment 2의 목표는 oracle card 성능을 더 높이는 것이 아니다.

목표는 다음을 구별하는 것이다.

```text
H_specific:
  정확한 failure attribution에서 온 memory/card라서 도움이 된다.

H_nudge:
  그냥 "조심해라", "검증해라"라는 generic in-context nudge라서 도움이 된다.
```

즉, Experiment 2는 다음 질문에 답해야 한다.

```text
정밀한 who/when/why failure attribution은
coarse reflection보다 더 좋은 self-improvement memory를 만드는가?
```

## 해소하려는 질문

주요 질문:

```text
oracle_specific_card가 coarse_reflection, broad_verification_card,
hard_mismatched_card보다 decisive-step repair에 더 효과적인가?
```

보조 질문:

```text
1. raw gold explanation보다 structured Failure Card가 좋은가?
2. generic verification nudge만으로도 대부분 설명되는가?
3. wrong/mismatched memory가 여전히 도움이 되는가?
4. failure-mode를 stratify하면 mismatch control이 정상화되는가?
5. source failure에서 만든 memory가 held-out target failure에 transfer되는가?
```

## Experiment 1에서 이어지는 문제

Experiment 1에서는 다음 결과가 나왔다.

```text
oracle_runtime_card   success 0.6 / recurrence 0.2
wrong_mismatched_card success 0.8 / recurrence 0.2
```

즉, oracle card가 no-guidance보다 좋았지만 wrong/mismatched card도 더 좋았다.

이 결과는 다음을 의미한다.

```text
현재 card effect는 attribution-specific effect라기보다
broad verification nudge effect일 수 있다.
```

Experiment 2는 이 문제를 정면으로 다룬다.

## 실행 전 Must-Fix

Experiment 2A를 돌리기 전에 반드시 고칠 항목은 세 가지다.

```text
1. Shared base prompt에서 "failed trajectory" 표현 제거
2. oracle_runtime_card를 mode-level generic card가 아니라 oracle_specific_card로 교체
3. hard_mismatched_card를 자동 "다른 mode" 선택이 아니라 orthogonal pairing으로 설계
```

### 1. Base Prompt Contamination 제거

Experiment 1의 공통 prompt는 모든 condition에 다음 정보를 암시했다.

```text
You are continuing a failed multi-agent trajectory from a prefix.
```

이러면 `no_guidance`도 이미 "이 trajectory는 실패했다"는 coarse failure signal을 받는다. Experiment 2에서는 `coarse_reflection`이 별도 baseline이므로, failure awareness는 condition별 guidance에만 들어가야 한다.

공통 prompt는 다음처럼 바꾼다.

```text
Before:
You are continuing a failed multi-agent trajectory from a prefix.

After:
You are continuing a multi-agent trajectory from a prefix.
```

이 변경의 결과로 Experiment 1에서 고른 failure-prone subset은 더 이상 그대로 유효하지 않다.

```text
neutral base prompt로 no_guidance recurrence pretest를 다시 실행하고
failure-prone subset을 재선정해야 한다.
```

anti-leakage instruction은 모든 condition에 동일하게 유지한다. 그래야 "benchmark label을 말하지 말라" 같은 안전 문구가 condition별 신호가 되지 않는다.

### 2. Oracle Specificity 강화

`oracle_specific_card`는 기존 `oracle_runtime_card`처럼 failure-mode canned template만 반환하면 안 된다.

gold `mistake_reason`에서 다음 정보를 case-specific but non-leaky하게 추출해야 한다.

```text
violated requirement pattern
missing check type
risky next-action pattern
concrete check_before_next_action
```

### 3. Hard Mismatch 강화

`hard_mismatched_card`는 inferred failure mode가 다른 case를 자동 선택하는 것만으로는 부족하다.

target failure와 corrective action이 orthogonal해야 한다.

예:

```text
target: constraint omission
mismatch: web navigation drift card

target: unsupported fabricated data
mismatch: premature finalization card
```

구현에서는 hard mismatch fallback을 제거해야 한다.

```text
허용하지 말 것:
  orthogonal source를 못 찾으면 자동으로 다음 case 또는 임의 case를 사용

허용할 것:
  pairing table에 없으면 record를 생성하지 않거나 manual review로 보냄
```

## 전체 구상

Experiment 2는 두 부분으로 구성한다.

```text
Experiment 2A:
  Same-trace specificity gate.
  Gold decisive step에서 oracle_specific_card가 generic/coarse/hard-mismatch보다 좋은지 확인.

Experiment 2B:
  Cross-trace transfer probe.
  한 failed trace에서 만든 card가 다른 held-out trace에도 도움이 되는지 확인.
```

Experiment 2A powered gate가 통과하지 못하면 Experiment 2B와 predicted attribution 실험으로 넘어가지 않는다.

## Experiment 2A: Specificity Gate

### 조건

Smoke 기본 조건은 6개다.

```text
1. no_guidance
2. coarse_reflection
3. broad_verification_card
4. sanitized_raw_gold_explanation
5. oracle_specific_card
6. hard_mismatched_card
```

각 조건의 의미:

```text
no_guidance:
  아무 guidance 없음.
  실패했다는 사실도 알려주지 않음.

coarse_reflection:
  Reflexion 스타일 coarse prompt.
  이전 시도가 실패했다는 정보는 주지만 who/when/why attribution은 주지 않음.

broad_verification_card:
  Runtime Failure Card 형식은 맞추되 내용은 case-무관 generic verification nudge.
  "사실 검증", "제약 재확인", "근거 없는 가정 금지" 등.

sanitized_raw_gold_explanation:
  gold mistake_reason을 leakage 제거 후 prose로 제공.
  card structure 없이 raw explanation만 주는 baseline.

oracle_specific_card:
  gold attribution에서 도출한 case-specific but non-leaky card.
  violated requirement pattern, missing check type, risky next-action pattern 포함.

hard_mismatched_card:
  같은 포맷과 유사한 길이를 유지하지만 target failure와 orthogonal한 source failure에서 만든 card.
  진짜로 target prefix에 적용되기 어려워야 함.
```

선택적 추가 조건:

```text
oracle_mode_card_current:
  Experiment 1의 기존 mode-level oracle card.

length_matched_placebo_card:
  card 형식/길이/salience 효과 통제용.

full_failed_trace_context:
  full context ICL baseline.
```

`full_failed_trace_context`는 "큰 context를 그대로 주면 되지 않나?"라는 ICL baseline이다.

해석은 다음처럼 한다.

```text
oracle_specific_card > full_failed_trace_context:
  매우 강한 결과. 구조화된 attribution memory가 raw ICL memory보다 낫다.

oracle_specific_card ~= full_failed_trace_context with far fewer tokens:
  좋은 결과. Failure Card는 compact self-improvement memory다.

full_failed_trace_context > oracle_specific_card:
  반드시 실패는 아니다. full trace ICL이 강한 upper bound라는 뜻이며,
  token-normalized utility와 retrieval cost를 같이 봐야 한다.
```

optional로 이 조건을 넣을 경우 다음 metric을 추가한다.

```text
utility_per_1k_tokens =
  repair_lift / input_token_count
```

## 카드 설계

### oracle_specific_card

목표:

```text
case-specific하지만 leakage 없는 Failure Card.
```

필드:

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

허용되는 정보:

```text
- failure pattern category
- violated requirement pattern
- missing check type
- role/action context
- forward-looking do / do_not / check_before_next_action
- final answer를 노출하지 않는 task-specific requirement pattern
```

금지되는 정보:

```text
- exact mistake_step
- original failed action text
- gold answer
- evidence span from the failed action
- "you failed at step N" 같은 표현
- benchmark label
```

### broad_verification_card

목표:

```text
generic nudge ceiling 측정.
```

특징:

```text
case, task, role, failure mode, gold attribution을 언급하지 않는다.
card 구조와 길이는 oracle_specific_card와 최대한 맞춘다.
```

### hard_mismatched_card

목표:

```text
right attribution vs wrong attribution 비교.
```

Experiment 1처럼 "다른 inferred failure mode" 정도로는 부족하다.

가능한 orthogonal pairing:

```text
target fabricated data -> mismatch navigation drift card
target unverified factual claim -> mismatch routing/handoff card
target constraint violation -> mismatch premature finalization card
target premature finalization -> mismatch table constraint card
target navigation drift -> mismatch numerical verification card
```

가능하면 pairing table을 남긴다.

```text
target_case_id
target_failure_mode
mismatch_source_case_id
mismatch_failure_mode
why_orthogonal
```

## Case Selection

Experiment 1의 한계 중 하나는 failure-mode monoculture였다.

Experiment 2에서는 stratified selection이 필요하다.

목표 failure-mode buckets:

```text
unsupported assumption / fabricated data
unverified factual claim
constraint or format violation
premature finalization
navigation drift / irrelevant action
handoff or routing error
```

Smoke 규모:

```text
20 candidate cases for no-guidance pretest
10-12 failure-prone cases selected for main smoke
at least 3-4 failure-mode buckets represented
2 attempts per condition
```

Main 규모:

```text
50-60 candidate cases for no-guidance pretest
30 failure-prone cases selected for main run
5-6 failure-mode buckets represented
3 attempts per condition
```

algorithm-generated case가 부족하면 hand-crafted subset을 제한적으로 허용한다.

단, 다음 metadata를 반드시 남긴다.

```text
dataset_type
has_system_prompt
history_len
role_reconstruction_method
```

## Judge 변경

Experiment 2의 judge는 의도 표명과 구체 행동을 분리해야 한다.

추가 필드:

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

repair_success 조건:

```text
task_progress == true
avoids_decisive_error == true
negative_transfer == false
and, when verification is required, verification_is_concrete == true
```

다음과 같은 답변은 성공으로 세지 않는다.

```text
I will verify this later.
I should be careful.
I need to check the facts.
```

단, 실제로 source request, recalculation, constraint list check, routing to correct agent/tool 같은 구체 행동을 수행하거나 즉시 착수하면 성공 후보가 될 수 있다.

의도와 행동은 분리해서 기록한다.

```text
"검증해야 한다"고 말만 함:
  states_relevant_intent = true
  performs_concrete_repair_action = false
  repair_success = false

필요한 evidence를 요청하거나 제약 목록을 실제로 점검함:
  performs_concrete_repair_action = true
```

## 관찰할 과정

Experiment 2A에서 관찰할 것:

```text
1. no-guidance가 여전히 recurring failure를 만드는가?
2. coarse_reflection이 얼마나 회복시키는가?
3. broad_verification_card가 oracle_specific_card와 비슷한가?
4. hard_mismatched_card가 정말 target case에 안 먹히는가?
5. oracle_specific_card가 어떤 failure mode에서만 강한가?
6. judge가 "검증하겠다"는 말만 한 candidate를 성공으로 과대평가하지 않는가?
```

Experiment 2B에서 관찰할 것:

```text
1. source card가 held-out target trace에서도 도움이 되는가?
2. same-mode source card가 mismatched-source card보다 좋은가?
3. cross-trace transfer가 특정 failure mode에만 나타나는가?
4. transfer card가 target task에 negative transfer를 만들지는 않는가?
```

## 결과 기록 템플릿

### Experiment 2A summary

| condition | n | repair_success_rate | same_failure_recurrence_rate | mean_score | negative_transfer_rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| no_guidance | TBD | TBD | TBD | TBD | TBD |
| coarse_reflection | TBD | TBD | TBD | TBD | TBD |
| broad_verification_card | TBD | TBD | TBD | TBD | TBD |
| sanitized_raw_gold_explanation | TBD | TBD | TBD | TBD | TBD |
| oracle_specific_card | TBD | TBD | TBD | TBD | TBD |
| hard_mismatched_card | TBD | TBD | TBD | TBD | TBD |

### Specificity metrics

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

### Case-level matrix

| case_id | failure_mode | attempt | no_guidance | coarse_reflection | broad_verification | raw_gold | oracle_specific | hard_mismatch | notes |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Qualitative buckets:

```text
oracle_only_success
oracle_and_mismatch_success
mismatch_only_success
nudge_only_success
all_success
all_failure
```

## Go / No-Go 기준

실행 전에 기준을 고정하되, smoke와 powered run을 구분한다.

Experiment 2A smoke는 통계적 확증용이 아니다.

```text
smoke purpose:
  방향성 확인
  baseline contamination 제거 확인
  hard_mismatched_card가 oracle보다 다시 좋아지는 참사 재발 여부 확인
  powered run에 투자할지 결정
```

따라서 smoke에서 `+10%p` 같은 작은 차이를 strong evidence로 해석하지 않는다. 10-12 cases × 2 attempts에서는 비율 차이의 불확실성이 크다.

실제 gate는 powered run에서만 적용한다.

```text
powered run target:
30 failure-prone cases
× 6 conditions
× 3 attempts
≈ 90 judgments per condition
paired bootstrap CI 또는 paired permutation test 포함
```

Primary contrast:

```text
nudge_gap =
  repair_rate(oracle_specific_card)
  - repair_rate(broad_verification_card)
```

이 contrast가 primary인 이유는 `oracle_specific_card`와 `broad_verification_card`가 같은 card format을 공유하므로, card format/salience 효과를 더 잘 통제하기 때문이다. `oracle_specific_card - coarse_reflection`은 여전히 중요하지만, prose reflection vs card format 차이가 섞인다.

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
and still beats hard_mismatched_card
```

해석:

```text
Failure memory는 도움이 되지만 card specificity가 아직 부족하다.
card renderer를 개선하고 재실험한다.
```

Powered no-go:

```text
oracle_specific_card ~= broad_verification_card
or hard_mismatched_card >= oracle_specific_card
```

해석:

```text
현재 효과는 attribution-specific memory가 아니라 generic ICL/reflection/nudge일 가능성이 크다.
predicted Who&When method로 넘어가지 않는다.
```

중요한 해석 경계:

```text
Experiment 2A는 kill-gate이지 confirmation result가 아니다.
2A 통과는 transfer 실험으로 갈 자격을 뜻할 뿐이다.
reusable failure memory에 대한 첫 강한 증거는 Experiment 2B부터 나온다.
```

## Experiment 2B: Cross-Trace Transfer Probe

Experiment 2A powered gate가 통과하면 작은 cross-trace transfer probe를 실행한다.

목표:

```text
source failure에서 만든 card가 held-out target failure에도 도움이 되는지 확인.
```

Experiment 2B의 전제는 transfer 단위를 명확히 정의하는 것이다.

```text
transfer unit:
  failure-mode pattern
  + missing check type
  + abstract corrective action
```

literal task detail은 transfer unit이 아니다.

예:

```text
bad transfer unit:
  "프랑스 인구 값을 검증하라"

good transfer unit:
  "최신 factual claim을 final answer 전에 외부 source와 대조하라"
```

즉, `oracle_specific_card`는 same-trace에서는 case-specific할 수 있지만, cross-trace transfer에서는 task answer나 literal entity가 아니라 추상화된 failure pattern과 check type이 남아야 한다.

구조:

```text
source failed trace
-> source oracle_specific_card
-> held-out target trace prefix
-> target next-action regeneration
-> target repair / recurrence judgment
```

조건:

```text
1. no_guidance
2. coarse_reflection_from_source
3. broad_verification_card
4. source_oracle_specific_card
5. source_hard_mismatched_card
6. raw_source_explanation
```

pairing:

```text
source_failure_mode == target_failure_mode
source_case_id != target_case_id
```

mismatch:

```text
source_failure_mode orthogonal to target_failure_mode
```

측정:

```text
transfer_repair_rate
transfer_recurrence_rate
source_card_vs_coarse_reflection
source_card_vs_broad_verification
source_card_vs_mismatched_source
negative_transfer_rate
```

Experiment 2B가 성공하면 처음으로 다음 표현을 조심스럽게 사용할 수 있다.

```text
Failure Card as reusable failure memory.
```

## 결과 해석 계획

### Strong go가 나오는 경우

해석:

```text
정확한 attribution에서 나온 specific card는 generic ICL/reflection보다 더 좋은 repair signal이다.
```

다음 단계:

```text
1. Experiment 2A smoke였다면 powered run으로 확장
2. Experiment 2A powered gate가 통과했다면 Experiment 2B cross-trace transfer
3. 2B에서 transfer가 broad/generic baseline을 이기면 predicted Who&When attribution method 추가
```

### Soft go가 나오는 경우

해석:

```text
Failure memory는 유용하지만 현재 card가 attribution-specific하다는 증거는 약하다.
```

다음 단계:

```text
1. oracle_specific_card renderer 개선
2. failure-mode stratification 재검토
3. hard mismatch pairing 재검토
4. judge rubric audit
```

### No-go가 나오는 경우

해석:

```text
정밀 attribution보다 coarse reflection 또는 broad verification nudge가 충분할 수 있다.
```

가능한 pivot:

```text
1. thesis를 attribution-specific card에서 generic failure memory로 이동
2. attribution의 가치를 card content가 아니라 intervention point selection에서 찾기
3. failure attribution은 memory content보다 retrieval/routing signal이라는 방향 검토
```

## 이후 로드맵

Experiment 2 이후 전체 로드맵:

```text
Experiment 1:
  Gold-point trace-prefix repair smoke.
  완료.

Experiment 2:
  Specificity gate + small cross-trace transfer probe.
  다음 단계.

Experiment 3:
  Predicted card content utility.
  gold who/when은 고정하고, all_at_once / step_by_step / binary_search의 predicted why/card만 비교.

Experiment 4:
  Runnable closed-loop self-improving agent.
  Experiment 2B transfer가 broad/generic baseline을 이긴 뒤에만 큰 엔지니어링으로 진행.
  먼저 oracle memory로 fail -> attribute -> card memory -> retry / held-out improvement 확인.

Experiment 5:
  Predicted intervention point.
  predicted who/when으로 어디에 누구에게 개입해야 하는지 평가.
```

## 관련 문서

```text
docs/experiment1.md
docs/experiment_2_specificity_and_transfer_plan.md
docs/experiment_1_feedback_and_next_steps.md
docs/who_when_phase2a_smoke_results.md
```
