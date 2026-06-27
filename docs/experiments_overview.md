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
  status: next
  doc: docs/experiment3.md

Experiment 4
  Cross-trace transfer lite
  status: planned after Experiment 3
  doc: docs/experiment4.md

Experiment 5
  Predicted card content utility
  status: gated

Experiment 6
  Runnable closed-loop self-improving agent
  status: gated by transfer signal

Experiment 7
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

## Next Gate: Experiment 3

Experiment 3의 목적:

```text
oracle card에서 literal gold reason을 제거해도
repair signal이 유지되는지 확인한다.
```

핵심 조건:

```text
broad_verification_card
correct_mode_only_placebo
oracle_specific_card_current
oracle_abstracted_card
hard_mismatched_abstracted_card
```

핵심 judge 변경:

```text
diagnostic judge:
  기존과 유사, gold reason을 봄

decoupled judge:
  gold reason 원문과 original failed action을 보지 않음
```

통과 기준:

```text
oracle_abstracted_card > broad_verification_card
oracle_abstracted_card > correct_mode_only_placebo
oracle_abstracted_card > hard_mismatched_abstracted_card
decoupled judge에서도 oracle advantage 유지
manipulation check에서 intended mode/check가 복원됨
```

통과하면:

```text
Experiment 4 cross-trace transfer lite
```

붕괴하면:

```text
Who&When same-trace track을 powered run으로 키우지 않는다.
content specificity 대신 retrieval/routing/closed-loop benchmark로 pivot을 검토한다.
```

중요한 분해:

```text
correct_mode_only_placebo - broad_verification:
  mode routing 단독 가치

oracle_abstracted_card - correct_mode_only_placebo:
  missing-check/action abstraction의 추가 가치
```

## Next Transfer Probe: Experiment 4

Experiment 4의 목적:

```text
source failure에서 만든 abstract card가
held-out target trace에도 transfer되는지 확인한다.
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
