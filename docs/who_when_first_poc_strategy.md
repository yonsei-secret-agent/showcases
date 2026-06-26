# Who&When-first Failure Card PoC Strategy

## 0. 핵심 결론

**Who&When을 먼저 돌려보는 접근은 좋다.** 다만 이 접근을 `Who&When-only` 실험으로 만들면 안 된다.

Who&When은 이미 수집된 failed multi-agent trajectories에 대해 **어느 agent가, 어느 step에서 실패를 유발했는지**를 찾는 attribution benchmark다. 따라서 Who&When을 돌리면 우리가 새로 얻는 것은 주로 다음 세 가지다.

1. 실패 로그와 gold attribution annotation
2. `all_at_once`, `step_by_step`, `binary_search` 등 기존 attribution method의 predicted attribution
3. gold / predicted attribution을 Failure Card로 변환하기 위한 source material

하지만 Who&When을 돌리는 것만으로는 다음 주장을 바로 증명할 수 없다.

> Failure Card를 넣었더니 기존에 실패하던 MAS 실행이 성공으로 바뀌었다.

이 주장을 하려면 **재실행 가능한 baseline failure case**와 **card 주입 후 rerun 결과**가 필요하다. 따라서 권장 설계는 다음이다.

```text
Who&When-first, but not Who&When-only.

Who&When = offline attribution/card source + 기존 연구 anchor
Runnable mini-benchmark = downstream utility / rescue-rate 검증 환경
```

---

## 1. 이 실험이 답하려는 질문

### Main question

```text
Failure Attribution 결과를 Failure Card로 변환해 MAS에 주입하면,
이전에는 실패하던 유사 task 실행이 성공으로 rescue되는가?
```

### More precise research question

```text
Attribution quality가 높을수록, attribution-derived Failure Card의 downstream utility도 높아지는가?
```

즉 이 PoC는 Failure Card 자체를 제안하는 실험이 아니라, **Failure Attribution의 downstream evaluation**이다.

---

## 2. Who&When을 먼저 쓰는 이유

Who&When-first 접근의 장점은 크다.

### 2.1 기존 연구와 바로 연결된다

우리 연구가 완전히 새 benchmark를 만든다는 느낌이 아니라, 기존 MAS Failure Attribution benchmark를 downstream evaluation으로 확장한다는 포지셔닝을 만들 수 있다.

### 2.2 실패 로그와 gold attribution이 이미 있다

Who&When에는 failed trajectory, responsible agent, decisive error step, natural language failure explanation이 포함되어 있다. 이것은 Failure Card 생성을 위한 좋은 원천 데이터다.

### 2.3 기존 attribution method output을 바로 비교할 수 있다

Who&When repo의 대표 method output을 card로 바꿀 수 있다.

```text
all_at_once attribution  -> All-at-once Card
step_by_step attribution -> Step-by-step Card
binary_search attribution -> Binary-search Card
gold attribution -> Oracle Card
corrupted gold attribution -> Partial / Wrong Card
```

### 2.4 논문의 core plot을 만들기 쉽다

```text
Attribution accuracy on Who&When
        ↓
Card utility on downstream rerun benchmark
```

이 흐름은 “accuracy가 utility를 예측하는가?”라는 thesis와 잘 맞는다.

---

## 3. Who&When-first 접근의 한계

Who&When은 매우 좋은 출발점이지만, core PoC로 바로 쓰기에는 한계가 있다.

### 3.1 Who&When은 기본적으로 offline attribution benchmark다

Who&When의 기본 task는 failed log를 보고 responsible agent와 decisive step을 맞히는 것이다.

```text
Input: failed trajectory
Output: responsible agent + decisive error step
Metric: agent accuracy, step accuracy
```

우리의 downstream utility task는 다르다.

```text
Input: previous failure-derived Failure Card + new execution
Output: task success / failure recurrence / rescue rate
Metric: rescue rate, recurrence reduction, negative transfer
```

### 3.2 Who&When failure log가 재실행 가능하지 않을 수 있다

Failure Card utility를 보려면 다음이 가능해야 한다.

```text
같은 task를 다시 실행한다.
No-card baseline이 실패하는지 확인한다.
Card를 넣고 rerun한다.
성공으로 바뀌는지 측정한다.
```

만약 Who&When의 각 failed task가 현재 환경에서 그대로 replay되지 않으면, Who&When만으로는 “card가 실패를 성공으로 바꿨다”는 주장을 할 수 없다.

### 3.3 predicted attribution부터 쓰면 원인 분리가 어렵다

Who&When의 predicted attribution은 noisy할 수 있다. 따라서 처음부터 predicted attribution card가 효과가 없으면 아래 원인들을 구분하기 어렵다.

```text
1. attribution method가 틀렸다.
2. card 변환이 나쁘다.
3. card injection 위치가 약하다.
4. target failure가 card로 고칠 수 있는 종류가 아니다.
5. evaluation environment가 너무 noisy하다.
```

따라서 먼저 gold / oracle attribution card로 upper bound를 확인해야 한다.

---

## 4. 권장 실험 구조

## Phase 0. Who&When reproduction and data audit

### Goal

Who&When repo를 실행해 기존 benchmark와 연결되는 최소 산출물을 확보한다.

### Inputs

```text
Who&When failed trajectories
Gold responsible agent
Gold decisive error step
Natural language failure explanation
```

### Run

```text
Run all_at_once
Run step_by_step
Run binary_search
Evaluate agent accuracy and step accuracy
Export predictions per failure case
```

### Outputs

```text
outputs/who_when_predictions.jsonl
outputs/who_when_eval_summary.json
outputs/failure_case_index.csv
```

### Failure case index fields

```text
case_id
source_dataset_type: algorithm_generated | hand_crafted
task_query
agents
num_steps
gold_responsible_agent
gold_decisive_step
gold_explanation
pred_all_at_once_agent
pred_all_at_once_step
pred_step_by_step_agent
pred_step_by_step_step
pred_binary_search_agent
pred_binary_search_step
trace_available
candidate_failure_mode
actionability_score
replayability_status
notes
```

---

## Phase 1. Failure Card conversion from Who&When

### Goal

Who&When failure annotations and method outputs를 공통 Failure Card schema로 변환한다.

### Card schema

```json
{
  "card_id": "string",
  "source_case_id": "string",
  "attribution_source": "gold | all_at_once | step_by_step | binary_search | partial | wrong | mismatched",
  "failure_mode": "string",
  "source_agent": "string",
  "source_step": "string",
  "affected_agent": "string",
  "failure_trigger": "string",
  "propagation": "string",
  "do": "string",
  "do_not": "string",
  "applicable_when": "string"
}
```

### Card types to generate

```text
1. Gold / Oracle Failure Card
2. Predicted all_at_once Failure Card
3. Predicted step_by_step Failure Card
4. Predicted binary_search Failure Card
5. Partial Failure Card
6. Wrong / Mismatched Failure Card
```

### Important control

The card renderer must be fixed. Do not make oracle cards more polished than predicted or wrong cards.

```text
Same schema
Same section order
Similar length
Same injection wrapper
No full trace access during card rendering unless the condition explicitly allows it
```

---

## Phase 2. Actionability and replayability audit

### Goal

Who&When failure cases 중 downstream utility 실험에 쓸 수 있는 case를 선별한다.

### Two independent labels

#### A. Actionability

A failure is actionable if the attribution can be converted into a concrete prevention instruction.

```text
High actionability:
- incomplete handoff
- missing constraint
- unverified tool output
- failure to check original requirement
- role responsibility confusion
- premature termination

Low actionability:
- task impossible due to missing external resource
- ambiguous user query with no clear correct answer
- API/tool unavailable
- failure caused mainly by stochastic hallucination with no stable prevention point
```

#### B. Replayability

A failure is replayable if we can rerun the task under controlled conditions.

```text
Replayability = yes
- task input is available
- agent roles can be reconstructed
- tools/data can be accessed or mocked
- success checker can be defined

Replayability = no
- external website state changed
- private data unavailable
- original tool environment missing
- success criterion is subjective
```

### Output

```text
who_when_actionable_replayable_cases.csv
```

Recommended target for PoC:

```text
At least 10-20 high-actionability cases
At least 1-2 dominant failure modes
At least 1 runnable evaluation environment
```

---

## Phase 3A. If Who&When cases are replayable: direct Who&When rescue PoC

Use this route only when the original task can be rerun.

### Experiment unit

```text
case_id + seed + condition
```

### Conditions

```text
1. No guidance rerun
2. Strong generic guideline
3. Raw gold attribution explanation
4. Gold / Oracle Failure Card
5. Predicted method card
6. Partial Failure Card
7. Wrong / Mismatched Failure Card
```

### Required baseline check

Before card evaluation, verify that the case still fails under no-guidance baseline.

```text
No-card rerun fails -> eligible rescue case
No-card rerun succeeds -> move to negative-transfer / neutral set
Cannot rerun -> not eligible for direct rescue
```

### Main metric

```text
Rescue Rate = P(card run succeeds | no-card baseline rerun failed)
```

### Secondary metrics

```text
Same-mode recurrence rate
Negative transfer rate
Card utility vs no guidance
Attribution accuracy vs card utility
```

---

## Phase 3B. If Who&When cases are not replayable: Who&When-sourced card transfer PoC

This is the safer default route.

### Idea

Use Who&When failed logs to create cards, then evaluate the cards in our own runnable MAS mini-benchmark with matched failure modes.

```text
Who&When failed trace
        ↓
Gold / predicted / partial / wrong Failure Card
        ↓
Our runnable Planner-Executor-Reviewer benchmark
        ↓
Measure rescue rate on harvested baseline failures
```

### Recommended mini-benchmark

```text
Environment:
Planner -> Executor -> Reviewer data-analysis MAS

Target failure mode:
Incomplete handoff / missing constraint

Task type:
Small CSV/table reasoning or coding tasks with objective answer checker

Why:
- easy to create baseline failures
- easy to check success
- easy to detect same-mode recurrence
- strongly aligned with agent-step attribution cards
```

### Failure harvesting

```text
1. Generate 30-60 candidate tasks.
2. Run no-guidance MAS for 2-3 seeds.
3. Collect baseline failures.
4. Label failure mode.
5. Keep only failures matching target mode.
6. Verify patchability: oracle handoff/checklist would plausibly fix the run.
```

### Evaluation

```text
Held-out baseline failure cases: 10-20
Conditions: 6
Seeds: 2-3
Total: around 120-360 runs
```

Recommended conditions:

```text
1. No guidance
2. Strong generic guideline
3. Raw gold attribution explanation
4. Oracle Failure Card from Who&When-style gold attribution
5. Predicted Failure Card from Who&When method
6. Wrong / Mismatched Failure Card
```

---

## 5. What this PoC can and cannot claim

### Can claim after Phase 3B

```text
Attribution-derived Failure Cards created from existing MAS failure logs can transfer to a runnable held-out MAS setting and reduce recurrence of matched failure modes.
```

This is a strong PoC claim.

### Cannot claim after Phase 3B alone

```text
The original Who&When failed tasks themselves were repaired by our cards.
```

That claim requires Phase 3A, i.e. actual replay and rerun of Who&When tasks.

### Best final claim if both 3A and 3B work

```text
Failure Attribution is useful not only as an offline diagnostic label, but also as a source of reusable execution guidance: accurate attributions generate Failure Cards that rescue failed MAS executions and transfer to held-out tasks with the same failure mode.
```

---

## 6. Minimal first-week implementation plan

### Day 1: Run Who&When

```text
Clone repo
Install requirements
Download dataset
Run 1 method on small subset
Run evaluation
Inspect data structure
```

Deliverable:

```text
who_when_smoke_eval.md
```

### Day 2: Build parser and case index

```text
Parse traces
Extract agents / steps / gold labels / explanations
Join predictions with gold labels
Create case index
```

Deliverable:

```text
failure_case_index.csv
```

### Day 3: Generate Failure Cards

```text
Implement structured attribution tuple
Implement fixed card renderer
Generate gold / predicted / wrong cards for 10-20 cases
```

Deliverable:

```text
failure_cards.jsonl
```

### Day 4: Audit actionability and replayability

```text
Label failure modes
Choose 1 target failure mode
Decide Phase 3A or 3B route
```

Deliverable:

```text
actionability_replayability_audit.csv
```

### Day 5-7: Run smallest downstream rescue PoC

If replayable:

```text
Run direct rescue on 5-10 Who&When cases
```

If not replayable:

```text
Build mini Planner-Executor-Reviewer benchmark
Harvest 10 baseline failures
Run 5-6 card conditions
```

Deliverable:

```text
rescue_eval_results.csv
poc_summary.md
```

---

## 7. Go / no-go criteria

### Strong go

```text
Oracle Failure Card rescue rate > No guidance rerun by at least 15 percentage points
Oracle Failure Card >= Strong generic guideline
Same-mode recurrence lower under Oracle Failure Card
Predicted card utility roughly tracks attribution correctness
Wrong / mismatched card shows weak rescue or negative transfer
```

### Soft go

```text
Oracle works, but predicted methods are noisy.
```

Interpretation:

```text
The downstream evaluation framing is valid, but current attribution methods are not accurate/actionable enough.
```

### No-go for current design

```text
Oracle card does not rescue baseline failures.
```

Likely causes:

```text
Failure mode not card-preventable
Card injection position too weak
Baseline failure not stable/reproducible
Task success checker too noisy
Card too generic or too long
```

Do not proceed to large-scale real-method comparison until oracle-card rescue works.

---

## 8. Recommended final framing

The strongest framing is:

```text
We first reproduce Who&When to anchor our work in established MAS failure attribution.
We then convert Who&When-style attributions into standardized Failure Cards.
Finally, we evaluate whether those cards rescue reproducible baseline failures in a downstream execution setting.
```

This makes the project clearly different from simply building another attribution benchmark.

```text
Existing benchmark:
Can we identify who failed and when?

Our extension:
If we identify who failed and when, does that knowledge help the MAS succeed next time?
```
