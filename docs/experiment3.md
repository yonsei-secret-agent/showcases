# Experiment 3: Abstraction Stress Test and Judge Decoupling

## 상태

```text
status: completed smoke
type: abstraction gate experiment
scope: same-trace gold-point repair, abstraction stress test, judge decoupling
```

Experiment 3는 Experiment 2A smoke를 바로 powered run으로 키우기 전에 실행하는 값싼 gate다.

목적은 `oracle_specific_card`의 이득이 실제로 reusable abstraction에서 온 것인지, 아니면 same-trace gold diagnosis를 literal하게 제공한 효과인지 확인하는 것이다.

이 실험은 positive proof가 아니라 falsification / pivot diagnostic이다.

```text
primary value:
  expensive powered run이나 closed-loop build 전에 멈출지 판단한다.

not primary value:
  hero thesis를 입증한다.
```

## 실험 목표

Experiment 2A smoke에서는 `oracle_specific_card`가 broad verification, hard mismatch, raw gold explanation보다 좋았다.

하지만 아직 남은 위험이 있다.

```text
oracle_specific_card가 compact gold mistake_reason을 포함한다.
judge도 gold diagnostic reason을 보고 candidate를 평가한다.
따라서 card와 judge가 같은 gold diagnosis를 공유할 수 있다.
```

Experiment 3는 이 위험을 직접 찌른다.

핵심 질문:

```text
literal gold reason을 제거하고
failure-mode pattern + missing-check type + abstract corrective action만 남겨도
oracle card가 broad/mismatch보다 좋은가?
```

보조 질문:

```text
judge에게 gold reason 원문을 주지 않아도
oracle advantage가 유지되는가?
```

## 왜 필요한가

Experiment 2A가 보여준 것은 같은 trace의 decisive step에서 좋은 신호였다.

```text
oracle_specific_card repair: 0.6364
broad_verification_card repair: 0.2273
hard_mismatched_card repair: 0.2727
```

하지만 이 결과가 곧 reusable failure memory를 뜻하지는 않는다.

위험한 해석:

```text
gold diagnosis를 같은 trace에 다시 넣었기 때문에 좋아진 것이다.
```

우리가 원하는 해석:

```text
gold attribution에서 추출한 abstract failure pattern이
다음 행동을 실제로 더 안전하게 만든 것이다.
```

Experiment 3는 이 둘을 가른다.

## 실행 결과

실행일:

```text
2026-06-27
```

실행 범위:

```text
Exp3a:
  11 target cases
  oracle_abstracted_card 생성
  hard_mismatched_abstracted_card 생성
  LLM leakage / manipulation / distinctness audit

Exp3b:
  11 target cases
  4 core conditions
  2 attempts
  88 generations
  88 decoupled judgments
```

사용한 조건:

```text
broad_verification_card
correct_mode_only_placebo
oracle_abstracted_card
hard_mismatched_abstracted_card
```

이번 smoke에서는 `oracle_specific_card_current` reference condition과 diagnostic judge sensitivity는 돌리지 않았다.

### Exp3a Audit

```text
audit records: 11
accepted: 11
rejected: 0
exact leakage flags: 0

abstraction_level:
  action_schema: 7
  check_type: 4
```

Target failure mode 분포:

```text
unverified or inaccurate factual claim: 4
decisive reasoning or execution error: 3
unsupported assumption or fabricated intermediate data: 3
incomplete handling of task constraints or data cases: 1
```

관찰:

```text
Exp3a는 renderer gate를 통과했다.
abstracted card는 broad baseline과 구별 가능하다고 audit되었고,
mode/check type 복원 가능성도 통과했다.
```

### Exp3b Metrics: Abstract-Criterion Judge

처음 실행한 judge는 gold reason 원문은 보지 않았지만, `oracle_abstracted_card`에서 생성된
`missing_check_type`과 `abstract_corrective_action`을 criterion으로 사용했다. 따라서 이후 문서에서는
이를 완전한 decoupled judge가 아니라 **abstract-criterion judge**로 해석한다.

Abstract-criterion judge 기준 결과:

| condition | n | repair_success | same_failure_recurrence | concrete_action | negative_transfer | mean_score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| broad_verification_card | 22 | 0.2727 | 0.5455 | 0.2727 | 0.0455 | 1.5000 |
| correct_mode_only_placebo | 22 | 0.1364 | 0.6364 | 0.1364 | 0.0455 | 1.2273 |
| hard_mismatched_abstracted_card | 22 | 0.4091 | 0.4091 | 0.4091 | 0.0909 | 1.7727 |
| oracle_abstracted_card | 22 | 0.6364 | 0.0455 | 0.6364 | 0.0000 | 2.2727 |

핵심 contrast:

```text
abstract_nudge_gap:
  oracle_abstracted - broad_verification
  = +0.3637 repair

mode_routing_lift:
  correct_mode_only - broad_verification
  = -0.1363 repair

abstract_action_lift:
  oracle_abstracted - correct_mode_only
  = +0.5000 repair

abstract_right_vs_wrong:
  oracle_abstracted - hard_mismatched_abstracted
  = +0.2273 repair

recurrence reduction vs broad:
  broad recurrence - oracle_abstracted recurrence
  = +0.5000
```

Case-level 관찰:

```text
oracle best over broad and mismatch: 3 / 11 cases
all equal: 6 / 11 cases
mixed tie: 2 / 11 cases
```

해석상 주의:

```text
aggregate signal은 강하지만, case-level에서는 동률이 많다.
따라서 이 smoke는 powered statistical evidence가 아니라 gate signal이다.
또한 judge criterion이 oracle card에서 파생되었으므로,
이 결과만으로 circularity가 제거되었다고 볼 수 없다.
```

### Judge-Ablation: Failure-Anchored Rejudging

추가 피드백 후, generation은 다시 돌리지 않고 기존 88개 candidate action을 **failure-anchored judge**로 재채점했다.

이 judge는 다음 정보를 보지 않는다.

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

| condition | n | repair_success | recurrence | concrete_action | repair_given_concrete | repair_without_concrete |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| broad_verification_card | 22 | 0.5455 | 0.3636 | 0.5455 | 1.0000 | 0.0000 |
| correct_mode_only_placebo | 22 | 0.4545 | 0.4545 | 0.4545 | 1.0000 | 0.0000 |
| hard_mismatched_abstracted_card | 22 | 0.4545 | 0.5000 | 0.4545 | 1.0000 | 0.0000 |
| oracle_abstracted_card | 22 | 0.6364 | 0.2727 | 0.6364 | 1.0000 | 0.0000 |

Judge-gap:

```text
abstract-criterion judge:
  oracle - broad = +0.3637
  oracle - hard_mismatch = +0.2273
  oracle - mode_only = +0.5000

failure-anchored judge:
  oracle - broad = +0.0909
  oracle - hard_mismatch = +0.1819
  oracle - mode_only = +0.1819
```

Case-level under failure-anchored judge:

```text
oracle strict best: 1 / 11 cases
oracle tied best: 4 / 11 cases
all equal or mixed: 5 / 11 cases
mode beats oracle: 1 / 11 cases
```

핵심 관찰:

```text
1. oracle advantage는 abstract-criterion judge에서보다 크게 줄었다.
2. 하지만 oracle - hard_mismatch 차이는 완전히 사라지지는 않았다.
3. repair_success와 concrete_action_rate는 여전히 같은 값을 보인다.
4. 따라서 현재 신호는 weak-real 가능성이 있지만,
   "정밀 attribution이 명확히 더 유용하다"는 증거로는 부족하다.
```

## 결과 해석

초기 abstract-criterion 결과만 보면 Experiment 2A의 신호가 literal gold diagnosis만으로 설명되지는 않는다는 쪽을 지지하는 듯했다.
하지만 failure-anchored 재채점 결과, 그 우위는 상당히 줄었다.

따라서 Experiment 3의 현재 해석은 보수적으로 바꿔야 한다.

```text
지원되는 약한 신호:
  맞는 abstract card가 hard mismatch보다 나을 가능성은 있다.

지원되지 않는 강한 신호:
  oracle abstract card가 generic/broad guidance보다 안정적으로 낫다.
  mode-only보다 action abstraction이 명확히 낫다.
  judge circularity가 완전히 제거되었다.
```

가장 정직한 해석:

```text
Exp3는 strong continue가 아니라 weak-positive / judge-dependent signal이다.
Exp4로 바로 가기 전에, Exp4의 primary judge는 failure-anchored 방식이어야 한다.
그리고 최종 thesis 증거는 runnable closed-loop task success에서 확보해야 한다.
```

하지만 아직 claim boundary는 좁다.

지원되는 해석:

```text
same-trace gold-point repair signal may partially survive abstraction,
but much of the abstract-criterion advantage is judge-dependent.
```

아직 지원되지 않는 해석:

```text
Failure Card is reusable memory.
Cross-trace transfer works.
Predicted Who&When attribution is useful.
Agent self-improves end-to-end.
```

결론:

```text
Do not rerun Experiments 1 and 2.
Do not scale same-trace powered runs yet.
Use the judge ablation as a decision point.
If continuing to Experiment 4, use failure-anchored judge as primary
and treat abstract-criterion judge as sensitivity only.
```

## 실험 구상

Experiment 2A와 같은 target case / same-trace gold intervention setup을 유지한다.

단, card와 judge를 바꾼다.

```text
target failed trace
-> gold decisive step 직전 prefix
-> condition-specific guidance
-> responsible agent next-action regeneration
-> two judge variants로 평가
```

실행은 두 단계로 나눈다.

```text
Exp3a:
  offline abstraction audit only
  generation 없음

Exp3b:
  minimal generation + decoupled judge 우선
```

Exp3a에서 abstracted card가 broad와 거의 구별되지 않거나 manipulation check를 통과하지 못하면 Exp3b를 바로 돌리지 않는다.

## 조건

Exp3b 최소 조건:

```text
1. broad_verification_card
2. oracle_specific_card_current
3. correct_mode_only_placebo
4. oracle_abstracted_card
5. hard_mismatched_abstracted_card
```

선택 조건:

```text
5. no_guidance
6. sanitized_raw_gold_explanation
```

이번 실험의 핵심 비교는 `oracle_specific_card_current`가 아니라 `oracle_abstracted_card`다.

추가된 `correct_mode_only_placebo`는 매우 중요하다. `oracle_abstracted_card`가 성공했을 때 그 이유가:

```text
1. 올바른 failure mode를 알려줬기 때문인지
2. mode를 넘어선 missing-check/action abstraction 때문인지
```

분리하기 위한 조건이다.

## Exp3a: Offline Abstraction Audit

Exp3a는 generation 전에 실행한다.

목적:

```text
1. oracle_abstracted_card가 broad_verification_card와 충분히 다른가?
2. intended failure mode / missing check type이 복원 가능한가?
3. literal source detail이 새지 않는가?
```

입력:

```text
Experiment 2A target cases
source mistake_reason
source task / ground truth / original failed action, leakage detection용
```

출력:

```text
oracle_abstracted_card
correct_mode_only_placebo
hard_mismatched_abstracted_card
removed_literal_terms
missing_check_type
abstract_corrective_action
abstraction_level
abstractiveness_rationale
```

Required artifact fields:

```text
abstraction_level:
  mode_only
  check_type
  action_schema
  too_literal

removed_literal_terms:
  entity
  value
  named object
  answer-like phrase
  original failed-action phrase

abstractiveness_rationale:
  why this card is narrower than broad_verification_card
  and why it is less literal than the source mistake_reason
```

Audit checks:

```text
1. leakage audit:
   literal entity, answer, original failed action paraphrase가 있는지 확인

2. manipulation check:
   blind evaluator가 card만 보고 intended failure mode와 missing_check_type을 복원 가능한지 확인

3. distinctness check:
   oracle_abstracted_card가 broad_verification_card의 generic checklist와 사실상 같은지 확인
```

Exp3a stop rule:

```text
if leakage medium/high:
  regenerate or drop

if manipulation check fails:
  renderer is too generic; fix renderer before generation

if oracle_abstracted_card ~= broad_verification_card in distinctness check:
  do not run Exp3b yet; revise abstraction granularity
```

Exp3a pass condition:

```text
mode/check recoverable
literal detail not recoverable
oracle_abstracted narrower than broad but less literal than source reason
```

## Exp3b: Minimal Generation Test

Exp3b는 Exp3a를 통과한 card만 사용한다.

목적:

```text
abstracted card가 actual next-action behavior를 broad/mode-only/mismatch보다 더 잘 바꾸는지 확인
```

우선순위:

```text
1. decoupled judge only smoke
2. 필요하면 diagnostic judge를 sensitivity analysis로 추가
```

## Card 정의

### oracle_specific_card_current

Experiment 2A에서 사용한 card다.

특징:

```text
case-specific compact diagnostic pattern 포함
sanitized mistake_reason 기반
same-trace에서는 강한 upper-bound condition
```

역할:

```text
Experiment 2A 결과와 연결되는 reference condition
```

### oracle_abstracted_card

새 핵심 조건이다.

agent-visible card에는 literal source case detail을 넣지 않는다.

이 renderer의 granularity가 Experiment 3의 독립변수다. 너무 coarse하면 broad verification과 구별되지 않고, 너무 specific하면 literal gold diagnosis leakage가 된다.

목표 granularity:

```text
mode-only보다 구체적이고
source literal보다 추상적이어야 한다.
```

즉 다음 수준을 목표로 한다.

```text
too coarse:
  factual verification failure

target granularity:
  current factual claim must be checked against an external source before handoff/finalization

too literal:
  verify the population value of France
```

포함 가능:

```text
failure-mode pattern
missing check type
abstract corrective action
applicable role/action context
check_before_next_action
```

금지:

```text
exact mistake_step
original failed action
gold answer
source entity / source value / source-specific answer hint
benchmark label
literal mistake_reason 문장
```

Renderer contract:

```text
input:
  source failure mode
  sanitized source mistake_reason
  source task, only for identifying literal entities to remove

output:
  failure_mode_label
  missing_check_type
  abstract_failure_pattern
  abstract_corrective_action
  check_before_next_action
  removed_literal_terms
```

`missing_check_type` 예:

```text
external factual verification
constraint enumeration
edge-case coverage check
tool-output validation
route-to-correct-agent check
do-not-finalize-before-evidence check
```

### broad_verification_card constraint

`broad_verification_card`는 강한 baseline이어야 하지만, kitchen-sink card가 되면 `oracle_abstracted_card`가 이길 수 없는 구조가 된다.

따라서 broad는 넓고 얕게 둔다.

```text
allowed:
  verify facts
  check constraints
  avoid unsupported assumptions
  maintain task relevance

forbidden:
  condition-specific missing_check_type
  failure-mode-specific corrective action
  source/target mode hint
  multiple detailed procedures that cover every mode
```

의도:

```text
broad:
  general caution baseline

oracle_abstracted:
  one missing-check type + one targeted abstract corrective action
```

Format/salience matching:

```text
broad_verification_card and oracle_abstracted_card must use:
  same visible card schema
  same section order
  similar length
  similar imperative strength
  similar warning language
```

즉, broad는 약한 baseline이 아니라 **wide-shallow but format-matched strong baseline**이어야 한다.

예:

```text
Bad:
  The prior agent failed to verify the population of France.

Good:
  Before relying on a current factual claim, verify it against an external source and state the evidence.
```

### correct_mode_only_placebo

올바른 failure mode만 알려주고, corrective action은 주지 않는 card-shaped placebo다.

예:

```text
Runtime Failure Card
Failure mode: unverified or inaccurate factual claim
Context: The next action may belong to this failure category.
No specific corrective action is provided.
```

목적:

```text
mode_only - broad_verification:
  correct failure-mode routing만의 가치

oracle_abstracted - mode_only:
  missing-check/action abstraction의 추가 가치
```

해석:

```text
mode_only ~= oracle_abstracted:
  가치는 card content보다 mode routing에 가까움.

oracle_abstracted > mode_only:
  추상 corrective action 자체가 기여함.
```

### hard_mismatched_abstracted_card

`oracle_abstracted_card`와 같은 abstraction procedure를 사용하되, source failure mode는 target과 orthogonal해야 한다.

목적:

```text
right abstraction vs wrong abstraction 비교
```

## Manipulation Check

Experiment 3는 abstracted card가 실제로 정보를 보존했는지 먼저 확인해야 한다.

조작 점검 질문:

```text
abstracted card만 보고 blind evaluator가
1. intended failure mode
2. missing check type
3. abstract corrective action
을 복원할 수 있는가?
```

판정:

```text
mode/check 복원이 안 됨:
  oracle_abstracted가 실패해도 "abstraction이 specificity를 죽였다"고 해석할 수 없음.
  renderer가 너무 generic한 artifact일 수 있음.

mode/check는 복원되지만 literal entity는 복원 안 됨:
  바람직한 abstraction.

literal entity/source answer가 복원됨:
  leakage. regenerate 또는 drop.
```

Manipulation check도 audit처럼 강제 규칙이어야 한다.

```text
failed manipulation check:
  regenerate or drop
```

## Judge Variants

Experiment 3는 judge를 두 개로 나눈다.

### Judge A: diagnostic judge

Experiment 2A와 유사하다.

```text
judge sees:
  original task
  prefix
  failure mode
  sanitized gold diagnostic reason
  original failed action
  candidate next action
```

역할:

```text
Experiment 2A와 연결되는 continuity check
```

### Judge B: decoupled judge

gold reason 원문과 original failed action을 보지 않는다.

```text
judge sees:
  original task
  prefix
  responsible agent
  abstract failure-mode rubric
  candidate next action
```

금지:

```text
sanitized mistake_reason 원문
original failed action 원문
gold answer
exact mistake_step
```

역할:

```text
card와 judge가 같은 gold diagnosis를 공유해서 생기는 순환성을 줄임
```

주의:

```text
Judge B는 gold reason과 original failed action을 보지 않기 때문에
"그 구체적 decisive error를 피했는가"를 직접 판단하기 어렵다.
```

따라서 Judge B에는 literal gold reason 대신 다음을 제공한다.

```text
abstract failure-mode rubric
missing-check-type success criterion
task-relevance anchor
responsible agent role
prefix context
```

Judge B success criterion 예:

```text
external factual verification:
  candidate must request, retrieve, cite, or explicitly verify the relevant source before relying on the claim.

constraint enumeration:
  candidate must enumerate or preserve the applicable constraints before computing/handoff.

tool-output validation:
  candidate must inspect or validate the tool output before passing it forward.
```

Judge B calibration check:

```text
recurs_same_failure가 거의 전부 false:
  recurrence metric is not meaningful under Judge B.

broad_verification_card가 과도하게 성공:
  Judge B may be measuring generic carefulness rather than repair.
```

이 경우 Judge B 결과는 main conclusion이 아니라 sensitivity analysis로 취급한다.

## 실행 규모

Exp3a는 offline audit이므로 모든 target case에 대해 먼저 실행한다.

Exp3b는 smoke로 충분하다.

```text
target cases:
  Experiment 2A에서 사용한 11 cases

conditions:
  4 core conditions

attempts:
  2

generations:
  11 × 4 × 2 = 88

judgments:
  110 × 2 judge variants = 220
```

비용을 줄이려면 먼저 decoupled judge만 돌려도 된다.

```text
minimum smoke:
11 × 5 × 2 generations
110 decoupled judgments
```

더 줄인 first pass:

```text
conditions:
  broad_verification_card
  correct_mode_only_placebo
  oracle_abstracted_card
  hard_mismatched_abstracted_card

generations:
  11 × 4 × 2 = 88

judge:
  decoupled only
```

## Metrics

핵심 metric:

```text
abstract_nudge_gap =
  repair_rate(oracle_abstracted_card)
  - repair_rate(broad_verification_card)

mode_routing_lift =
  repair_rate(correct_mode_only_placebo)
  - repair_rate(broad_verification_card)

abstract_action_lift =
  repair_rate(oracle_abstracted_card)
  - repair_rate(correct_mode_only_placebo)

abstract_right_vs_wrong =
  repair_rate(oracle_abstracted_card)
  - repair_rate(hard_mismatched_abstracted_card)

literal_to_abstract_drop =
  repair_rate(oracle_specific_card_current)
  - repair_rate(oracle_abstracted_card)
```

judge decoupling metric:

```text
judge_gap =
  repair_rate_under_diagnostic_judge
  - repair_rate_under_decoupled_judge
```

해석상 가장 중요한 것은 decoupled judge 기준 `abstract_nudge_gap`이다.

하지만 `abstract_action_lift`도 함께 본다.

```text
abstract_nudge_gap > 0 and abstract_action_lift > 0:
  mode routing뿐 아니라 추상 corrective action도 기여.

abstract_nudge_gap > 0 and abstract_action_lift ~= 0:
  효과는 content specificity보다 correct mode routing에 가까움.
```

## Power Note

Experiment 3는 Experiment 2A보다 더 약한 효과를 볼 가능성이 높다.

```text
literal oracle_specific_card effect >= abstract oracle effect
```

따라서 11 cases × 2 attempts smoke에서 `oracle_abstracted_card`가 broad보다 조금만 좋게 나오면, 그 결과는 no-go가 아니라 inconclusive다.

사전 규칙:

```text
small positive abstract_nudge_gap:
  do not pivot immediately
  run a small powered mini-run on the abstract_nudge_gap contrast

clear collapse:
  inspect renderer granularity, manipulation check, and judge calibration before pivot
```

Exp3a에서 renderer가 broad와 거의 같다는 결과가 나오면, Exp3b 결과가 약해도 attribution thesis 자체의 실패로 바로 해석하지 않는다.

```text
first suspect:
  renderer artifact

second suspect:
  broad baseline too broad

third suspect:
  true collapse of attribution-specific abstraction
```

## Go / No-Go

### Strong continue

```text
Exp3a manipulation check passes
oracle_abstracted_card > broad_verification_card
oracle_abstracted_card > correct_mode_only_placebo
oracle_abstracted_card > hard_mismatched_abstracted_card
decoupled judge에서도 우위가 유지됨
literal_to_abstract_drop이 작거나 감당 가능함
```

해석:

```text
Experiment 2A signal은 literal gold diagnosis 때문만은 아니다.
abstracted failure memory로 이어갈 다리가 있다.
```

다음 단계:

```text
Experiment 4: cross-trace transfer lite
```

### Soft continue

```text
Exp3a passes
oracle_abstracted_card > no_guidance
하지만 broad_verification_card와 비슷함
```

해석:

```text
failure memory는 도움이 되지만 attribution-specific abstraction은 약하다.
card abstraction schema를 다시 조정한다.
```

### Pivot warning

```text
oracle_abstracted_card ~= broad_verification_card
or hard_mismatched_abstracted_card >= oracle_abstracted_card
or decoupled judge에서 oracle advantage가 크게 붕괴
```

해석:

```text
Experiment 2A의 이득은 literal diagnosis / same-trace clairvoyance / judge coupling 때문일 수 있다.
Who&When same-trace repair를 powered run으로 키우면 매몰 위험이 크다.
```

가능한 pivot:

```text
1. failure attribution의 가치를 card content가 아니라 intervention targeting에서 찾는다.
2. runnable closed-loop benchmark로 이동한다.
3. generic failure memory vs attribution-specific memory를 비교하는 방향으로 thesis를 낮춘다.
```

## 구현 요구사항

```text
1. oracle_abstracted_card renderer 추가
2. hard_mismatched_abstracted_card renderer 추가
3. correct_mode_only_placebo 조건 추가
4. Exp3a offline audit command 추가
5. manipulation check 추가: mode/check 복원 가능 여부
6. distinctness check 추가: broad와 abstracted가 구별되는지 확인
7. leakage audit는 enforcing으로 운영: regenerate/drop
8. broad_verification_card를 wide-shallow baseline으로 제한
9. judge mode 추가: diagnostic / decoupled
10. Judge B에 missing-check-type success criterion 제공
11. judge mode를 judgment record에 저장
12. source literal terms leakage audit 추가
13. condition × judge_mode summary 출력
14. paired case-level contrast 유지
15. deterministic post-processing으로 judge subfield consistency check
16. case-level clustered bootstrap 또는 paired permutation test 추가
17. experiment_version / prompt_hash 기반 output path 또는 resume key 사용
```

## 산출물

```text
docs/experiment3.md
who_when_card_poc/data/interim/exp3_abstraction_audit.jsonl
who_when_card_poc/reports/exp3_abstraction_stress_summary.md
who_when_card_poc/data/runs/exp3_abstraction_stress_generations.jsonl
who_when_card_poc/data/judgments/exp3_abstraction_stress_judgments.jsonl
```

## Claim Boundary

Experiment 3가 통과해도 아직 말하면 안 되는 것:

```text
Failure Card is reusable memory.
Predicted attribution works.
Agent self-improves end-to-end.
Task success improves.
```

Experiment 3가 통과하면 말할 수 있는 것:

```text
The same-trace repair signal survives abstraction and is not solely explained by literal gold diagnosis or judge coupling.
```

한국어로는:

```text
same-trace repair 신호가 literal gold reason을 제거해도 유지되므로,
cross-trace transfer를 실험할 자격이 생긴다.
```
