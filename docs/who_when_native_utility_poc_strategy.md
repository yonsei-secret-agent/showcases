# Who&When-Native Failure Card Utility PoC Strategy

## 0. 핵심 입장

이 프로젝트의 출발점은 **Who&When**으로 두는 것이 맞다.

기존 질문은 다음이다.

```text
Which agent caused the failure, and when?
```

우리 질문은 여기서 한 단계 뒤로 이어져야 한다.

```text
If we know who failed and when, does that knowledge help repair or prevent the failure?
```

따라서 첫 PoC의 중심은 별도 mini-benchmark가 아니라, **Who&When failed trajectory 자체를 이용한 downstream utility 평가**여야 한다.

다만 용어를 정확히 나눠야 한다.

```text
Who&When-only로 가능한 것:
  trace-level counterfactual repair utility
  attribution quality와 card utility의 관계
  same-failure recurrence / error avoidance 평가
  cross-trace transfer 평가

Who&When-only로 바로 주장하기 어려운 것:
  original task full rerun success
  실제 실행 환경에서의 end-to-end rescue rate
```

즉, 더 정확한 결론은 이것이다.

```text
Who&When-native first.
Execution-rescue evidence is optional but desirable.
Full execution rescue claim은 replayable subset에서만 주장한다.
```

기존 `Who&When-first, but not Who&When-only`라는 표현은 너무 방어적이다. 더 정확한 표현은 다음이다.

```text
Who&When-native first, execution-rescue optional but desirable.
```

논문 시작점이 Who&When이라면 첫 실험도 Who&When 안에서 닫히는 형태가 더 자연스럽다. 단, 이 실험이 말하는 것은 **end-to-end task rescue**가 아니라 **decisive-step counterfactual repair**임을 끝까지 유지해야 한다.

---

## 1. 근거

Who&When은 failed multi-agent trajectory에서 다음을 찾는 benchmark다.

```text
who  = failure-responsible agent
when = decisive error step
why  = natural language failure explanation
```

Who&When 프로젝트 설명에 따르면 dataset은 127개 multi-agent system의 failure log로 구성되고, 각 failure는 responsible agent와 decisive error step으로 annotation되어 있다. repo README 기준으로는 184 annotated failure tasks가 포함되어 있고, 대표 attribution method로 `all_at_once`, `step_by_step`, `binary_search`가 제공된다.

중요한 점은 decisive error step의 의미다.

```text
decisive error step =
the earliest mistake whose correction would change failure into success
```

이 정의는 우리 실험에 매우 유리하다. 우리가 실제 full rerun을 못 하더라도, **decisive error step 직전 prefix에서 다음 action을 다시 생성시켜 gold failure가 회피되는지**를 볼 수 있기 때문이다.

따라서 Who&When은 단순한 card source가 아니라, 다음 실험을 직접 만들 수 있는 primary benchmark다.

```text
failed trace prefix before decisive step
        +
attribution-derived Failure Card
        ↓
counterfactual next action generation
        ↓
does the action avoid or repair the decisive error?
```

---

## 2. 이 PoC의 정확한 주장

첫 PoC의 주장은 full task success보다 좁고 명확해야 한다.

### Primary claim

```text
Gold Who&When attribution can be converted into a standardized runtime Failure Card that reduces recurrence of the decisive error in trace-prefix counterfactual repair.
```

한국어로 쓰면:

```text
정확한 Who&When attribution은 표준화된 runtime Failure Card로 변환되었을 때,
decisive error point에서 같은 실패를 반복하지 않도록 만든다.
```

이 claim은 의도적으로 좁다. Phase 2/3만으로는 "original task를 고쳤다"거나 "end-to-end success가 올랐다"고 주장하지 않는다.

### Secondary claim

```text
Attribution quality predicts downstream card utility.
```

즉 다음 gradient를 보여주는 것이 핵심이다.

```text
Oracle / Gold Runtime Card
  > Sanitized Raw Gold Explanation
  >= Strong Generic Guideline
  > No Guidance
  > Wrong / Mismatched Card
```

그리고 real method는 이 사이 어딘가에 놓인다.

```text
Oracle Runtime Card
  > Step-by-Step / All-at-Once / Binary-Search Predicted Runtime Cards
  > Wrong Card
```

완전한 단조성까지 첫 PoC에서 요구할 필요는 없다. 하지만 최소한 다음은 보여야 한다.

```text
Oracle Runtime Card repair rate > No Guidance repair rate
Oracle Runtime Card same-failure recurrence < No Guidance recurrence
Wrong / Mismatched Card는 효과가 낮거나 negative transfer를 만든다
```

---

## 3. 전체 실험 구조

권장 구조는 다음이다.

```text
Phase 0. Who&When reproduction
Phase 1. Attribution-to-Card conversion
Pre-Phase 2. Baseline recurrence pretest
Phase 2A. Gold-intervention-point trace-prefix repair
Phase 2B. Predicted-intervention-point trace-prefix repair
Phase 3. Who&When cross-trace transfer
Phase 4. Replayable subset direct rescue
Phase 5. Supplementary mini-benchmark, only if needed
```

중요한 순서는 이렇다.

```text
먼저 Who&When 안에서 utility를 보인다.
Gold intervention point에서 oracle upper bound를 확인한다.
그다음 predicted who/when으로 실제 attribution method utility를 본다.
cross-trace transfer로 reusable guidance 주장을 보강한다.
그다음 replay 가능한 subset에서 full rerun rescue를 시도한다.
그래도 external execution evidence가 부족할 때만 mini-benchmark를 보조로 붙인다.
```

---

## Phase 0. Who&When Reproduction

### Goal

Who&When repo와 dataset을 재현해 우리가 논문의 기본 benchmark 위에 서 있음을 확인한다.

### Inputs

```text
Who&When failed trajectories
gold responsible agent
gold decisive error step
gold natural language explanation
```

### Run

```text
Run all_at_once
Run step_by_step
Run binary_search
Evaluate agent-level accuracy
Evaluate step-level accuracy
Export per-case predictions
```

### Outputs

```text
outputs/who_when_predictions.jsonl
outputs/who_when_eval_summary.json
outputs/who_when_case_index.csv
```

### Case index fields

```text
case_id
source_split
source_system_id
source_dataset_type
task_query
ground_truth_answer
agent_names
num_steps
gold_responsible_agent
gold_decisive_step
gold_explanation
pred_all_at_once_agent
pred_all_at_once_step
pred_all_at_once_reason
pred_step_by_step_agent
pred_step_by_step_step
pred_step_by_step_reason
pred_binary_search_agent
pred_binary_search_step
pred_binary_search_reason
candidate_failure_mode
actionability_label
replayability_label
no_guidance_recurrence_rate
main_set_eligible
notes
```

### Why this matters

이 단계는 utility 평가가 아니다. 목적은 attribution source를 확보하고, gold와 predicted attribution이 어떤 형식으로 나오는지 확인하는 것이다.

---

## Phase 1. Attribution-to-Card Conversion

### Goal

Who&When의 gold / predicted attribution을 동일한 Failure Card schema로 변환한다.

### Diagnostic attribution record

```json
{
  "case_id": "string",
  "attribution_source": "gold | all_at_once | step_by_step | binary_search | partial | wrong | mismatched",
  "responsible_agent": "string",
  "decisive_step": "number | string",
  "failure_mode": "string",
  "trigger": "string",
  "violated_requirement": "string",
  "propagation": "string",
  "observable_symptom": "string",
  "evidence_span": "string"
}
```

이 record는 분석/저장/평가용이다. 여기에는 `decisive_step`, `evidence_span`, 원래 실패 action, gold explanation 같은 진단 정보를 포함할 수 있다.

### Runtime Failure Card schema

Agent에게 실제 주입되는 것은 diagnostic record가 아니라 **runtime Failure Card**다. 이 schema에는 미래 시점 정보나 원래 실패 문장을 넣지 않는다.

```json
{
  "card_id": "string",
  "attribution_source": "gold | all_at_once | step_by_step | binary_search | partial | wrong | mismatched",
  "failure_mode": "string",
  "trigger_pattern": "string",
  "propagation": "string",
  "do": "string",
  "do_not": "string",
  "check_before_next_action": "string",
  "applicable_when": "string"
}
```

### Hidden metadata

다음 필드는 저장 파일에는 남길 수 있지만, runtime prompt에는 절대 노출하지 않는다.

```text
source_case_id
source_step / decisive_step
evidence_span
original failed action
task-specific gold answer
exact original failure wording
"you originally failed at step t*" style phrasing
```

### Agent-visible fields

Agent에게 보이는 card는 일반화된 preventive guidance여야 한다.

```text
failure_mode
trigger_pattern
do
do_not
check_before_next_action
applicable_when
```

### Leakage rule

Gold attribution으로 oracle card를 만들더라도, agent-visible runtime card는 다음처럼 쓰면 안 된다.

```text
Bad:
You will fail at step 7 by omitting constraint X. Include constraint X now.

Good:
When handing off a task with constraints, explicitly preserve every user constraint,
including filters, tie-break rules, output format, and verification criteria.
Before acting, compare your next action against the original user request.
```

### Conditions

첫 실험 조건은 최소 7개로 둔다.

```text
1. No Guidance
2. Strong Generic Guideline
3. Sanitized Raw Gold Attribution Explanation
4. Gold / Oracle Runtime Failure Card
5. Predicted all_at_once Runtime Failure Card
6. Predicted step_by_step Runtime Failure Card
7. Predicted binary_search Runtime Failure Card
8. Wrong / Mismatched Failure Card
```

`Sanitized Raw Gold Attribution Explanation`은 raw explanation을 그대로 넣는 조건이 아니다. step number, original failed action, gold answer, future-failure wording을 제거한 뒤 넣는다. 그래야 "원인 설명 자체"와 "구조화된 runtime card"의 차이를 비교할 수 있다.

여력이 있으면 다음을 추가한다.

```text
9. Partial Card: who만 맞고 when은 틀림
10. Partial Card: when만 맞고 who는 틀림
11. Partial Card: who/when은 맞지만 why가 약함
```

이 partial 조건은 중요하다. Who&When의 기본 label인 `who`와 `when` 중 무엇이 utility에 더 중요한지 분리할 수 있기 때문이다.

### Renderer control

Card renderer는 모든 condition에 대해 고정한다.

```text
same runtime schema
same section order
similar token length
same injection position
same base prompt
no extra polishing for oracle cards
no source step / evidence span / original failed action leakage
no task-specific gold answer leakage
```

### Conversion audit

각 card는 생성 후 간단한 leakage audit을 통과해야 한다.

```text
Does the runtime text mention the exact original failed step number?
Does it quote or paraphrase the original failed action too specifically?
Does it reveal the gold answer?
Does it tell the agent what will happen in the future?
Does it contain details unavailable at the prefix point?
```

하나라도 yes면 runtime card에서 제거하거나 일반화한다.

---

## Pre-Phase 2. Baseline Recurrence Pretest

Phase 2를 시작하기 전에 no-guidance baseline이 실제로 같은 실패를 반복하는지 확인해야 한다. 같은 prefix에서 새 모델이 next action을 생성하면, 아무 guidance가 없어도 원래 decisive error를 피할 수 있기 때문이다.

### Goal

```text
Identify cases where the original failure is non-trivially recurrent under no guidance.
```

### Protocol

각 candidate case에 대해 다음을 먼저 실행한다.

```text
1. Cut the trajectory at t*-1.
2. Do not inject any card or failure explanation.
3. Regenerate the next action 3-5 times.
4. Judge whether each generation repeats the same decisive error.
5. Estimate no_guidance_recurrence_rate.
```

### Main set filter

Primary analysis는 다음 조건을 만족하는 case를 중심으로 한다.

```text
high actionability
no_guidance_recurrence_rate >= 40-50%
judge confidence is not low
trace prefix has enough context to make a next action
```

하지만 전체 case 결과도 별도로 보고한다.

```text
All eligible cases:
  shows generality

Failure-prone subset:
  shows card utility when baseline recurrence exists
```

### Why this matters

이 filter가 없으면 다음 현상이 생긴다.

```text
Original trace failed.
No Guidance regeneration already repairs it.
Oracle Runtime Card also repairs it.
Measured oracle lift becomes small.
```

이 경우 card가 쓸모없는 것이 아니라 baseline regeneration이 이미 강한 것이다. 따라서 main utility 분석은 failure-prone subset과 전체 set을 분리해야 한다.

---

## Phase 2. Who&When Trace-Prefix Counterfactual Repair

이 단계가 첫 PoC의 primary experiment다.

### Core idea

Gold decisive step `t*` 직전까지의 trajectory prefix를 잘라낸다. 그다음 condition별 runtime guidance를 넣고, next action을 다시 생성하게 한다.

```text
Original failed trajectory:
step 1, step 2, ..., step t*-1, step t* [decisive error], ..., final failure

Counterfactual repair input:
task + agent roles + trajectory prefix up to the intervention point + runtime guidance condition

Output:
new candidate step t*

Evaluation:
does the new step avoid or repair the gold decisive error?
```

Phase 2는 반드시 두 층으로 나눈다.

```text
Phase 2A. Gold-intervention-point repair
Phase 2B. Predicted-intervention-point repair
```

### Phase 2A. Gold-intervention-point repair

2A는 oracle upper bound와 card content utility를 확인하는 실험이다.

```text
Intervention agent:
  gold_responsible_agent

Intervention time:
  gold_decisive_step = t*

Question:
  If we intervene at the true critical point, does the card content help?
```

2A에서는 `who`와 `when`을 이미 gold로 고정한다. 따라서 이 결과만으로는 "attribution method가 어디에 개입해야 하는지 잘 찾는다"는 주장을 할 수 없다.

### Phase 2B. Predicted-intervention-point repair

2B는 실제 attribution method output의 utility를 보는 실험이다.

```text
Intervention agent:
  predicted_responsible_agent

Intervention time:
  predicted_decisive_step

Question:
  Does the attribution method identify the right intervention point and generate useful guidance?
```

2B에서는 predicted `who`나 `when`이 틀리면 잘못된 agent 또는 잘못된 prefix에서 개입하게 된다. 이 때문에 2B가 attribution utility에 더 가깝다.

### Experimental units

```text
Phase 2A:
case_id
gold_responsible_agent
gold_decisive_step = t*
trajectory_prefix = steps <= t*-1
condition
seed

Phase 2B:
case_id
predicted_responsible_agent
predicted_decisive_step
trajectory_prefix = steps <= predicted_decisive_step - 1
condition
seed
```

### Prompt structure

```text
System:
You are the original agent named {responsible_agent}.

Context:
Original task
Agent roster
Conversation / trajectory prefix up to the intervention point

Guidance:
Condition-specific runtime card or baseline text

Instruction:
Produce the next message/action for this agent.
Do not mention that this is a benchmark.
```

The prompt must not include:

```text
gold decisive step number
source step number
original failed action
future-failure wording
task-specific gold answer
hidden evaluation labels
```

### Why this is valid

Who&When의 decisive step은 failure를 success로 바꿀 수 있는 가장 이른 critical mistake로 정의된다. 따라서 `t*` 직전에서 better next step을 생성하는지는 attribution utility를 직접 보는 trace-level downstream task가 된다.

이 실험은 full rerun success는 아니지만, 다음 주장은 할 수 있다.

```text
The card helps the responsible agent avoid the decisive error at the critical point of the failed trajectory.
```

더 강한 attribution-method claim은 Phase 2B와 Phase 3이 함께 있어야 한다.

---

## 4. Phase 2 Metrics

모든 metric은 최소한 다음 세 split으로 따로 보고한다.

```text
All eligible cases
Failure-prone subset after recurrence pretest
High-confidence judge subset
```

또한 Phase 2A와 Phase 2B 결과를 섞지 않는다.

```text
Phase 2A:
  gold intervention point에서 card content utility를 측정

Phase 2B:
  predicted intervention point에서 attribution method utility를 측정
```

### Primary metric: repair rate

```text
Repair Rate =
P(candidate next step avoids the gold decisive error)
```

예시는 다음과 같다.

```text
gold failure: agent ignored required constraint
repair success: candidate explicitly carries or checks that constraint

gold failure: agent used unverified tool output
repair success: candidate verifies, reruns, or flags uncertainty before proceeding

gold failure: agent prematurely terminates
repair success: candidate continues with the missing action or requests required info
```

### Secondary metric: same-failure recurrence

```text
Same-Failure Recurrence =
P(candidate repeats the same failure mode as the original decisive step)
```

### Negative transfer

```text
Negative Transfer =
P(card condition introduces a new error that No Guidance did not introduce)
```

### Card adherence

```text
Card Adherence =
P(candidate action follows the do / do_not / check instruction)
```

### Attribution-utility correlation

각 predicted attribution에 대해 attribution accuracy score를 만들고 card utility와 상관을 본다.

```text
attribution_accuracy_score:
  who_correct: 0/1
  when_exact: 0/1
  when_near: within +/- 1 or same subepisode
  why_match: judge/human label

utility_score:
  repair_success: 0/1
  recurrence_avoided: 0/1
  negative_transfer: 0/1
```

분석은 최소한 다음을 본다.

```text
Spearman correlation between attribution_accuracy_score and utility_score
paired difference vs No Guidance
paired difference vs Strong Generic Guideline
```

### Predicted intervention validity

Phase 2B에서는 다음을 추가로 본다.

```text
intervention_agent_correct:
  predicted agent == gold responsible agent

intervention_time_exact:
  predicted step == gold decisive step

intervention_time_near:
  predicted step is within an accepted local window

intervention_prefix_valid:
  prefix is not after the original decisive error
```

이 metric이 필요한 이유는 predicted card가 실패했을 때 원인을 분리하기 위해서다.

```text
Bad card content
Wrong responsible agent
Wrong intervention time
Intervention after failure already occurred
```

---

## 5. Phase 2 Evaluation Protocol

### Judge input

Judge는 condition label을 보지 않는다.

```text
original task
agent role
trajectory prefix up to the intervention point
runtime guidance text, if applicable, with source/method labels removed
gold decisive error step
gold failure explanation
candidate next step
```

`gold decisive error step`과 `gold failure explanation`은 judge에게만 주는 평가 정보다. Candidate agent prompt에는 이 정보를 넣지 않는다.

### Judge output

```json
{
  "repair_success": true,
  "same_failure_recurrence": false,
  "new_error_introduced": false,
  "card_adherence_visible": true,
  "reason": "short explanation",
  "confidence": "high | medium | low"
}
```

### Evaluation layers

```text
1. Rule-based checks where possible
2. Blind LLM judge for semantic cases
3. Human audit for at least 20%, or at least 30 cases
```

### Failure-mode-specific repair criteria

Judge는 "답변이 좋아 보이는가"가 아니라, 원래 decisive error가 실제로 회피됐는지를 본다.

```text
ignored constraint / missing requirement:
  repair_success only if candidate explicitly preserves, checks, or asks about the missing constraint.

unverified tool output:
  repair_success only if candidate verifies the tool result, requests evidence, reruns, or marks uncertainty before relying on it.

premature finalization:
  repair_success only if candidate refuses to finalize and performs the missing action, asks for missing information, or continues the required workflow.

wrong routing / wrong tool / wrong agent:
  repair_success only if candidate routes to the correct agent/tool, invokes the missing capability, or blocks the incorrect route.

role responsibility confusion:
  repair_success only if candidate clarifies ownership or hands off to the responsible role with the required context.

insufficient evidence gathering:
  repair_success only if candidate gathers the missing evidence or explicitly conditions the answer on unavailable evidence.

calculation or code execution mistake:
  repair_success only if candidate recomputes, validates, tests, or catches the specific error pattern before proceeding.
```

### Important control

Judge에게 다음을 노출하지 않는다.

```text
condition name
whether the card is oracle or predicted
which method generated the card
expected ordering
```

---

## Phase 3. Who&When Cross-Trace Transfer

Phase 2는 same trace 안의 counterfactual repair다. 이것만으로도 trace-level utility claim은 가능하지만, Failure Card가 reusable guidance라는 주장을 하려면 cross-trace transfer가 사실상 필수다.

### Core idea

Source failure에서 만든 card를 같은 failure mode의 held-out target trace prefix에 적용한다.

```text
source Who&When failure case
        ↓
Failure Card
        ↓
held-out target Who&When trace prefix before t*
        ↓
candidate next step
        ↓
repair / recurrence evaluation
```

### Split rule

Leakage를 막기 위해 split은 case random이 아니라 더 강하게 잡는다.

```text
preferred:
  split by source_system_id

acceptable:
  split by task family + system type

avoid:
  same original task or near-duplicate task appears in both source and target
```

### Failure mode taxonomy

처음에는 너무 세분화하지 않는다.

```text
missing requirement / ignored constraint
wrong tool use or wrong subtask routing
unverified intermediate result
premature finalization
role responsibility confusion
insufficient evidence gathering
calculation or code execution mistake
```

각 case에 failure mode를 붙이는 방식은 다음이 현실적이다.

```text
LLM draft label
human spot check
disagreement cases manually resolve
low-confidence cases exclude from main analysis
```

### Conditions

```text
1. No Guidance
2. Strong Generic Guideline
3. Single-source same-mode Oracle Runtime Card
4. Single-source same-mode Predicted Runtime Card
5. Mismatched-mode Card
6. Random Card
```

Main Phase 3은 single-source transfer로 둔다. 즉 source case 하나에서 만든 card가 held-out target case에 transfer되는지 본다.

### Optional secondary transfer: schema-level card

여력이 있으면 같은 failure mode의 여러 source cards를 요약해 reusable schema-level card를 만든다.

```text
multiple source cards from same failure mode
        ↓
schema-level runtime Failure Card
        ↓
held-out target trace prefixes
```

이 조건은 강한 결과를 만들 수 있지만, main claim과는 분리한다. 너무 앞세우면 연구 질문이 "attribution-to-card utility"에서 "failure schema induction"으로 커질 수 있다.

Recommended placement:

```text
Main result:
  single-source same-mode transfer

Secondary result:
  schema-level aggregated card transfer
```

### Main metric

```text
Transfer Repair Rate =
P(source card improves target trace-prefix repair)
```

### Good result pattern

```text
Same-mode Oracle Runtime Card
  > Same-mode Predicted Runtime Card
  >= Strong Generic Guideline
  > No Guidance
  > Mismatched-mode Card
```

Schema-level card를 추가한 경우에는 별도 plot으로 보고한다.

```text
Schema-level Same-mode Card
  >= Single-source Same-mode Card
  > Strong Generic Guideline
```

이 phase가 성공하면 다음 주장이 가능하다.

```text
Who&When-derived Failure Cards are not only post-hoc explanations of a single trace;
they can transfer as reusable execution guidance to held-out failures of the same type.
```

---

## Phase 4. Replayable Subset Direct Rescue

이 단계는 가능하면 강력하지만, 첫 PoC의 필수 조건으로 두면 위험하다.

### Goal

Who&When original task 중 실제 rerun 가능한 subset을 찾아 full execution rescue를 측정한다.

### Eligibility

```text
task input is available
agent roles can be reconstructed
tool calls can be reproduced or mocked
required files/data are accessible
success checker can be defined
no-card baseline still fails often enough
```

### Protocol

```text
1. Select replayable candidate cases
2. Rerun without card
3. Keep cases where no-card baseline fails
4. Rerun with card conditions
5. Measure full task success and same-failure recurrence
```

### Main metric

```text
Direct Rescue Rate =
P(card run succeeds | no-card rerun failed)
```

### Claim boundary

이 phase가 있어야 다음 주장이 가능하다.

```text
The card repaired original Who&When tasks under rerun.
```

Phase 2와 3만으로는 이 표현을 쓰면 안 된다. 대신 다음 표현을 써야 한다.

```text
The card improved counterfactual repair at the decisive error point.
The card reduced same-failure recurrence in held-out Who&When trace prefixes.
```

---

## Phase 5. Supplementary Mini-Benchmark

Mini-benchmark는 버리는 것이 아니라, 위치를 낮춘다.

### When to use

```text
Who&When cases are mostly not replayable
Phase 2/3 show trace-level utility but reviewers ask for execution-level evidence
specific failure modes need objective success checkers
```

### Role

```text
not the primary benchmark
not the origin of the research question
supplementary execution-level validation
```

### Recommended setup

```text
Planner -> Executor -> Reviewer
small data-analysis / table reasoning tasks
objective checker
target failure mode matched to Who&When taxonomy
```

### Claim after mini-benchmark

```text
Who&When-derived cards also improve execution-level success in a controlled runnable setting.
```

이 claim은 좋지만, 논문 중심은 계속 Who&When에 둔다.

---

## 6. Minimum Viable PoC

가장 작은 의미 있는 실험은 다음이다.

```text
Candidate cases:
  40-60 Who&When cases with high actionability

Pretest:
  No Guidance x 3-5 generations per case
  estimate same-failure recurrence

Main cases:
  30 cases passing recurrence filter
  no_guidance_recurrence_rate >= 40-50%

Phase 2A conditions:
  No Guidance
  Strong Generic Guideline
  Sanitized Raw Gold Explanation
  Oracle Runtime Failure Card
  One predicted method card
  Wrong / Mismatched Card

Seeds:
  2

Total:
  pretest: 40-60 cases x 3-5 generations
  main: 30 cases x 6 conditions x 2 seeds = 360 generations
```

첫 주에 너무 크면 smoke로 줄인다.

```text
Pretest:
  15 candidate cases x 3 no-guidance generations

Main smoke:
  10 recurring cases x 5 conditions x 1 seed = 50 generations
```

Smoke에서 봐야 하는 것은 p-value가 아니라 signal이다.

```text
Oracle Runtime Card가 No Guidance보다 명확히 좋은가?
Wrong Card가 좋아지지 않는가?
Judge rubric이 일관적으로 작동하는가?
Failure modes가 card로 actionable한가?
No Guidance recurrence가 충분히 존재하는가?
Runtime card에 leakage가 없는가?
```

---

## 7. Analysis Tables

### Table 1. Who&When reproduction

```text
method | agent_acc | step_exact_acc | step_near_acc | cost | avg_calls
```

### Table 2. Trace-prefix repair

```text
phase | condition | repair_rate | recurrence_rate | negative_transfer | card_adherence
```

### Table 3. Predicted method utility

```text
method | who_acc | when_acc | why_match | intervention_validity | repair_rate | delta_vs_no_guidance
```

### Table 4. Cross-trace transfer

```text
source_card_type | target_failure_mode | repair_rate | recurrence_rate | delta_vs_generic
```

### Table 5. Baseline recurrence and eligibility

```text
failure_mode | candidate_cases | mean_no_guidance_recurrence | main_set_cases | excluded_cases
```

### Table 6. Leakage audit

```text
condition | cards_checked | leakage_flags | fixed_before_run | excluded_cards
```

### Figure 1. Main causal chain

```text
Who&When attribution accuracy
        ↓
Failure Card quality
        ↓
decisive-step repair rate
        ↓
same-failure recurrence reduction
```

### Figure 2. Utility gradient

```text
Oracle Runtime > Sanitized Raw Gold > Generic > No Guidance > Wrong
```

---

## 8. Go / No-Go Criteria

### Strong go

```text
Phase 2A Oracle Runtime Card repair rate > No Guidance by at least 10-15 percentage points
Phase 2A Oracle Runtime Card recurrence rate < No Guidance by at least 10 percentage points
Oracle Runtime Card beats or ties Strong Generic Guideline
Wrong / Mismatched Card does not improve and may hurt
Phase 2B predicted card utility roughly tracks attribution correctness
Phase 3 same-mode transfer beats mismatched/random card
Runtime card leakage audit passes
```

### Soft go

```text
Phase 2A Oracle Runtime Card works, but Phase 2B predicted cards are noisy.
```

Interpretation:

```text
Failure attribution has downstream utility in principle,
but current automated methods are not accurate/actionable enough.
```

### Interesting negative result

```text
Attribution accuracy does not correlate with card utility.
```

Interpretation:

```text
Current who/when metrics may not capture what makes attribution useful for downstream repair.
```

This is still publishable if the experiment is clean.

### No-go for current design

```text
Phase 2A Oracle Runtime Card does not improve trace-prefix repair over No Guidance on the failure-prone subset.
```

Likely causes:

```text
card is too generic
card is injected at the wrong point
candidate cases are not actionable
baseline recurrence filter is too weak
judge rubric is too noisy
decisive step cannot be repaired by local next-step change
runtime card was over-sanitized and lost actionable content
```

Do not scale predicted methods until Phase 2A oracle utility is visible and leakage checks pass.

---

## 9. Recommended Paper Framing

### Abstract-level framing

```text
Existing MAS failure attribution benchmarks ask whether a model can identify who failed and when.
We ask whether such attribution is useful after identification.
Using Who&When as the primary benchmark, we convert gold and predicted attributions into standardized runtime Failure Cards and evaluate whether they reduce recurrence of the decisive error in trace-prefix counterfactual repair and held-out trace transfer.
```

### Contribution list

```text
1. We extend Who&When-style failure attribution from offline localization to downstream utility evaluation.
2. We distinguish diagnostic attribution records from agent-visible runtime Failure Cards to control leakage.
3. We introduce Failure Cards as a standardized interface for turning attributions into execution guidance.
4. We propose trace-prefix counterfactual repair as a Who&When-native utility task.
5. We separate gold-intervention utility from predicted-intervention utility.
6. We measure whether attribution accuracy predicts repair utility.
7. We optionally validate execution-level rescue on replayable subsets or controlled runnable tasks.
```

### Claim wording

Use:

```text
trace-level downstream utility
counterfactual repair at the decisive error step
same-failure recurrence reduction
held-out trace transfer
gold-intervention-point utility
predicted-intervention-point utility
```

Avoid unless Phase 4 succeeds:

```text
fixed the original task
improved original Who&When task success
end-to-end rescue on the benchmark
```

---

## 10. Concrete First Week Plan

### Day 1: Reproduce Who&When

```text
clone repo
install requirements
load dataset
run one method on small subset
run evaluation
inspect raw trace format
```

Deliverable:

```text
who_when_reproduction_notes.md
```

### Day 2: Build case index and audit labels

```text
parse task/query/agents/steps
extract gold who/when/why
join predicted outputs
create case index
draft actionability labels
draft failure mode labels
draft replayability labels
```

Deliverable:

```text
who_when_case_index.csv
```

### Day 3: Build card converter and leakage audit

```text
define attribution tuple
define diagnostic attribution record
define runtime Failure Card schema
render oracle/predicted/wrong runtime cards
check token length parity
run leakage audit
```

Deliverable:

```text
failure_cards.jsonl
card_rendering_examples.md
card_leakage_audit.csv
```

### Day 4: Baseline recurrence pretest

```text
cut trace at t*-1
run No Guidance 3-5 times per candidate case
judge same-failure recurrence
select failure-prone main set
```

Deliverable:

```text
baseline_recurrence_pretest.csv
main_case_selection.md
```

### Day 5: Build Phase 2A trace-prefix repair runner

```text
cut trace at t*-1
construct responsible-agent prompt
inject runtime card or baseline condition
generate candidate next actions
save outputs
```

Deliverable:

```text
phase2a_counterfactual_generations.jsonl
```

### Day 6: Build judge

```text
implement blind judge prompt
add failure-mode-specific repair criteria
add rule-based checks where possible
run judge on smoke outputs
audit manually
```

Deliverable:

```text
repair_judgments.jsonl
judge_audit_notes.md
```

### Day 7: Smoke analysis and Phase 2B design check

```text
10 recurring cases
5-6 Phase 2A conditions
1-2 seeds
compute repair/recurrence/negative transfer
inspect predicted who/when outputs for Phase 2B
write result memo
```

Deliverable:

```text
who_when_native_poc_smoke_report.md
phase2b_design_notes.md
```

---

## 11. Final Recommendation

내 기준에서 가장 좋은 설계는 다음이다.

```text
Precondition:
  actionability audit + no-guidance recurrence pretest

Primary:
  Phase 2A Who&When gold-intervention trace-prefix repair

Attribution-method utility:
  Phase 2B predicted-intervention trace-prefix repair

Main transfer:
  Who&When cross-trace same-failure-mode transfer

Strong additional evidence:
  replayable Who&When subset direct rescue

Fallback / supplement:
  controlled mini-benchmark execution rescue
```

이렇게 두면 논문의 중심이 흔들리지 않는다.

```text
The project starts from Who&When.
The first utility task is native to Who&When.
The runtime card avoids diagnostic leakage.
Execution-level rerun is added only where the benchmark permits it.
```

이 구조가 가장 방어 가능하고, 동시에 네가 처음 잡은 “Who&When에서 시작한다”는 연구 정체성과도 가장 잘 맞는다.

---

## References

- Who&When / Agents Failure Attribution repo: https://github.com/ag2ai/Agents_Failure_Attribution
- Project page: https://ag2ai.github.io/Agents_Failure_Attribution/
