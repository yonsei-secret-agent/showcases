# Failure Attribution Downstream Utility PoC — Agent Implementation Brief

> 목적: 이 문서는 PoC 프로젝트를 실제로 구성할 구현 에이전트에게 주는 실행 명세다.  
> 핵심은 “Failure Card가 좋아 보이는가?”가 아니라, **Failure Attribution 결과가 다음 MAS 실행을 실제로 개선하는가**를 검증하는 것이다.

---

## 0. One-line Mission

**정확한 MAS Failure Attribution에서 만든 Failure Card를 held-out MAS task에 주입했을 때, task success가 올라가고 동일 failure recurrence가 줄어드는지 검증한다.**

PoC의 1차 성공 신호는 아래 하나다.

```text
Attribution quality ↑  →  Failure Card utility ↑
```

최소한 아래 패턴이 나와야 한다.

```text
Oracle Failure Card > Strong Generic Guideline ≥ No Guidance > Wrong / Mismatched Card
```

단, 완전한 단조성까지 첫 PoC에서 요구하지는 않는다. 가장 중요한 1차 go signal은 다음 두 개다.

```text
Oracle Failure Card success rate > No Guidance success rate
Oracle Failure Card recurrence rate < No Guidance recurrence rate
```

---

## 1. 이 실험은 정확히 어떤 실험인가?

이 실험은 **MAS failure attribution의 downstream evaluation**이다.

기존 failure attribution benchmark는 대체로 failed trace를 보고 다음을 맞힌다.

```text
Who failed?      → responsible agent
When failed?     → decisive error step
Why failed?      → failure explanation / root cause
```

우리 PoC는 여기서 한 단계 더 간다.

```text
failed trace
→ attribution output
→ standardized Failure Card
→ held-out MAS task prompt에 주입
→ 새로운 실행에서 success / recurrence 측정
```

즉, attribution을 정답 라벨과 비교하는 데서 끝내지 않고, 그 attribution이 **다음 실행을 개선하는 실행 지식으로 transfer되는지**를 본다.

### Core causal chain

```text
Attribution source
  ├─ oracle attribution
  ├─ partial attribution
  ├─ wrong attribution
  └─ real-method predicted attribution
        ↓
Standardized Failure Card
        ↓
MAS execution guardrail injection
        ↓
Held-out task execution
        ↓
Task Success / Failure Recurrence / Negative Transfer
```

---

## 2. 이 접근이 연구적으로 의미 있는가?

의미 있다. 단, framing을 잘 잡아야 한다.

이 연구는 “새로운 prompting trick”이 아니다. Failure Card는 method가 아니라 **evaluation interface**다. 서로 다른 failure attribution 결과를 MAS가 실제로 사용할 수 있는 동일한 형식으로 변환하기 위한 공통 포맷이다.

### 기존 접근과의 차이

| 기존 Failure Attribution 평가 | 우리 Downstream Evaluation |
|---|---|
| failed trace에서 agent / step / cause를 맞힘 | attribution 결과가 다음 실행을 개선하는지 봄 |
| static label accuracy 중심 | execution success / recurrence 중심 |
| “설명이 맞는가?” | “그 설명이 유용한가?” |
| benchmark score가 끝 | benchmark score와 real utility의 관계를 측정 |

### 핵심 novelty

```text
Attribution accuracy가 높으면 실제 card utility도 높은가?
```

가능한 결과는 둘 다 연구적으로 의미 있다.

```text
Case A. accuracy ↑ → utility ↑
  → 기존 attribution accuracy가 실용적 가치가 있음을 보여줌.

Case B. accuracy와 utility의 상관이 약함
  → 기존 attribution benchmark가 실제 debugging utility를 충분히 대변하지 못할 수 있음을 보여줌.
```

따라서 실패 가능성도 결과가 될 수 있다. 단, 첫 PoC에서는 최소한 **oracle attribution card의 upper-bound utility**가 보여야 한다.

---

## 3. Who&When benchmark를 어떻게 쓸 것인가?

Who&When은 매우 좋은 anchor다. 하지만 첫 PoC의 core로만 쓰면 위험하다.

### Who&When을 쓰면 좋은 점

```text
1. 기존 MAS Failure Attribution 본류와 직접 연결됨.
2. responsible agent / decisive step이라는 명확한 attribution target이 있음.
3. all_at_once / step_by_step / binary_search 같은 baseline method를 재사용할 수 있음.
4. 우리 연구가 “Failure Card prompt 연구”가 아니라 “Failure Attribution downstream evaluation”임을 보여줌.
```

### 하지만 첫 utility PoC의 core로 쓰면 위험한 이유

Who&When은 기본적으로 **failed trajectory를 보고 who/when을 맞히는 attribution benchmark**다. PoC에서 진짜로 필요한 것은 다음이다.

```text
카드를 넣고 같은 시스템 또는 유사 시스템을 다시 실행할 수 있는가?
```

만약 benchmark log가 static trace 중심이고 재실행 환경이 완전하지 않다면, downstream utility를 직접 측정할 수 없다. 이 경우 Who&When 위에서 바로 “우리 card가 success를 올렸다”를 증명하기 어렵다.

또한 처음부터 predicted attribution으로 만든 card만 평가하면, 결과가 나쁠 때 원인을 분리할 수 없다.

```text
나쁜 결과의 가능한 원인:
1. attribution method가 틀림
2. card 변환이 안 좋음
3. card injection이 약함
4. eval task가 card로 개선 가능한 실패를 만들지 않음
5. MAS 자체의 variance가 너무 큼
```

따라서 PoC는 다음 순서로 가야 한다.

```text
Phase 0. Who&When repo / data / baseline method를 확인하고 attribution output format을 이해한다.
Phase 1. 우리 runnable mini-benchmark에서 oracle / partial / wrong card utility gradient를 먼저 증명한다.
Phase 2. 같은 runnable mini-benchmark에 Who&When-style attribution method를 붙인다.
Phase 3. 가능하면 Who&When logs를 card-conversion external validity / static utility proxy로 연결한다.
```

### 결론

```text
Who&When은 “연구 anchor”와 “real-method baseline”으로 쓴다.
하지만 첫 가능성 증명은 controlled runnable PoC에서 한다.
```

---

## 4. PoC 전체 구조

### Phase 0 — Attribution benchmark anchor

목적: 기존 benchmark와 연결되는 최소 산출물을 만든다.

해야 할 일:

```text
1. Who&When repository 실행 가능 여부 확인.
2. sample failed logs 5~10개 로드.
3. all_at_once / step_by_step / binary_search 중 최소 1개 method 실행.
4. output이 responsible_agent, decisive_step, explanation으로 어떻게 나오는지 확인.
5. 이 output을 우리 Failure Card schema로 변환하는 converter 초안 작성.
```

주의:

```text
Phase 0은 downstream utility 실험이 아니다.
Phase 0의 목표는 연구 연결성과 pipeline feasibility 확인이다.
```

---

### Phase 1 — Core controlled utility PoC

목적: 정확한 attribution에서 나온 card가 실제 next execution을 개선할 수 있음을 가장 깨끗하게 증명한다.

핵심 실험:

```text
Failure mode:
  Incomplete handoff / missing constraint

MAS:
  Planner → Executor → Reviewer

Task type:
  small data-analysis / coding tasks with objective checker

Card conditions:
  1. No Guidance
  2. Strong Generic Guideline
  3. Raw Gold Attribution Explanation
  4. Oracle Failure Card
  5. Partial Failure Card
  6. Wrong / Mismatched Failure Card

Scale:
  12 held-out tasks × 6 conditions × 2 seeds = 144 runs
```

이 phase에서 봐야 할 질문:

```text
Q1. Oracle Failure Card가 No Guidance보다 task success를 올리는가?
Q2. Oracle Failure Card가 Strong Generic Guideline보다 나은가?
Q3. Oracle Failure Card가 동일 failure recurrence를 줄이는가?
Q4. Raw Gold Attribution보다 structured Failure Card가 더 나은가?
Q5. Partial / Wrong card로 갈수록 utility가 떨어지는가?
Q6. Wrong / Mismatched card가 negative transfer를 만드는가?
```

---

### Phase 2 — Real-method attribution card PoC

목적: controlled gradient에서 signal이 확인되면 실제 attribution method를 붙인다.

조건 추가:

```text
7. Direct LLM Judge Card
8. Who&When-style Step-by-Step Card
9. Optional: Constraint / Evidence Card
```

이 phase의 질문:

```text
Q1. real-method predicted card의 utility는 oracle과 wrong 사이 어디에 놓이는가?
Q2. real-method의 attribution accuracy가 card utility를 예측하는가?
Q3. 누가/언제만 맞힌 card와 왜/어떻게까지 포함한 card 중 무엇이 유용한가?
```

---

### Phase 3 — External validity

목적: 더 다양한 failure mode / task / trace에서 결과가 유지되는지 본다.

가능한 확장:

```text
1. failure mode 2개 이상으로 확장
   - incomplete handoff
   - unverified tool output
   - premature termination

2. tasks 30개 이상, seeds 3개 이상으로 확장

3. Who&When logs에서 card conversion quality 평가
   - success utility가 아니라 static actionability / relevance proxy
   - runnable reconstruction이 가능할 때만 true downstream utility 평가
```

---

## 5. PoC에서 구현할 MAS 환경

### Recommended MAS

```text
Planner → Executor → Reviewer
```

### Agent responsibilities

#### Planner

```text
Input:
  user task, data schema, available tools

Output:
  structured handoff to Executor

Expected behavior:
  - identify goal
  - list all constraints
  - list filters
  - define computation formula
  - specify tie-break rules
  - specify output format
```

#### Executor

```text
Input:
  Planner handoff, data file or table

Output:
  code, intermediate result, final candidate answer

Expected behavior:
  - follow handoff
  - use Python/pandas or deterministic local computation
  - return result and evidence
```

#### Reviewer

```text
Input:
  original user task, Planner handoff, Executor result

Output:
  approve/reject, final answer

Expected behavior:
  - compare result against original constraints
  - catch missing constraints
  - reject if result violates original task
```

### Why this MAS?

```text
1. Handoff failure가 자연스럽게 발생함.
2. Planner의 missing constraint를 자동 감지하기 쉬움.
3. Executor 결과를 objective checker로 채점 가능함.
4. Reviewer failure까지 propagation을 관찰할 수 있음.
5. 비용이 낮고 반복 실행이 쉬움.
```

---

## 6. PoC failure mode

첫 PoC는 failure mode를 하나로 고정한다.

```text
failure_mode = incomplete_handoff / missing_constraint
```

### Gold failure chain

```text
Source agent:
  Planner

Source step:
  Planner handoff to Executor

Failure trigger:
  Planner omitted one or more required constraints from the handoff.

Propagation:
  Executor followed the underspecified handoff and produced an answer that ignored the missing constraint.

Symptom:
  Final answer fails exact checker or violates task constraints.
```

### Example

Original user task:

```text
Given orders.csv, return the product category with the highest total revenue.
Constraints:
- exclude cancelled orders
- revenue = quantity * unit_price
- only include orders after 2024-01-01
- if tied, choose alphabetically earliest category
- output only the category name
```

Injected faulty handoff:

```text
Compute the product category with the highest total revenue.
Use revenue = quantity * unit_price.
Output only the category name.
```

Missing constraints:

```text
- exclude cancelled orders
- only include orders after 2024-01-01
- tie-break alphabetically
```

---

## 7. Task dataset construction

### Minimum smoke dataset

```text
12 held-out eval tasks
3 source failure tasks
2 seeds
6 card conditions
Total eval runs = 144
```

### Recommended expanded dataset

```text
30 held-out eval tasks
6 source failure tasks
3 seeds
6~9 card conditions
Total eval runs = 540~810
```

### Task requirements

Each task must satisfy:

```text
1. Objective checker exists.
2. Correct final answer is deterministic.
3. Task has 4~7 explicit constraints.
4. At least one constraint is easy to omit in handoff.
5. Baseline No Guidance success is not too high or too low.
   Target baseline success range: 30%~70%.
6. A missing-constraint failure can be detected from Planner handoff.
```

### Task schema

Create JSONL file:

```json
{
  "task_id": "orders_001",
  "split": "eval",
  "task_family": "tabular_data_analysis",
  "user_prompt": "Given orders.csv, return the product category with the highest total revenue...",
  "data_path": "tasks/data/orders_001.csv",
  "gold_answer": "Electronics",
  "gold_constraints": [
    "exclude cancelled orders",
    "revenue = quantity * unit_price",
    "include only orders after 2024-01-01",
    "if tied, choose alphabetically earliest category",
    "output only the category name"
  ],
  "critical_constraint": "exclude cancelled orders",
  "checker_type": "exact_match",
  "failure_mode": "incomplete_handoff"
}
```

### Recommended task families

Use only one family for the first PoC.

```text
Preferred:
  tabular_data_analysis

Examples:
  - sales aggregation with filters
  - ranking with tie-break rules
  - date filtering
  - group-by with exclusions
  - weighted average with missing-value rule
```

Avoid in first PoC:

```text
- open-ended writing
- web browsing
- subjective evaluation
- long-horizon tool tasks
- tasks requiring external APIs
```

---

## 8. Source traces vs held-out eval tasks

Do not create a card from the same task where it is evaluated.

### Required split

```text
source_tasks:
  Used to create failed traces and cards.

eval_tasks:
  Used to measure whether cards transfer to new tasks.
```

### Example

```text
source task:
  orders_source_001: missing date filter in Planner handoff

card created:
  Planner must explicitly pass all filters, tie-break rules, and output constraints to Executor.

eval task:
  customers_eval_007: missing region exclusion would cause wrong answer
```

This tests transfer of failure knowledge, not memorization.

---

## 9. How to generate source failure traces

### Option A — True run then injected handoff

```text
1. Run MAS normally on a source task until Planner produces handoff.
2. Programmatically remove one critical constraint from Planner handoff.
3. Pass faulty handoff to Executor.
4. Let Executor and Reviewer continue.
5. Keep trace if final answer fails because of the omitted constraint.
```

### Option B — Direct controlled faulty handoff

Use this if Option A is unstable.

```text
1. Generate a gold Planner handoff from task metadata.
2. Remove one critical constraint using a deterministic function.
3. Feed faulty handoff to Executor.
4. Let Executor and Reviewer continue.
5. Save trace and gold attribution.
```

For first PoC, Option B is acceptable. The purpose is not to show natural failure frequency; it is to show whether known attribution-derived guidance can prevent recurrence.

### Source trace schema

```json
{
  "trace_id": "src_orders_001_fault_omit_cancelled",
  "task_id": "orders_source_001",
  "failure_mode": "incomplete_handoff",
  "messages": [
    {"step": 1, "agent": "Planner", "content": "...faulty handoff..."},
    {"step": 2, "agent": "Executor", "content": "...code and result..."},
    {"step": 3, "agent": "Reviewer", "content": "...approval..."}
  ],
  "gold_attribution": {
    "failure_mode": "incomplete_handoff",
    "source_agent": "Planner",
    "source_step": 1,
    "affected_agent": "Executor",
    "failure_trigger": "Planner omitted required constraints in the handoff.",
    "violated_constraint": "exclude cancelled orders",
    "propagation": "Executor followed the incomplete handoff and computed revenue without excluding cancelled orders.",
    "symptom": "Final answer selected the wrong product category."
  }
}
```

---

## 10. Attribution tuple schema

All card conditions must start from a structured attribution tuple.

```json
{
  "attribution_id": "attr_oracle_001",
  "trace_id": "src_orders_001_fault_omit_cancelled",
  "condition": "oracle",
  "accuracy_level": 1.0,
  "failure_mode": "incomplete_handoff",
  "source_agent": "Planner",
  "source_step": 1,
  "affected_agent": "Executor",
  "failure_trigger": "Planner omitted required constraints during handoff.",
  "violated_constraint": "exclude cancelled orders",
  "propagation": "Executor followed the underspecified instruction and ignored the missing constraint.",
  "symptom": "Final answer failed the task checker."
}
```

### Accuracy levels for controlled PoC

```text
Oracle attribution:
  accuracy_level = 1.0
  mode, source_agent, source_step, trigger, propagation all correct

Partial attribution:
  accuracy_level = 0.5
  mode correct, but source agent or repair target partially wrong

Wrong attribution:
  accuracy_level = 0.0
  plausible but wrong mode/source/trigger

Mismatched attribution:
  accuracy_level can be high for another trace, but relevance to current eval family is low
```

### Optional tuple-level score

If needed:

```text
AttributionAccuracy =
  0.20 * mode_match
+ 0.20 * source_agent_match
+ 0.15 * source_step_match
+ 0.20 * trigger_match
+ 0.10 * violated_constraint_match
+ 0.15 * propagation_match
```

---

## 11. Failure Card schema

All cards must use the same fields and renderer.

```json
{
  "card_id": "card_oracle_001",
  "source_attribution_id": "attr_oracle_001",
  "card_condition": "oracle_card",
  "failure_mode": "Incomplete handoff / missing constraint",
  "source_agent": "Planner",
  "affected_agent": "Executor",
  "failure_trigger": "Planner omitted required constraints during handoff.",
  "propagation": "Executor followed the underspecified handoff and produced an answer that ignored the missing constraint.",
  "do": "Before handoff, list every task constraint, filter, formula, edge case, tie-break rule, and output-format requirement.",
  "do_not": "Do not assume the Executor can infer missing requirements from the original user request.",
  "applicable_when": "The task requires Planner-to-Executor handoff for data analysis, coding, or tool execution."
}
```

### Rendered card format

```text
[Failure Card]

Failure mode:
Incomplete handoff / missing constraint

Source agent:
Planner

Affected agent:
Executor

Failure trigger:
Planner omitted required constraints during handoff.

Propagation:
Executor followed the underspecified handoff and produced an answer that ignored the missing constraint.

Do:
Before handoff, list every task constraint, filter, formula, edge case, tie-break rule, and output-format requirement.

Do not:
Do not assume the Executor can infer missing requirements from the original user request.

Applicable when:
The task requires Planner-to-Executor handoff for data analysis, coding, or tool execution.
```

### Card generation rules

```text
1. Never let card generator see the full trace for controlled oracle/partial/wrong cards.
2. Card generator only receives the attribution tuple.
3. Use the same renderer for every condition.
4. Keep approximate length similar across conditions.
5. Wrong card must be plausible, not intentionally absurd.
6. Do not include task-specific answer values in the card.
7. Do not leak held-out eval task content into card generation.
```

---

## 12. Card conditions

### C0. No Guidance

No additional guidance is added.

Purpose:

```text
baseline
```

---

### C1. Strong Generic Guideline

Use strong general MAS quality guidance.

```text
General MAS quality guideline:
- Identify all user requirements before execution.
- Preserve constraints across agent handoffs.
- Verify intermediate outputs before finalizing.
- Check filters, formulas, tie-break rules, edge cases, and output format.
- If an instruction is incomplete, ask for clarification or state assumptions before proceeding.
```

Purpose:

```text
Prevent strawman baseline.
Show that oracle card is not merely “more prompting”.
```

---

### C2. Raw Gold Attribution Explanation

Provide a short root-cause explanation, not a structured card.

Example:

```text
Previous failure analysis:
The Planner caused the failure by omitting required constraints during handoff. The Executor followed the incomplete handoff and produced an answer that ignored the missing constraint.
```

Purpose:

```text
Test whether structured Failure Card adds value over raw attribution text.
```

---

### C3. Oracle Failure Card

Structured card from correct attribution tuple.

Purpose:

```text
Upper bound of the approach.
If this does not improve execution, do not proceed to real-method comparison.
```

---

### C4. Partial Failure Card

Card from partially correct attribution.

Example:

```text
failure mode correct:
  incomplete handoff

source agent wrong or secondary:
  Executor failed to ask clarification

repair target:
  Executor should check whether instructions are complete before acting
```

Purpose:

```text
Middle point in attribution accuracy → card utility gradient.
```

---

### C5. Wrong / Mismatched Failure Card

Card from plausible but wrong attribution or a correct attribution from a different failure mode.

Example wrong card:

```text
Failure mode:
Output format violation

Source agent:
Reviewer

Do:
Before finalizing, ensure the final response format exactly matches the user request.
```

Example mismatched card:

```text
Failure mode:
Unverified tool output

Do:
Compare tool output against final answer before submission.
```

Purpose:

```text
Measure negative transfer and show that failure memory is not free.
```

---

## 13. Card injection prompt

Use exactly the same wrapper for all card conditions that include a card.

```text
You are given a Failure Card derived from a previous multi-agent failure.
Use it as an execution guardrail.

Before acting, check whether the card's "Applicable when" condition matches the current task.
If applicable, follow the "Do" instruction and avoid the "Do not" instruction.
Do not blindly force the card if it is irrelevant.
Do not mention the card in the final answer.

{FAILURE_CARD}
```

For Raw Gold Attribution condition, use:

```text
You are given a previous failure analysis.
Use it as execution guidance if it is relevant to the current task.
Do not mention it in the final answer.

{RAW_ATTRIBUTION_EXPLANATION}
```

For Strong Generic Guideline, use:

```text
Use the following general MAS quality guideline during execution.
Do not mention it in the final answer.

{GENERIC_GUIDELINE}
```

Important:

```text
Do not change the agent base prompt across conditions.
Do not change model, temperature, token budget, tool availability, or task order across conditions.
Only the guidance condition should vary.
```

---

## 14. Run design

### Paired design

Every condition must be run on the same task and same seed.

```text
task_id = orders_eval_001
seed = 0
conditions:
  C0 No Guidance
  C1 Generic
  C2 Raw Gold
  C3 Oracle Card
  C4 Partial Card
  C5 Wrong Card
```

This enables paired comparison:

```text
Utility(task, seed, condition) = Success(task, seed, condition) - Success(task, seed, no_guidance)
```

### Recommended model settings

```text
temperature: 0.0 or 0.2
max_tokens: fixed across conditions
model: configurable via config file
judge model: separate optional config
```

### Minimum run matrix

```text
12 eval tasks × 6 conditions × 2 seeds = 144 runs
```

### Smoke test before full run

```text
3 eval tasks × 6 conditions × 1 seed = 18 runs
```

Run the smoke test first. Check logs manually. Only then run the full 144.

---

## 15. Evaluation metrics

### 15.1 Task Success Rate

```text
Success = 1 if final answer passes checker else 0
```

Aggregate:

```text
SuccessRate(condition) = mean(Success over tasks and seeds)
```

---

### 15.2 Failure Recurrence Rate

For incomplete handoff:

```text
Recurrence = 1 if:
  Planner handoff omitted one or more required gold constraints
  AND final answer failed or Reviewer approved despite omission
```

Aggregate:

```text
RecurrenceRate(condition) = mean(Recurrence over tasks and seeds)
```

---

### 15.3 Card Utility

Primary utility:

```text
UtilitySuccess(condition) = SuccessRate(condition) - SuccessRate(no_guidance)
```

Recurrence utility:

```text
UtilityRecurrence(condition) = RecurrenceRate(no_guidance) - RecurrenceRate(condition)
```

Do not collapse these into one score for the first report. Show both.

---

### 15.4 Negative Transfer Rate

Paired definition:

```text
NegativeTransfer(condition) =
  mean over task/seed pairs where
  Success(no_guidance) = 1 and Success(condition) = 0
```

Also useful:

```text
Strict negative transfer:
  No Guidance succeeds, condition fails.

Soft negative transfer:
  condition final answer violates a constraint that No Guidance handled correctly.
```

---

### 15.5 Attribution–Utility Correlation

For controlled cards:

```text
x = attribution_accuracy_level
  Oracle = 1.0
  Partial = 0.5
  Wrong = 0.0

y = UtilitySuccess(condition)
```

Report:

```text
Spearman correlation between attribution_accuracy and utility
```

Do not overclaim with small n. For PoC, visual trend is more important than p-value.

---

### 15.6 Card adherence diagnostic

Optional but useful.

```text
Adherence = did the relevant agent perform the card's Do action?
```

For incomplete handoff:

```text
Planner listed all constraints before handoff = 1 / 0
```

This helps diagnose failures:

```text
Card had no effect because agent ignored it?
Card was followed but still did not improve success?
Card caused overfitting or irrelevant behavior?
```

---

## 16. Recurrence detector

### Deterministic detector for missing constraints

Input:

```text
- gold_constraints from task JSON
- Planner handoff text from trace
```

Output:

```json
{
  "missing_constraints": ["exclude cancelled orders"],
  "handoff_complete": false,
  "recurrence": true
}
```

Recommended implementation:

```text
1. Normalize constraints into canonical short labels.
2. Use keyword/rule checks for obvious constraints.
3. Use LLM judge only for ambiguous cases.
4. Save detector reasoning.
```

### LLM judge prompt for ambiguous cases

```text
You are evaluating whether a Planner handoff preserved the required constraints.

Required constraints:
{GOLD_CONSTRAINTS}

Planner handoff:
{PLANNER_HANDOFF}

For each required constraint, answer whether it is explicitly present, implicitly present, or missing.
Return JSON only:
{
  "constraint_results": [
    {"constraint": "...", "status": "explicit|implicit|missing", "evidence": "..."}
  ],
  "handoff_complete": true/false,
  "missing_constraints": ["..."],
  "recurrence": true/false
}
```

Audit:

```text
Human-check at least 20 random runs or 20% of runs, whichever is smaller.
```

---

## 17. Analysis report

Generate a markdown report plus CSV outputs.

### Required tables

#### Table 1 — Aggregate metrics

| condition | runs | success_rate | recurrence_rate | utility_success | utility_recurrence | negative_transfer |
|---|---:|---:|---:|---:|---:|---:|
| no_guidance | | | | 0.00 | 0.00 | 0.00 |
| generic | | | | | | |
| raw_gold | | | | | | |
| oracle_card | | | | | | |
| partial_card | | | | | | |
| wrong_card | | | | | | |

#### Table 2 — Paired differences vs No Guidance

| condition | wins | ties | losses | paired_success_delta |
|---|---:|---:|---:|---:|
| generic | | | | |
| raw_gold | | | | |
| oracle_card | | | | |
| partial_card | | | | |
| wrong_card | | | | |

### Required plots

```text
1. Success rate by condition
2. Recurrence rate by condition
3. Attribution accuracy vs card utility
4. Negative transfer rate by condition
```

### Interpretation template

```text
Primary result:
  Oracle Failure Card improved success by X percentage points over No Guidance.

Generic baseline:
  Oracle Failure Card improved success by Y points over Strong Generic Guideline.

Recurrence:
  Oracle Failure Card reduced incomplete-handoff recurrence by Z points.

Gradient:
  Oracle > Partial > Wrong trend was / was not observed.

Negative transfer:
  Wrong / mismatched card caused N negative-transfer cases.

Conclusion:
  Go / Soft Go / No-Go
```

---

## 18. Go / Soft-Go / No-Go criteria

### Strong Go

Proceed to Phase 2 real-method cards if:

```text
1. Oracle card improves success over No Guidance by ≥ 10 percentage points.
2. Oracle card improves or ties Strong Generic Guideline.
3. Oracle card reduces recurrence by ≥ 10 percentage points.
4. Partial card is between Oracle and Wrong, or at least not better than Oracle.
5. Wrong / Mismatched card has lower utility or some negative transfer.
```

### Soft Go

Continue but revise framing if:

```text
1. Oracle card improves over No Guidance.
2. Oracle does not clearly beat Strong Generic Guideline.
3. Accuracy gradient is weak.
```

Likely interpretation:

```text
Attribution-derived guidance is useful, but card actionability / relevance may matter more than attribution accuracy alone.
```

### No-Go

Do not proceed to real-method comparisons if:

```text
1. Oracle card does not improve over No Guidance.
2. Recurrence does not decrease.
3. Agents ignore cards or task success is saturated.
```

Fix before expanding:

```text
- Recalibrate task difficulty.
- Make failure mode more card-preventable.
- Improve injection location.
- Strengthen card specificity.
- Lower baseline ceiling.
```

---

## 19. Implementation repository structure

Use this structure.

```text
failure-card-poc/
  README.md
  configs/
    default.yaml
    models.yaml
    experiment_phase1.yaml
  data/
    tasks/
      source_tasks.jsonl
      eval_tasks.jsonl
      data_files/
        orders_source_001.csv
        orders_eval_001.csv
    traces/
      source/
      eval/
    cards/
      attribution_tuples.jsonl
      failure_cards.jsonl
  src/
    agents/
      planner.py
      executor.py
      reviewer.py
      prompts.py
    mas/
      runner.py
      trace.py
    tasks/
      generate_tasks.py
      checkers.py
      schemas.py
    faults/
      inject_missing_constraint.py
    attribution/
      tuple_builder.py
      controlled_attributions.py
      who_when_adapter.py
    cards/
      renderer.py
      converters.py
    eval/
      success.py
      recurrence.py
      metrics.py
      plots.py
  scripts/
    00_smoke_test.py
    01_generate_tasks.py
    02_generate_source_traces.py
    03_generate_cards.py
    04_run_phase1.py
    05_evaluate.py
    06_report.py
  outputs/
    runs/
    metrics/
    plots/
    reports/
  tests/
    test_checkers.py
    test_card_renderer.py
    test_recurrence_detector.py
```

---

## 20. Required CLI commands

Implement these commands or equivalent.

### Generate tasks

```bash
python scripts/01_generate_tasks.py \
  --n_source 3 \
  --n_eval 12 \
  --out_dir data/tasks
```

### Generate source traces

```bash
python scripts/02_generate_source_traces.py \
  --tasks data/tasks/source_tasks.jsonl \
  --out_dir data/traces/source \
  --failure_mode incomplete_handoff
```

### Generate cards

```bash
python scripts/03_generate_cards.py \
  --source_traces data/traces/source \
  --conditions oracle,partial,wrong \
  --out_cards data/cards/failure_cards.jsonl
```

### Run Phase 1

```bash
python scripts/04_run_phase1.py \
  --tasks data/tasks/eval_tasks.jsonl \
  --cards data/cards/failure_cards.jsonl \
  --conditions no_guidance,generic,raw_gold,oracle_card,partial_card,wrong_card \
  --seeds 0,1 \
  --out_dir outputs/runs/phase1
```

### Evaluate

```bash
python scripts/05_evaluate.py \
  --runs outputs/runs/phase1 \
  --tasks data/tasks/eval_tasks.jsonl \
  --out_dir outputs/metrics/phase1
```

### Report

```bash
python scripts/06_report.py \
  --metrics outputs/metrics/phase1/metrics.csv \
  --out outputs/reports/phase1_report.md
```

---

## 21. Run output schema

Every run must save a JSON file.

```json
{
  "run_id": "orders_eval_001_seed0_oracle_card",
  "task_id": "orders_eval_001",
  "seed": 0,
  "condition": "oracle_card",
  "model": "MODEL_NAME",
  "failure_card_id": "card_oracle_001",
  "messages": [
    {"step": 1, "agent": "Planner", "content": "..."},
    {"step": 2, "agent": "Executor", "content": "..."},
    {"step": 3, "agent": "Reviewer", "content": "..."}
  ],
  "final_answer": "Electronics",
  "gold_answer": "Electronics",
  "success": true,
  "recurrence_eval": {
    "recurrence": false,
    "missing_constraints": [],
    "handoff_complete": true
  },
  "token_usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "latency_sec": 0.0
}
```

---

## 22. How to connect Who&When-style attribution later

After Phase 1 succeeds, implement `who_when_adapter.py`.

### Input

```text
failed trace from our source task
```

### Output

```json
{
  "predicted_source_agent": "Planner",
  "predicted_source_step": 1,
  "predicted_explanation": "Planner failed to include all constraints in the handoff."
}
```

### Conversion to card

```text
Who&When-style output
→ attribution tuple
→ same Failure Card renderer
→ held-out eval runs
```

### Adapter rule

Do not give the converter more information than the attribution method produced.

Allowed:

```text
- predicted source agent
- predicted source step
- selected step text
- predicted natural-language explanation, if produced
```

Not allowed:

```text
- gold attribution
- held-out task answer
- full trace if the attribution method did not use it
- manually fixed explanation
```

This prevents leakage.

---

## 23. Common pitfalls

### Pitfall 1 — Oracle card too polished, wrong card too weak

Fix:

```text
Use same schema, same renderer, similar length.
```

### Pitfall 2 — Generic baseline too weak

Fix:

```text
Make generic guideline strong. It must include handoff preservation and verification.
```

### Pitfall 3 — Baseline success ceiling

Problem:

```text
No Guidance success > 85%
```

Fix:

```text
Increase task constraints or choose tasks where handoff matters.
```

### Pitfall 4 — Baseline success floor

Problem:

```text
No Guidance success < 15%
```

Fix:

```text
Simplify task or improve base MAS prompt.
```

### Pitfall 5 — Card ignored

Fix:

```text
Inject card into Planner system prompt or pre-handoff instruction, not only final user prompt.
```

### Pitfall 6 — Recurrence detector too noisy

Fix:

```text
Start with missing-constraint failure mode because recurrence can be checked against gold constraints.
```

### Pitfall 7 — Proving too many things at once

Fix:

```text
First prove oracle card utility.
Only then add real attribution methods.
```

---

## 24. Implementation acceptance checklist

Before declaring Phase 1 done, ensure:

```text
[ ] 12 eval tasks exist with objective checkers.
[ ] 3 source failure traces exist with gold attribution.
[ ] All 6 card conditions are implemented.
[ ] Card renderer is shared across oracle / partial / wrong.
[ ] Same task/seed is run across all conditions.
[ ] Every run saves full Planner / Executor / Reviewer messages.
[ ] Success checker is deterministic.
[ ] Recurrence detector is implemented for missing constraints.
[ ] Aggregate metrics CSV is generated.
[ ] Report contains success, recurrence, utility, negative transfer.
[ ] At least 10 random traces manually inspected.
```

---

## 25. Final expected PoC report conclusion format

Use exactly this structure in final report.

```text
Conclusion: Strong Go / Soft Go / No-Go

1. Does an oracle attribution-derived Failure Card improve held-out execution?
   Answer: Yes / No
   Evidence: success delta = ...

2. Does it reduce same-mode recurrence?
   Answer: Yes / No
   Evidence: recurrence delta = ...

3. Is structured card better than raw attribution text?
   Answer: Yes / No / Mixed
   Evidence: oracle_card vs raw_gold delta = ...

4. Is there an attribution accuracy → utility gradient?
   Answer: Yes / No / Mixed
   Evidence: oracle vs partial vs wrong utility = ...

5. Is there negative transfer from wrong or mismatched cards?
   Answer: Yes / No
   Evidence: negative transfer rate = ...

Next step:
   If Strong Go: add real-method Who&When-style cards.
   If Soft Go: adjust card/actionability framing and rerun.
   If No-Go: revise task/failure mode/injection before scaling.
```

---

## 26. Minimal first-week execution plan

### Day 1

```text
- Implement task schema and 3 toy data-analysis tasks.
- Implement Planner / Executor / Reviewer runner.
- Implement exact answer checker.
```

### Day 2

```text
- Implement missing-constraint fault injection.
- Generate 1 source failure trace.
- Implement gold attribution tuple and card renderer.
```

### Day 3

```text
- Implement six guidance conditions.
- Run 3-task smoke test.
- Manually inspect logs.
```

### Day 4

```text
- Generate 12 eval tasks.
- Run full Phase 1: 144 runs.
```

### Day 5

```text
- Evaluate success / recurrence / utility / negative transfer.
- Generate report.
- Decide Strong Go / Soft Go / No-Go.
```

---

## 27. Non-goals for first PoC

Do not implement these in Phase 1:

```text
- Full reproduction of every Failure Attribution paper.
- Large-scale natural failure collection.
- Human annotation pipeline for ambiguous causal failures.
- Multi-perspective attribution benchmark.
- Training or fine-tuning.
- Web-browsing agents.
- Subjective answer evaluation.
```

These can come after oracle-card utility is shown.

---

## 28. Final instruction to implementation agent

Your first job is not to build the most general benchmark. Your first job is to answer this narrow question:

```text
If we know the true cause of a previous MAS failure,
and we convert it into a standardized Failure Card,
does injecting that card into a similar but held-out MAS task
make the next execution measurably better?
```

If the answer is yes, the research direction is alive. Then add Who&When-style predicted attributions and test whether real attribution accuracy predicts downstream utility.

If the answer is no, do not scale. Diagnose task difficulty, card injection, failure mode, and recurrence detection first.
