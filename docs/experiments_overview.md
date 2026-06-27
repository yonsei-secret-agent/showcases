# Experiments Overview

## North Star

이 프로젝트의 핵심 질문은 다음이다.

```text
Can precise failure attribution become a better self-improvement signal
than coarse reflection or generic in-context memory?
```

한국어로는:

```text
정밀한 failure attribution은 coarse reflection / generic memory보다
더 좋은 자기개선 신호가 될 수 있는가?
```

## 현재 판단

Who&When same-trace repair는 필요한 첫 단계였지만 최종 목적지는 아니다.

```text
Who&When same-trace:
  좋은 diagnostic/proxy setting
  하지만 deployment loop는 아님

최종 목표:
  failure -> attribution -> memory -> retrieval -> retry / held-out success
```

따라서 다음 실험은 무작정 scale-up하지 않고, 아래 gate를 순서대로 통과해야 한다.

현재 가장 중요한 방향 전환:

```text
Who&When track:
  feasibility / specificity / abstraction diagnostic로 사용

tau2-bench track:
  objective retry success를 보는 runnable PoC로 이동
```

## 실험 흐름

```text
Experiment 1
  Gold-point runtime card smoke
  status: completed
  doc: docs/experiment1.md

Experiment 2
  Specificity smoke
  status: completed
  doc: docs/experiment2.md

Experiment 3
  Abstraction stress test + judge decoupling
  status: completed smoke
  summary: weak-positive, judge-dependent signal
  doc: docs/experiment3.md

Experiment 4
  Cross-trace transfer lite
  status: deferred / conditional
  doc: docs/experiment4.md

Experiment 5
  tau2-bench runnable rescue pilot
  status: next planned track
  doc: docs/experiment5.md

Experiment 6
  Predicted card content utility
  status: gated by runnable rescue signal

Experiment 7
  Runnable closed-loop self-improving agent
  status: gated by transfer / rescue signal

Experiment 8
  Predicted intervention point
  status: gated
```

## Experiment 1 Summary

질문:

```text
Gold Who&When attribution에서 만든 runtime card가
gold decisive step에서 same-failure recurrence를 줄이는가?
```

결과:

```text
oracle_runtime_card:
  repair 0.6
  recurrence 0.2

no_guidance:
  repair 0.1
  recurrence 0.9

wrong_mismatched_card:
  repair 0.8
  recurrence 0.2
```

해석:

```text
Runtime guidance can improve local trace-prefix repair.
하지만 wrong/mismatched card가 oracle보다 좋아서 attribution-specific utility는 미지원.
```

## Experiment 2 Summary

질문:

```text
oracle_specific_card가 broad verification / hard mismatch / raw gold보다 좋은가?
```

결과:

```text
oracle_specific_card:
  repair 0.6364
  recurrence 0.2727

broad_verification_card:
  repair 0.2273
  recurrence 0.6364

hard_mismatched_card:
  repair 0.2727
  recurrence 0.6818
```

핵심 contrast:

```text
oracle_specific - broad_verification = +0.4091
oracle_specific - hard_mismatch      = +0.3637
```

해석:

```text
same-trace specificity smoke로는 좋은 신호.
하지만 아직 literal gold diagnosis / judge coupling / same-trace clairvoyance 위험이 남아 있음.
```

## Experiment 3 Summary

Experiment 3의 목적:

```text
oracle card에서 literal gold reason을 제거해도
repair signal이 유지되는지 확인한다.
```

핵심 조건:

```text
broad_verification_card
correct_mode_only_placebo
oracle_abstracted_card
hard_mismatched_abstracted_card
```

실행 결과:

```text
abstract-criterion judge:
  oracle_abstracted repair = 0.6364
  broad_verification repair = 0.2727
  hard_mismatch repair = 0.4091

failure-anchored judge:
  oracle_abstracted repair = 0.6364
  broad_verification repair = 0.5455
  hard_mismatch repair = 0.4545
```

해석:

```text
oracle signal은 일부 살아남았지만,
judge criterion을 card-derived check에서 떼어내면 advantage가 크게 줄었다.
```

현재 판단:

```text
Who&When same-trace track은 가능성 확인용으로는 충분했다.
하지만 이를 powered run으로 키우기보다,
objective runnable benchmark인 tau2-bench로 이동한다.
```

중요한 분해:

```text
correct_mode_only_placebo - broad_verification:
  mode routing 단독 가치

oracle_abstracted_card - correct_mode_only_placebo:
  missing-check/action abstraction의 추가 가치
```

## Deferred Transfer Probe: Experiment 4

Experiment 4의 목적:

```text
source failure에서 만든 abstract card가
held-out target trace에도 transfer되는지 확인한다.
```

이 단계는 삭제된 것이 아니라 Exp3 이후로 지연된 것이다.

```text
Cross-trace transfer is deferred, not removed.
```

단, Experiment 4는 Experiment 3 결과에 따라 두 갈래로 나뉜다.

```text
oracle_abstracted > mode_only > broad:
  abstract failure-memory transfer로 진행

mode_only ~= oracle_abstracted > broad:
  mode-routing / retrieval transfer로 재프레이밍

oracle_abstracted ~= broad:
  Exp4 보류, renderer/broad baseline 재검토
```

주의:

```text
이 실험은 oracle retrieval upper bound다.
agent가 스스로 memory를 retrieve했다는 claim은 금지.
```

통과하면 처음으로 다음 주장이 가능해진다.

```text
Under oracle retrieval, attribution-derived abstract cards can act as reusable failure memory.
```

현재는 Experiment 5 tau2-bench runnable rescue pilot을 먼저 실행한다.

이유:

```text
Exp4는 여전히 Who&When trace-prefix proxy다.
Exp5는 official task reward로 retry rescue를 직접 본다.
```

## Next Runnable Probe: Experiment 5

Experiment 5의 목적:

```text
tau2-bench failed task에서 만든 attribution-derived card가
fresh retry의 official reward를 올리는지 확인한다.
```

핵심 차이:

```text
Who&When:
  same-trace next-action proxy

tau2-bench:
  rerunnable task, fresh environment, official final reward
```

첫 pilot은 paper-level evidence가 아니라 team-convincing PoC다.

성공하면:

```text
existing runnable benchmark 위에서
failure attribution -> memory -> retry success
흐름에 실제 가능성이 있음을 보여준다.
```

단, `source_mode_only_placebo`와 비교해야 한다.

```text
source_mode_only_placebo ~= source_oracle_abstracted_card:
  transfer 효과는 rich memory content보다 mode routing에 가까움.

source_oracle_abstracted_card > source_mode_only_placebo:
  abstract corrective action까지 transfer에 기여함.
```

## Decision Gates

```text
Experiment 3 passes:
  proceed to Experiment 4.

Experiment 3 collapses:
  do not scale same-trace repair.
  inspect literal diagnosis / judge coupling.
  prepare routing or closed-loop pivot.

Experiment 4 passes:
  consider powered transfer or runnable closed-loop benchmark.

Experiment 4 fails:
  same-trace card repair may not transfer.
  pivot to intervention targeting, retrieval/routing, or controlled runnable benchmark.
```

## Claim Boundaries

현재까지 말할 수 있는 것:

```text
Gold attribution-derived cards can improve same-trace trace-prefix repair.
Experiment 2A smoke suggests attribution-specific signal under same-trace gold intervention.
```

아직 말하면 안 되는 것:

```text
Failure Cards are reusable memory.
Predicted Who&When attribution works.
Agents self-improve end-to-end.
Original tasks are rescued.
Attribution accuracy predicts downstream utility.
```
