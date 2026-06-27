# Who&When Attribution-to-Intervention PoC Report

## Executive Summary

이 PoC의 목적은 Who&When 자체를 최종 benchmark로 삼는 것이 아니다.

목적은 다음 연구 아이디어가 실험 가능한 방향인지 빠르게 확인하는 것이다.

```text
agent trajectory에서 실패 원인을 귀인한다.
-> 그 귀인을 실행 가능한 guidance / memory로 변환한다.
-> 다음 실행에서 같은 실패를 줄이거나 성공률을 올릴 수 있는지 본다.
```

현재 결론은 다음과 같다.

```text
Go, but not on Who&When alone.
```

Who&When PoC는 다음을 보여줬다.

```text
1. Failed trajectory + gold attribution을 runtime intervention으로 변환하는 파이프라인은 구현 가능하다.
2. Gold attribution-derived guidance가 same-trace prefix에서 agent next action을 바꾸는 신호는 있다.
3. 하지만 그 신호는 LLM judge 설계와 proxy repair metric에 민감하다.
4. 따라서 최종 연구 증거는 rerunnable benchmark의 objective task success로 봐야 한다.
```

따라서 Who&When은 **diagnostic PoC / motivation**으로 유지하고, 다음 메인 실험은 기존 runnable benchmark 위에서 진행하는 것이 적절하다.

## Research Question

우리가 검증하려는 질문은 Failure Card 자체가 좋은 prompt인지가 아니다.

핵심 질문은 다음이다.

```text
Do trajectory-level failure attributions improve future agent execution?
```

더 구체적으로는:

```text
정밀한 who / when / why failure attribution은
coarse reflection이나 generic guideline보다 더 좋은 self-improvement signal인가?
```

이 질문은 기존 failure attribution benchmark의 방향을 downstream utility로 확장한다.

```text
기존 질문:
  Which agent caused the failure, and when?

우리 질문:
  If we know who failed, when, and why,
  can an agent use that information to avoid failing again?
```

## Why Who&When First

Who&When은 최종 success benchmark로는 부족하지만, PoC 출발점으로는 좋다.

이유:

```text
1. failed multi-agent trajectories가 이미 있다.
2. gold responsible agent, decisive step, explanation이 있다.
3. attribution -> intervention 변환을 빠르게 검증할 수 있다.
4. 새 benchmark를 만들지 않고 기존 attribution benchmark 위에서 출발할 수 있다.
```

하지만 Who&When-only는 위험하다.

```text
1. original task를 end-to-end로 rerun하기 어렵다.
2. official task success metric이 없다.
3. same-trace prefix repair는 clairvoyant intervention에 가깝다.
4. LLM judge proxy에 의존하면 card/judge circularity가 생길 수 있다.
```

따라서 Who&When의 역할은 다음으로 제한한다.

```text
Who&When:
  attribution-to-intervention pipeline feasibility
  local behavior-change diagnostic
  연구 방향 설득용 PoC

Not Who&When:
  final self-improvement evidence
  task success proof
  deployable memory benchmark
```

## Pipeline Built

현재 구현된 pipeline은 다음과 같다.

```text
Who&When local clone
-> data audit / case index
-> failure-prone case selection
-> trajectory prefix cut at gold decisive step
-> condition-specific guidance generation
-> responsible agent next-action regeneration
-> LLM judge evaluation
-> condition / case-level metrics
```

핵심 artifacts:

```text
who_when_card_poc/src/ww_card_poc/conditions.py
who_when_card_poc/src/ww_card_poc/phase2a_inputs.py
who_when_card_poc/src/ww_card_poc/generation_runner.py
who_when_card_poc/src/ww_card_poc/judging.py
who_when_card_poc/src/ww_card_poc/results.py
who_when_card_poc/src/ww_card_poc/exp3.py
```

이 pipeline 자체는 이후 runnable benchmark에서도 재사용 가능하다.

재사용 가능한 부분:

```text
1. trajectory parsing
2. condition rendering
3. attribution -> card conversion
4. no-memory / generic / raw / oracle / mismatch condition 비교
5. retry-style run orchestration
6. condition-level and case-level reporting
```

바꿔야 하는 부분:

```text
1. LLM judge proxy -> benchmark official evaluator
2. same-trace prefix repair -> task retry / held-out task transfer
3. gold-only attribution -> predicted attribution and accuracy/utility analysis
```

## Experiment 1: Feasibility Smoke

### Goal

Experiment 1은 가장 기본적인 feasibility check였다.

질문:

```text
Who&When gold attribution에서 만든 runtime card가
gold decisive step 직전 prefix에서 same-failure recurrence를 줄이는가?
```

### Setup

조건:

```text
no_guidance
strong_generic_guideline
sanitized_raw_gold_explanation
oracle_runtime_card
wrong_mismatched_card
```

먼저 no-guidance recurrence pretest를 실행해 baseline이 같은 실패를 반복하는 case를 골랐다.

```text
candidate cases: 15
repeats per case: 3
no_guidance recurrence: 0.7111
failure-prone cases: 11 / 15
```

그 후 10개 failure-prone cases에 대해 5조건 smoke를 실행했다.

### Results

| condition | n | repair success | recurrence |
| --- | ---: | ---: | ---: |
| no_guidance | 10 | 0.1000 | 0.9000 |
| strong_generic_guideline | 10 | 0.2000 | 0.8000 |
| sanitized_raw_gold_explanation | 10 | 0.3000 | 0.6000 |
| oracle_runtime_card | 10 | 0.6000 | 0.2000 |
| wrong_mismatched_card | 10 | 0.8000 | 0.2000 |

### Interpretation

긍정적 신호:

```text
oracle_runtime_card는 no_guidance보다 repair success가 높고 recurrence가 낮았다.
failure attribution을 runtime guidance로 바꾸면 agent behavior가 바뀔 수 있다.
```

한계:

```text
wrong_mismatched_card가 oracle보다 더 좋았다.
negative control이 깨졌다.
card effect가 attribution specificity가 아니라 broad verification nudge일 가능성이 있다.
```

Experiment 1의 안전한 결론:

```text
Runtime guidance can change same-trace next-action behavior.
But Exp1 does not prove attribution-specific utility.
```

## Experiment 2: Specificity Gate

### Goal

Experiment 2는 Exp1에서 깨진 negative control을 고치기 위한 specificity smoke였다.

질문:

```text
oracle_specific_card가 coarse reflection, broad verification,
raw gold explanation, hard mismatch보다 좋은가?
```

### Setup

주요 수정:

```text
1. shared base prompt에서 "failed trajectory" 표현 제거
2. oracle_runtime_card 대신 oracle_specific_card 사용
3. wrong mismatch 대신 hard_mismatched_card 사용
4. broad_verification_card와 coarse_reflection baseline 추가
```

조건:

```text
no_guidance
coarse_reflection
broad_verification_card
sanitized_raw_gold_explanation
oracle_specific_card
hard_mismatched_card
```

### Result Pattern

Exp2 smoke에서는 `oracle_specific_card`가 broad / hard mismatch / raw gold보다 강한 신호를 보였다.

핵심 관찰:

```text
oracle_specific_card repair: 0.6364
broad_verification_card repair: 0.2273
hard_mismatched_card repair: 0.2727
```

### Interpretation

처음 보기에는 attribution specificity signal처럼 보였다.

하지만 이후 코드/리뷰에서 중요한 문제가 드러났다.

```text
oracle_specific_card는 compact gold mistake_reason을 card에 포함했다.
diagnostic judge도 같은 gold mistake_reason을 평가 정보로 봤다.
따라서 card와 judge가 같은 gold diagnosis를 공유했다.
```

Experiment 2의 안전한 결론:

```text
Exp2 improves controls over Exp1,
but the strong oracle advantage may be inflated by judge-card coupling.
```

## Experiment 3: Abstraction and Judge Ablation

### Goal

Experiment 3는 Exp2의 literal gold diagnosis coupling을 줄이기 위한 stress test였다.

질문:

```text
literal gold reason을 제거하고
failure-mode pattern + missing-check type + abstract corrective action만 남겨도
oracle card가 broad/mismatch보다 좋은가?
```

### Setup

Exp3a:

```text
11 target cases
oracle_abstracted_card 생성
hard_mismatched_abstracted_card 생성
leakage / manipulation / distinctness audit
accepted: 11 / 11
exact leakage flags: 0
```

Exp3b:

```text
11 cases
4 conditions
2 attempts
88 generations
```

조건:

```text
broad_verification_card
correct_mode_only_placebo
oracle_abstracted_card
hard_mismatched_abstracted_card
```

### Initial Abstract-Criterion Judge Result

초기 judge는 gold reason 원문을 보지 않았지만, `oracle_abstracted_card`에서 나온 `missing_check_type`과 `abstract_corrective_action`을 criterion으로 사용했다.

따라서 완전한 independent judge가 아니라 **abstract-criterion judge**로 해석해야 한다.

| condition | n | repair success | recurrence |
| --- | ---: | ---: | ---: |
| broad_verification_card | 22 | 0.2727 | 0.5455 |
| correct_mode_only_placebo | 22 | 0.1364 | 0.6364 |
| hard_mismatched_abstracted_card | 22 | 0.4091 | 0.4091 |
| oracle_abstracted_card | 22 | 0.6364 | 0.0455 |

초기 contrast:

```text
oracle - broad = +0.3637
oracle - hard_mismatch = +0.2273
oracle - mode_only = +0.5000
```

### Failure-Anchored Judge Ablation

추가 피드백 후, generation은 다시 돌리지 않고 같은 88개 candidate action을 새 judge로 재채점했다.

failure-anchored judge는 다음을 보지 않는다.

```text
condition label
card text
card-derived missing_check_type
card-derived corrective action
gold failure explanation
```

대신 다음만 비교한다.

```text
original task
trajectory prefix
responsible agent
original failed action
candidate regenerated action
```

결과:

| condition | n | repair success | recurrence |
| --- | ---: | ---: | ---: |
| broad_verification_card | 22 | 0.5455 | 0.3636 |
| correct_mode_only_placebo | 22 | 0.4545 | 0.4545 |
| hard_mismatched_abstracted_card | 22 | 0.4545 | 0.5000 |
| oracle_abstracted_card | 22 | 0.6364 | 0.2727 |

Judge-gap:

```text
abstract-criterion judge:
  oracle - broad = +0.3637
  oracle - hard_mismatch = +0.2273

failure-anchored judge:
  oracle - broad = +0.0909
  oracle - hard_mismatch = +0.1819
```

### Interpretation

Exp3의 가장 중요한 결과는 다음이다.

```text
oracle advantage는 judge-card coupling을 줄이면 크게 약해진다.
하지만 oracle - hard mismatch 차이는 완전히 사라지지는 않는다.
```

또 하나의 중요한 관찰:

```text
repair_success와 concrete_action_rate가 강하게 묶여 있다.
failure-anchored judge에서도 repair_given_concrete = 1.0,
repair_without_concrete = 0.0이었다.
```

즉 현재 metric은 “진짜 task rescue”라기보다:

```text
original failed action과 비교해 concrete하게 다른 action을 냈는가
```

에 가깝다.

Experiment 3의 안전한 결론:

```text
There is a weak-positive signal that correct abstract attribution guidance
may help more than mismatched guidance.

However, the effect is judge-dependent, small under failure-anchored judging,
and not sufficient as evidence for self-improvement.
```

## What Worked

PoC에서 확인된 긍정적 요소:

```text
1. Who&When failure annotations can be transformed into runtime guidance.
2. Trace-prefix intervention pipeline works end-to-end.
3. Baseline recurrence filtering is possible.
4. Oracle vs mismatch comparisons can be constructed.
5. Judge ablation can expose circularity.
6. The remaining oracle-hard mismatch signal suggests the idea is not obviously dead.
```

팀 설득 관점에서 중요한 점:

```text
우리는 단순히 "좋아 보이는 card"를 만든 것이 아니라,
attribution -> intervention -> behavior change라는 실험 루프를 실제로 구현했다.
```

## What Did Not Work

현재 PoC가 final evidence가 될 수 없는 이유:

```text
1. same-trace gold intervention이라 clairvoyant proxy에 가깝다.
2. original task success를 측정하지 못한다.
3. LLM judge proxy가 card-derived key와 coupling될 수 있다.
4. repair_success가 concrete_action과 강하게 묶여 있다.
5. n=11 smoke라 통계적 근거가 약하다.
6. predicted attribution utility는 아직 보지 않았다.
7. reusable memory / cross-trace transfer도 아직 보지 않았다.
```

따라서 이 PoC만으로 말하면 안 되는 것:

```text
Failure Card improves task success.
Precise attribution is clearly better than coarse reflection.
Predicted Who&When attribution is useful.
Agents self-improve end-to-end.
```

## Decision

현재까지의 결론:

```text
Continue the research direction,
but do not scale Who&When same-trace repair as the main evidence.
```

즉:

```text
Who&When track:
  stop as powered same-trace experiment
  keep as diagnostic PoC / appendix / motivation

Main research track:
  move to existing runnable benchmark
  evaluate retry / transfer using official task success
```

## Recommended Next Step

새 benchmark를 직접 만들기보다, 기존 runnable benchmark 위에 protocol을 얹는다.

필요 조건:

```text
1. task rerun 가능
2. trajectory capture 가능
3. objective success evaluator 존재
4. baseline failure가 충분히 발생
5. failure attribution이 의미 있는 multi-step task
```

후보:

```text
1. tau-bench / tau2-bench
   tool-use, policy following, state-based success evaluation.
   가장 추천.

2. SWE-bench Lite
   objective test-based success.
   다만 coding domain으로 좁아짐.

3. WebArena / MiniWoB / OSWorld
   interaction trajectory는 좋지만 setup noise와 비용이 큼.

4. GAIA subset
   Who&When과 자연스럽게 연결되지만 objective rerun/evaluator가 더 까다로움.
```

추천 우선순위:

```text
Primary:
  tau-bench 계열

Bridge / appendix:
  Who&When PoC

Later external validity:
  SWE-bench Lite or WebArena/OSWorld
```

## Proposed Runnable Benchmark Protocol

기존 benchmark 위에서 다음 protocol을 실행한다.

```text
1. baseline agent run
2. failed trajectory 수집
3. failure attribution 생성
   - oracle / human-labeled subset
   - predicted attribution
4. attribution-derived memory/card 생성
5. same-task retry
6. held-out same-failure-mode transfer
7. official evaluator로 task success 측정
```

조건:

```text
no_memory
generic_guideline
coarse_reflection
full_failed_trajectory_ICL
raw_attribution_explanation
structured_attribution_card
wrong_or_mismatched_card
predicted_attribution_card
```

핵심 metric:

```text
official task success
retry rescue rate
held-out transfer success
negative transfer
same-failure recurrence, secondary
utility per token, if comparing full trajectory ICL vs compact card
```

가장 중요한 비교:

```text
structured_attribution_card
  vs coarse_reflection
  vs generic_guideline
  vs full_failed_trajectory_ICL
  vs wrong/mismatched_card
```

논문 spine:

```text
Does trajectory-level failure attribution provide a better self-improvement signal
than coarse reflection or generic in-context memory?
```

## Suggested Team Pitch

팀원에게는 다음처럼 설명하는 것이 안전하다.

```text
Who&When으로 빠르게 PoC를 했다.
gold attribution을 runtime intervention으로 바꾸는 파이프라인은 작동했다.
same-trace prefix에서 agent behavior가 바뀌는 신호도 있었다.
하지만 judge ablation을 해보니 효과 일부는 proxy/judge coupling에 민감했다.

따라서 이 아이디어는 가능성이 있지만,
진짜 주장은 rerunnable benchmark에서 official task success로 검증해야 한다.

다음 단계는 새 benchmark 제작이 아니라
tau-bench 같은 기존 benchmark 위에
failure attribution -> memory -> retry/transfer protocol을 얹는 것이다.
```

짧은 버전:

```text
Who&When PoC says: possible, but not proven.
Next step: prove it on a runnable benchmark with objective success.
```

## Current Recommendation

```text
Do not rerun Experiments 1 and 2.
Do not scale same-trace Who&When powered runs.
Do not run Exp4 until we decide whether transfer probe is still useful.

Use Who&When as PoC evidence that the pipeline is feasible.
Move main experimental evidence to a runnable existing benchmark.
```

