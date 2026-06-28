# Failure 활용 PoC 발표용 요약

Date: 2026-06-28

## Executive Summary

이 PoC는 “에이전트 실패를 잘 설명할 수 있는가?”에서 출발했지만, 실제로 확인하고 싶었던 것은 한 단계 더 downstream에 있었다. 실패 원인을 알게 되었을 때 그 정보가 다음 실행을 더 성공적으로 만들 수 있는지, 그리고 그 효과가 단순한 generic reminder보다 나은지를 보고자 했다.

핵심 질문:

```text
정밀한 failure attribution은
generic reflection / memory보다
더 좋은 자기개선 신호가 될 수 있는가?
```

초기 가설:

```text
failure attribution
-> better prose memory card
-> better retry success
```

실험 후 수정된 가설:

```text
failure attribution
-> enforceable check / verifier
-> guarded retry success
```

최종 takeaway:

```text
Failure attribution is weak as plain advice,
but promising as a source of enforceable checks.
```

이 말은 “failure card가 성공했다”는 뜻이 아니다. 오히려 prose card 방식은 여러 번 실패했다. 더 정확한 결론은, failure attribution을 자연어 조언으로 넣는 것보다 실행을 멈추거나 통과시키는 check로 바꾸는 쪽이 더 유망하다는 것이다.

## Research Arc 한 줄 요약

전체 실험은 세 단계로 진행됐다. 먼저 Who&When으로 빠르게 local repair 가능성을 확인했고, 그 다음 tau2에서 실제 fresh retry success를 봤으며, 마지막으로 intervention 형식을 prose memory에서 binding check로 바꿨다.


| Stage | 실험 | 결론 |
| --- | --- | --- |
| Local repair | Who&When Exp1-3 | attribution guidance는 행동을 바꾸지만, same-trace proxy로는 약함 |
| Fresh retry | tau2 Exp5.3-5.5 | prose memory는 generic baseline과 잘 분리되지 않음 |
| Enforcement | tau2 Exp6A-6C | binding check로 바꾸면 precision signal이 제한적으로 살아남 |

# Experiment Notes

각 실험은 이전 실험에서 드러난 약점을 하나씩 제거하기 위해 설계했다. 따라서 단일 실험의 승패보다 중요한 것은, 어떤 가설이 살아남고 어떤 interface가 탈락했는지의 흐름이다.

## Experiment 1 — Who&When Feasibility Smoke

### 왜 이 실험을 했나

가장 먼저 확인해야 했던 것은 단순했다. 실패 원인 분석을 아무리 잘해도, 그것을 agent에게 넣었을 때 행동이 바뀌지 않으면 downstream utility 연구는 시작할 수 없다. 그래서 Who&When의 gold attribution을 runtime card로 바꿔, 실패가 발생했던 decisive step 직전에 넣어보는 local repair smoke를 먼저 했다.

이 실험은 task를 처음부터 다시 푸는 실험이 아니다. 같은 failed trace의 prefix에서 next action만 다시 생성하는 좁은 counterfactual test다.

### 핵심 가설

```text
Gold attribution-derived runtime card를 넣으면
failed trace의 decisive step에서 같은 실패 반복이 줄어들 것이다.
```

### 실험

Who&When failed trajectory를 gold decisive step 직전까지 잘라서 prefix를 만들고, condition별 guidance를 넣은 뒤 next action을 재생성했다.

조건:

```text
no_guidance
strong_generic_guideline
sanitized_raw_gold_explanation
oracle_runtime_card
wrong_mismatched_card
```

### 결과

```text
no_guidance           repair 0.1 / recurrence 0.9
oracle_runtime_card   repair 0.6 / recurrence 0.2
wrong_mismatched_card repair 0.8 / recurrence 0.2
```

### 해석

좋은 신호:

```text
attribution-derived card는 no guidance보다 훨씬 좋았다.
즉, failure analysis를 runtime guidance로 바꾸면 행동은 바뀐다.
```

문제:

```text
wrong mismatched card가 oracle보다 더 좋았다.
```

결론:

```text
pipeline feasibility는 확인.
하지만 attribution-specific utility는 아직 미검증.
```

다음 결정:

```text
negative control을 고치고, oracle이 generic/wrong보다 정말 나은지 다시 봐야 한다.
```

## Experiment 2 — Who&When Specificity Gate

### 왜 이 실험을 했나

Exp1의 가장 큰 문제는 wrong card가 oracle보다 더 잘 나온 것이었다. 이 상태에서는 “failure attribution이 유용하다”가 아니라 “어떤 verify-style nudge든 도움이 된다”는 해석이 더 강했다. 그래서 Exp2는 성능을 더 높이는 실험이 아니라, oracle 효과가 generic/mismatch와 구별되는지 확인하는 specificity gate였다.

### 핵심 가설

```text
Exp1의 negative control을 고치면
oracle_specific_card가 broad/generic/mismatch보다 좋아야 한다.
```

### 실험

Exp1보다 control을 강화했다.

```text
1. base prompt에서 "failed trajectory" 제거
2. mode-level oracle card 대신 oracle_specific_card 사용
3. weak mismatch 대신 hard_mismatched_card 사용
```

조건:

```text
no_guidance
coarse_reflection
broad_verification_card
raw_gold_explanation
oracle_specific_card
hard_mismatched_card
```

### 결과

```text
oracle_specific_card    repair 0.6364 / recurrence 0.2727
broad_verification_card repair 0.2273 / recurrence 0.6364
hard_mismatched_card    repair 0.2727 / recurrence 0.6818
```

핵심 contrast:

```text
oracle - broad    = +0.4091
oracle - mismatch = +0.3637
```

### 해석

좋은 신호:

```text
oracle_specific_card가 broad/mismatch를 확실히 이겼다.
```

문제:

```text
oracle card가 compact gold mistake reason을 포함했고,
judge도 같은 gold diagnosis를 참고했다.
```

결론:

```text
specificity signal은 보였지만,
literal gold leakage / judge-card coupling 위험이 남았다.
```

다음 결정:

```text
oracle card에서 literal gold reason을 제거하고, judge coupling을 줄여도 신호가 남는지 봐야 한다.
```

## Experiment 3 — Who&When Abstraction + Judge Ablation

### 왜 이 실험을 했나

Exp2의 oracle advantage는 강했지만, oracle card와 judge가 같은 gold diagnosis를 공유했을 가능성이 있었다. 그래서 Exp3에서는 card를 더 추상화하고, judge가 card 내용이나 gold reason을 보지 않는 재채점까지 수행했다. 목적은 “정답을 슬쩍 알려줘서 좋아진 것인지”를 줄이는 것이었다.

### 핵심 가설

```text
literal gold reason을 제거해도
abstracted oracle card가 broad/mismatch보다 좋아야 한다.
```

### 실험

oracle card를 더 추상화했다.

```text
literal mistake detail 제거
failure-mode pattern 유지
missing-check type 유지
abstract corrective action 유지
```

조건:

```text
broad_verification_card
mode_only_placebo
oracle_abstracted_card
hard_mismatched_abstracted_card
```

두 judge를 비교했다.

```text
abstract-criterion judge:
  oracle card에서 나온 abstract criterion을 사용

failure-anchored judge:
  card text / condition label / gold reason을 보지 않음
```

### 결과

Abstract-criterion judge:

```text
oracle_abstracted repair 0.6364
broad_verification repair 0.2727
hard_mismatch repair 0.4091
```

Failure-anchored judge:

```text
oracle_abstracted repair 0.6364
broad_verification repair 0.5455
hard_mismatch repair 0.4545
```

### 해석

좋은 신호:

```text
oracle signal이 완전히 사라지지는 않았다.
```

문제:

```text
judge를 더 독립적으로 만들자 oracle advantage가 크게 줄었다.
same-trace proxy는 여전히 task success가 아니라 local repair만 본다.
```

결론:

```text
Who&When은 PoC로는 충분하지만,
main self-improvement claim을 입증하기에는 약하다.
objective runnable benchmark로 이동해야 한다.
```

다음 결정:

```text
trace-prefix repair가 아니라, 실제 task retry success를 official reward로 볼 수 있는 benchmark가 필요하다.
```

## Experiment 4 — Cross-Trace Transfer

### 왜 원래 계획했나

same-trace repair는 “그 실패 지점을 보고 바로 고친 것”에 가깝다. 진짜 self-improvement에 가까워지려면 한 trace에서 만든 memory가 다른 유사 failure에도 transfer되어야 한다. 그래서 원래는 Who&When cross-trace transfer를 다음 단계로 계획했다.

### 핵심 가설

```text
source failure에서 만든 card가
held-out target failure에도 transfer될 수 있는가?
```

### 상태

```text
deferred
```

### 이유

Exp3 이후 핵심 병목은 cross-trace 이전에:

```text
실제 task success를 볼 수 있는 runnable benchmark가 필요하다.
```

였기 때문에 tau2로 이동했다.

### 해석

```text
Exp4는 삭제된 것이 아니라 보류된 Who&When transfer probe다.
하지만 현재 보고서의 main evidence path는 tau2 fresh retry다.
```

## Experiment 5.2 — tau2 Baseline Harvest

### 왜 이 실험을 했나

Who&When은 빠른 PoC에는 좋았지만, 실제 task success를 볼 수 없었다. tau2는 fresh environment에서 task를 다시 실행하고 official reward를 받을 수 있기 때문에, failure attribution이 retry success를 올리는지 더 직접적으로 볼 수 있다. 먼저 필요한 것은 충분히 실패하면서도 완전히 불가능하지 않은 task pool을 찾는 것이었다.

### 핵심 가설

```text
tau2 retail에서 retry rescue 실험에 쓸 실패 task를 충분히 수확할 수 있다.
```

### 실험

```text
30 tasks
3 trials per task
90 simulations
gpt-4.1-mini agent/user
official tau2 reward
```

### 결과

```text
official success 22/90 = 0.2444
DB match         33/90 = 0.3667

stable_failure 15 tasks
mixed          14 tasks
stable_success  1 task
```

### 해석

좋은 점:

```text
baseline이 너무 쉽지도 않고, 완전히 hopeless하지도 않았다.
failure diversity도 있었다.
```

대표 failure family:

```text
availability count
refund / calculation / communication
DB write / mutation
tracking communication
multi-action modification
```

결론:

```text
tau2 retail은 runnable rescue PoC에 적합하다.
```

다음 결정:

```text
이제 oracle/generic/mismatch memory를 넣고 fresh retry success를 비교한다.
```

## Experiment 5.3 — tau2 Prose Memory Rescue

### 왜 이 실험을 했나

이 실험이 처음으로 원래 질문에 가까웠다. 실패 trace를 보고 만든 oracle memory를 fresh tau2 retry에 넣었을 때, no memory나 generic policy reminder보다 실제 official reward가 좋아지는지를 봤다. 즉, Who&When의 local repair가 아니라 runnable task rescue로 넘어간 첫 실험이다.

### 핵심 가설

```text
oracle missing-check memory가
no_memory / generic / mismatch보다 fresh retry success를 더 잘 올릴 것이다.
```

### 실험

```text
20 selected tasks
4 conditions
3 seeds
240 runs
official tau2 reward
```

조건:

```text
no_memory
generic_policy_card
oracle_single_missing_check_card
hard_mismatched_card
```

### 결과

```text
generic_policy_card              16/60 = 0.2667
oracle_single_missing_check_card 15/60 = 0.2500
hard_mismatched_card             13/60 = 0.2167
no_memory                        12/60 = 0.2000
```

Component:

```text
generic DB 0.5167 / NL 0.5965
oracle  DB 0.4000 / NL 0.6842
```

### 해석

좋은 신호:

```text
runtime memory는 live했다.
oracle card도 일부 failure를 rescue했다.
```

문제:

```text
oracle이 generic을 이기지 못했다.
oracle은 NL/assertion은 올렸지만 DB/tool success는 낮췄다.
```

결론:

```text
prose memory card만으로는 attribution specificity가 잘 드러나지 않는다.
```

다음 결정:

```text
oracle card가 DB/tool side를 충분히 강제하지 못한 것이 문제인지 확인한다.
```

## Experiment 5.4 — Tool-Completion Card Revision

### 왜 이 실험을 했나

Exp5.3에서 oracle card는 NL/assertion을 올렸지만 DB/tool completion은 약했다. 그래서 실패 원인을 “카드가 너무 말 중심이고 실제 tool-side completion을 충분히 밀지 못한다”로 보고, branch/tool completion을 더 명시한 v2 card를 만들었다.

### 핵심 가설

```text
Exp5.3에서 oracle이 DB/tool side를 못 밀었다면,
tool-completion ledger를 명시한 oracle_v2가 성능을 올릴 것이다.
```

### 실험

```text
7 tasks
5 conditions
5 seeds
175 runs
```

조건:

```text
no_memory
generic_policy_card_v2
oracle_single_missing_check_v1
oracle_tool_completion_card_v2
hard_mismatched_card_v2
```

### 결과

```text
oracle_single_missing_check_v1 14/35 = 0.4000
generic_policy_card_v2         8/35 = 0.2286
no_memory                      7/35 = 0.2000
oracle_tool_completion_v2      6/35 = 0.1714
hard_mismatch_v2               5/35 = 0.1429
```

### 해석

좋은 신호:

```text
짧은 v1 missing-check card는 여전히 유망했다.
```

문제:

```text
더 긴 v2 branch/tool-completion card는 오히려 실패했다.
```

결론:

```text
더 많은 prose, 더 긴 checklist가 답은 아니다.
decisive missing check를 짧게 잡는 편이 더 나았다.
```

다음 결정:

```text
card를 더 길게 만드는 방향은 중단하고, 짧은 missing-check prose가 held-out에서도 generic보다 나은지 확인한다.
```

## Experiment 5.5 — Variability + Saturation Pre-Check

### 왜 이 실험을 했나

Exp5.4에서 v1 missing-check card가 가장 좋아 보였지만, 그 효과가 특정 task에 몰렸을 수 있었다. 바로 큰 run을 하기 전에, held-out pool에서 oracle prose memory가 generic/mode-only와 분리될 가능성이 있는지 cheap pre-check를 했다. 동시에 tau2 user simulator의 변동성도 측정했다.

### 핵심 가설

```text
held-out pool에서 oracle prose memory가
generic / mode_only보다 좋은지 full run 전에 cheap gate로 확인한다.
```

### 실험

5.5A:

```text
5 tasks x 1 seed x 3 no-memory repeats
```

5.5C:

```text
6 tasks x 4 conditions x 3 seeds = 72 runs
```

조건:

```text
no_memory
generic_policy_card
failure_mode_only_card
oracle_single_missing_check_v1
```

### 결과

Same-seed instability:

```text
success flip 1/5
DB flip      1/5
NL flip      2/5
```

Pre-check:

```text
generic_policy_card            6/18
oracle_single_missing_check_v1 6/18
failure_mode_only_card         5/18
no_memory                      5/18
```

### 해석

문제:

```text
oracle prose memory가 generic과 동률이었다.
pool도 all-fail / saturated / wrong-family task가 섞여 있었다.
```

결론:

```text
full prose-memory experiment를 키우면 또 ambiguous result가 나올 가능성이 높다.
prose memory track은 여기서 멈춘다.
```

다음 결정:

```text
새 card variant를 더 만들지 말고, intervention interface 자체를 바꾼다.
```

## Experiment 6A/B — Binding Check Pilot

### 왜 이 실험을 했나

Exp5까지의 반복된 패턴은 “정보가 아예 쓸모없다”라기보다, prompt 안의 prose memory를 모델이 안정적으로 따르지 않는다는 쪽에 가까웠다. 그래서 개입을 조언에서 강제로 바꿨다. agent가 final response를 내려고 할 때, harness가 post-condition을 검사하고 실패하면 종료를 막는 방식이다.

### 핵심 가설

```text
prose memory가 약한 이유가 agent가 조언을 무시할 수 있기 때문이라면,
finalization boundary에서 binding check로 강제할 때 reward가 움직일 것이다.
```

### 실험 방식 전환

Before:

```text
task starts
-> memory in system prompt
-> agent may follow or ignore
```

After:

```text
agent tries final response
-> binding wrapper checks post-condition
-> if check fails, stop is blocked once
```

### 결과

6A timing smoke:

```text
no_gate 0/2
mismatched_money_gate 2/2
```

6B recoverability probe:

```text
coarse_binding_gate 4/10
no_gate             1/10
```

Paired:

```text
rescues 4
regressions 1
delta +0.3000
```

### 해석

좋은 신호:

```text
binding finalization check는 실제 tau2 reward를 움직였다.
```

문제:

```text
이 단계에서는 precision을 테스트하지 않았다.
coarse binding도 DB regression을 만들 수 있었다.
```

결론:

```text
advisory prose보다 enforcement가 더 강한 intervention lever다.
```

다음 결정:

```text
binding 자체가 좋은 것인지, precise attribution-derived check가 좋은 것인지 분리한다.
```

## Experiment 6C — Binding Forcing vs Content

### 왜 이 실험을 했나

Exp6A/B는 binding check가 live하다는 것을 보였지만, 아직 precision은 테스트하지 않았다. 성공이 단순히 “한 번 더 말할 기회를 줘서” 나온 것인지, broad check만으로 충분한지, 아니면 정확한 failure attribution에서 나온 post-condition이 실제로 더 좋은지 분리해야 했다.

### 핵심 가설

```text
binding이 효과가 있다면,
그 효과가 단순 extra turn 때문인지,
정확한 attribution-derived check 때문인지 분리해야 한다.
```

### 실험

```text
3 tasks
8 seeds
6 conditions
144 runs
```

조건:

```text
no_gate
always_continue_once_control
coarse_binding_gate
mode_only_binding_gate
precise_attribution_binding_gate
wrong_binding_gate
```

### 결과

```text
precise_attribution_binding_gate 15/24 = 0.6250
mode_only_binding_gate           11/24 = 0.4583
coarse_binding_gate              10/24 = 0.4167
wrong_binding_gate                6/24 = 0.2500
always_continue_once_control      4/24 = 0.1667
no_gate                           2/24 = 0.0833
```

Component:

```text
precise success 0.6250 / DB 0.7500 / NL 0.8333
mode    success 0.4583 / DB 0.6250 / NL 0.7083
coarse  success 0.4167 / DB 0.6667 / NL 0.6250
```

Task-level:

```text
task 19:
  precise 4/8, coarse 4/8

task 36:
  precise 4/8, coarse 4/8

task 95:
  precise 7/8, mode_only 6/8, coarse 2/8, no_gate 0/8
```

### 해석

좋은 신호:

```text
precise gate가 전체적으로 가장 높았다.
wrong gate와 always_continue를 이겼기 때문에 단순 extra turn만으로는 설명이 부족하다.
```

제한:

```text
가장 강한 signal은 task 95에서 나온다.
tasks 19/36에서는 precise = coarse다.
```

결론:

```text
precision under binding에 대한 limited positive result.
prose memory가 아니라 binding verifier/check가 더 유망한 interface다.
```

다음 결정:

```text
보고서의 결론은 "failure card가 된다"가 아니라 "failure attribution을 enforceable check로 바꿔야 한다"로 잡는다.
```

# Final Synthesis

## 우리가 배운 것

```text
1. failure attribution은 행동을 바꿀 수 있다.
2. 하지만 prose memory/card interface는 약하다.
3. 더 긴 card도 답이 아니다.
4. binding finalization check는 강한 intervention lever다.
5. precision은 binding 아래에서 제한적으로 살아났다.
```

## 최종 결론

```text
Failure attribution is weak as plain advice,
but promising as a source of enforceable checks.
```

## 다음 질문

```text
1. predicted attribution으로 이런 binding check를 만들 수 있는가?
2. 어떤 check를 언제 적용할지 routing/retrieval할 수 있는가?
3. multi-agent setting에서 who/when attribution이 targeted intervention에 도움이 되는가?
4. fail -> attribute -> check -> guarded retry loop가 closed-loop self-improvement로 이어지는가?
```
