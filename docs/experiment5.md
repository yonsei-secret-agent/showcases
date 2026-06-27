# Experiment 5: tau2-bench Runnable Rescue Pilot

## 상태

```text
status: planned
type: runnable benchmark rescue pilot
scope: existing tau2-bench tasks, same-task retry, objective task reward
primary benchmark: sierra-research/tau2-bench
```

Experiment 5는 Who&When PoC의 다음 단계다.

Who&When은 failure attribution을 downstream guidance로 바꿨을 때 local behavior가 바뀌는지 확인하기 좋은 PoC였다.
하지만 Who&When은 failed trace 중심의 offline benchmark이기 때문에 다음 한계가 남았다.

```text
1. final task success를 직접 재실행으로 측정하지 못한다.
2. judge proxy가 gold attribution과 coupling될 수 있다.
3. same-trace decisive-step repair가 reusable self-improvement인지 알기 어렵다.
```

tau2-bench pilot은 이 문제를 줄이기 위한 runnable benchmark 실험이다.

핵심 목표:

```text
failure attribution에서 만든 memory/card가
기존 runnable benchmark task의 retry success를 실제로 올리는가?
```

이 실험은 tau2-bench 전체를 돌리는 실험이 아니다.

첫 목표는 작은 subset에서 다음 두 가지 transition을 동시에 보는 것이다.

```text
1. 기존에 실패하던 task가 memory/card로 성공하는가?
2. 기존에 성공하던 task가 memory/card 때문에 실패하지는 않는가?
```

즉, rescue만 보지 않고 regression도 같이 본다.

## 왜 tau2-bench인가

tau2-bench는 customer-service style tool-agent-user interaction benchmark다.
각 domain은 policy, tools, tasks를 갖고 있으며, agent는 user simulator와 대화하면서 tool을 사용해 task를 해결한다.

현재 repo README 기준 사용 가능한 domain:

```text
core text-mode:
mock
airline
retail
telecom

optional knowledge retrieval:
banking_knowledge
```

첫 pilot은 `retail` 또는 `airline` 중 하나로 시작한다.
기본 추천은 `retail`이다.

이유:

```text
1. tool use + policy following + DB mutation이 섞여 있다.
2. missing verification, wrong update, premature finalization 같은 failure card가 자연스럽다.
3. final reward가 DB state / communicated info 중심이라 LLM judge circularity가 줄어든다.
```

공식 문서상 tau2 scoring은 task의 `reward_basis`에 따라 final reward를 계산한다.
clone한 현재 repo 기준으로 retail task 0-4는 `DB + NL_ASSERTION`을 사용했다.
따라서 domain과 task version별 reward basis를 실제 `tasks.json`에서 확인해야 한다.

`actions`는 하나의 reference trajectory이지, agent가 반드시 그대로 따라야 하는 유일한 정답 경로가 아니다.
이 점이 중요하다.

```text
우리의 primary metric은 "judge가 보기 좋은 action"이 아니라
tau2 evaluator가 인정하는 final outcome success다.
```

주의:

```text
NL_ASSERTION이 reward_basis에 포함된 task는 일부 LLM-judged component를 포함한다.
그래도 Who&When의 card-aligned repair judge와는 다르다.
tau2 evaluator는 card 내용을 보지 않고 task outcome 기준으로 판정한다.
```

참고:

```text
repo:
  https://github.com/sierra-research/tau2-bench

getting started:
  https://github.com/sierra-research/tau2-bench/blob/main/docs/getting-started.md

evaluation:
  https://github.com/sierra-research/tau2-bench/blob/main/docs/evaluation.md
```

## North Star와 연결

전체 연구 질문:

```text
Can precise failure attribution become a better self-improvement signal
than coarse reflection or generic in-context memory?
```

Experiment 5의 축소 질문:

```text
When an agent fails a runnable tau2 task,
can attribution-derived memory improve the next retry
more than coarse reflection or generic policy reminders?
```

Who&When에서 본 질문:

```text
attribution-derived card가 local next action을 바꾸는가?
```

tau2에서 볼 질문:

```text
attribution-derived card가 task-level retry success를 바꾸는가?
```

이 전환이 중요하다.

```text
local repair proxy -> objective runnable success
```

## Claim Boundary

Experiment 5는 아직 완전한 self-improving agent 논문이 아니다.
첫 pilot은 small-scale runnable rescue signal을 보는 단계다.

성공해도 가능한 claim:

```text
On a runnable tau2-bench subset,
oracle attribution-derived Failure Cards can improve same-task retry success
over no-memory and generic/coarse memory baselines.
```

아직 주장하면 안 되는 것:

```text
1. predicted attribution이 충분하다.
2. agent가 스스로 안정적으로 failure를 귀인했다.
3. memory retrieval 문제가 해결됐다.
4. held-out task transfer가 입증됐다.
5. full self-improving loop가 완성됐다.
```

첫 pilot은 다음을 보여주면 충분하다.

```text
기존 benchmark task에서 실패가 발생한다.
그 실패를 attribution card로 바꿀 수 있다.
같은 task retry에서 objective success가 오르는 신호가 있다.
기존 성공 task에 memory/card를 넣었을 때 harmful regression이 크지 않다.
```

## Experimental Unit

기본 단위:

```text
domain
task_id
baseline_run_id
baseline_attempt
failure_trace
failure_annotation
condition
retry_attempt
retry_result
transition_type
```

처음에는 same-task retry만 본다.

```text
same task, fresh environment, same user goal
```

같은 task를 다시 돌리되, 이전 실패에서 생성한 memory/card를 agent prompt에 넣는다.

중요:

```text
retry는 fresh environment에서 시작한다.
baseline trajectory의 intermediate state를 이어받지 않는다.
```

그래야 "prefix repair"가 아니라 "task rescue"가 된다.

## Subset Strategy

tau2-bench 전체를 평가하지 않는다.
첫 pilot은 `retail` domain의 작은 task subset으로 제한한다.

권장 초기 subset:

```text
domain: retail
candidate tasks: 12-20
baseline attempts per task: 3 preferred
retry attempts per condition: 2 minimum, 3 if budget allows
```

baseline 3회 실행으로 task를 세 그룹으로 나눈다.

```text
stable_success:
  baseline attempts가 모두 성공한 task

stable_failure:
  baseline attempts가 모두 실패한 task

mixed:
  baseline attempts 중 성공과 실패가 모두 있는 task
```

각 그룹의 의미:

```text
stable_failure:
  rescue signal을 보기 좋다.

mixed:
  stochastic recovery와 card effect가 섞일 수 있으므로 별도 표시한다.

stable_success:
  memory/card injection이 기존 성공을 망치는지 보는 safety set이다.
```

첫 pilot에서 모든 그룹을 균등하게 많이 뽑을 필요는 없다.
다만 최소한 아래는 확보하는 것이 좋다.

```text
rescue set:
  5-10 failed baseline traces

safety set:
  5-10 baseline-success tasks
```

해석상 주의:

```text
tau2는 LLM user simulator를 사용하므로 같은 task도 run마다 흔들릴 수 있다.
따라서 단일 baseline failure를 곧 "이 task는 실패 task"라고 보지 않는다.
stable_failure / stable_success 분류는 반복 실행 기반으로만 한다.
```

이렇게 하면 작은 비용으로 다음을 동시에 본다.

```text
failure -> success:
  rescue

success -> failure:
  regression / harmful negative transfer
```

## Phase 5A: tau2-bench Smoke Setup

목표:

```text
tau2-bench를 local third_party에 설치하고,
공식 CLI로 1-5개 task를 실행해 results.json 구조를 확인한다.
```

예상 설치:

```bash
git clone https://github.com/sierra-research/tau2-bench third_party/tau2-bench
cd third_party/tau2-bench
uv sync
cp .env.example .env
uv run tau2 check-data
```

첫 실행 예시:

```bash
uv run tau2 run \
  --domain retail \
  --agent-llm gpt-4.1-mini \
  --user-llm gpt-4.1-mini \
  --agent-llm-args '{"temperature": 0}' \
  --user-llm-args '{"temperature": 0}' \
  --num-trials 1 \
  --num-tasks 3 \
  --max-concurrency 1 \
  --seed 300 \
  --save-to retail_smoke_001
```

실제 command는 repo clone 후 CLI 옵션을 확인해 확정한다.

```bash
uv run tau2 --help
uv run tau2 run --help
```

성공 기준:

```text
1. results.json이 생성된다.
2. task별 final reward / DB reward / communicate reward를 읽을 수 있다.
3. conversation trace와 tool calls를 추출할 수 있다.
```

## Phase 5B: Baseline Failure Harvest

목표:

```text
no-memory baseline에서 실제 실패 task와 안정적 성공 task를 함께 수집한다.
```

초기 규모:

```text
domain: retail
candidate tasks: 12-20
baseline attempts per task: 3 preferred
model: gpt-4.1-mini or gpt-4o-mini
```

수집할 필드:

```text
task_id
task instruction / user goal
domain policy
available tools
conversation trace
tool calls
final reward
db reward
communicate reward
nl assertion reward
action diagnostics if available
failure summary
```

failure 후보:

```text
final_reward < 1.0
```

success 후보:

```text
final_reward == 1.0
```

task grouping:

```text
stable_failure:
  all baseline attempts have final_reward < 1.0

stable_success:
  all baseline attempts have final_reward == 1.0

mixed:
  at least one success and at least one failure
```

첫 pilot에서는 실패가 너무 적으면 더 약한 agent model을 사용한다.

추천 순서:

```text
1. gpt-4.1-mini 또는 gpt-4o-mini로 시작
2. 실패가 부족하면 더 작은/저렴한 model로 baseline harvest
3. retry agent는 baseline과 같은 model을 유지
```

주의:

```text
강한 model을 쓰면 failure가 너무 적어 rescue signal을 볼 수 없다.
약한 model을 쓰면 card를 읽고 활용할 능력도 부족할 수 있다.
```

따라서 baseline failure rate가 대략 다음 범위에 들어오는 model이 좋다.

```text
target baseline failure rate:
  30% - 70%
```

User simulator control:

```text
set user temperature to 0 when supported
set agent temperature to 0 for first smoke
record tau2 --seed for every run
record agent/user model and llm args in result metadata
```

Even with temperature and seed controls, do not assume perfect determinism.
Provider-side sampling, model updates, retries, and user simulator behavior can still vary.
This is why cell-level replication remains necessary.

## Phase 5C: Failure Attribution Overlay

tau2-bench는 Who&When처럼 gold `who/when/why` attribution label을 기본 제공하지 않는다.
따라서 첫 pilot에서는 기존 benchmark 위에 작은 attribution overlay를 얹는다.

이것은 새 benchmark를 만드는 것이 아니다.

또한 첫 pilot의 `oracle_failure_card`는 upper bound다.

```text
oracle means:
  사람이 실패 trajectory와 official outcome을 보고 attribution을 작성한다.

not:
  agent가 스스로 attribution을 맞혔다.
```

따라서 Experiment 5는 다음 질문을 먼저 본다.

```text
완벽한 attribution이 있다고 가정하면,
그것을 memory/card로 바꿨을 때 retry success가 개선되는가?
```

```text
benchmark:
  tau2-bench official task and evaluator

overlay:
  failed trajectory에 대한 small oracle attribution annotation
```

첫 pilot annotation 단위:

```text
5-10 failed trajectories from stable_failure or mixed tasks
```

가능하면 failure type을 2-3개 이상 포함한다.
단, 첫 smoke에서 강제하지는 않는다.

```text
minimum:
  failure_type 분포를 보고서에 기록

preferred:
  one failure type이 전체 rescue set의 70%를 넘지 않게 샘플링
```

annotation schema:

```text
case_id
domain
task_id
failure_type
responsible_component
decisive_turn_or_tool_call
failure_reason
missing_check_type
preventive_memory
evidence_span
confidence
```

`responsible_component`는 tau2 기본 agent가 single-agent일 경우 다음처럼 단순화한다.

```text
agent_policy_reasoning
tool_selection
tool_argument_construction
state_update_decision
user_communication
premature_finalization
```

나중에 multi-agent wrapper를 만들면 더 명확한 `who`를 둘 수 있다.

```text
planner
tool_executor
policy_checker
final_responder
```

하지만 첫 pilot에서는 wrapper를 먼저 만들지 않는다.
기존 tau2 agent를 그대로 사용하고, trajectory attribution overlay만 둔다.

Claim boundary:

```text
기본 tau2 agent는 single-agent에 가깝다.
따라서 Experiment 5는 MAS의 "who" utility를 강하게 검증하지 않는다.
이 pilot은 주로 when/why 또는 component-level failure attribution utility를 본다.
```

MAS의 `who`가 연구의 핵심 축으로 남는다면, 후속 실험에서 multi-agent wrapper를 추가해야 한다.

성공 baseline에는 oracle failure annotation이 없다.
따라서 success safety set에서는 다음 조건만 사용한다.

```text
no_memory_retry
generic_policy_checklist
irrelevant_or_mismatched_failure_card
```

목적:

```text
성공하던 task에 memory/card를 넣었을 때
성능이 떨어지는지 확인한다.
```

주의:

```text
coarse_reflection_memory는 success safety set에 넣지 않는다.
이 조건은 "이전 시도가 실패했다"는 신호를 주기 때문에,
baseline-success task에는 의도적으로 거짓 failure memory가 된다.
```

## Phase 5D: Memory/Card Conditions

retry 조건:

```text
1. no_memory_retry
2. coarse_reflection_memory
3. generic_policy_checklist
4. raw_failure_explanation
5. oracle_failure_card
6. wrong_or_mismatched_card
```

### 1. no_memory_retry

이전 실패 정보를 주지 않는다.

목적:

```text
retry 자체의 stochastic recovery를 측정한다.
```

### 2. coarse_reflection_memory

실패했다는 사실만 알려준다.

예시:

```text
A previous attempt at this task failed. Before acting, reflect on likely policy,
tool-use, and communication mistakes, then avoid repeating them.
```

목적:

```text
Reflexion-style coarse failure memory baseline.
```

### 3. generic_policy_checklist

case-specific attribution 없이 일반적인 tau2 customer-service checklist를 제공한다.
핵심 비교에서는 `oracle_failure_card`, `wrong_or_mismatched_card`와 같은 card schema를 사용한다.

예시:

```text
Failure pattern:
  General customer-service task failures often come from unchecked policy,
  unsupported tool assumptions, or incomplete user communication.

Applicable situation:
  Before any tool call that reads or changes records, and before the final response.

Risky action pattern:
  Acting from memory, skipping policy checks, or finalizing without confirming required details.

Do:
  Check the user request against the policy, use tools before record-changing claims,
  and confirm that required information is communicated.

Do not:
  Do not mutate records or finalize from an unsupported assumption.

Check before tool or final response:
  Have I verified policy eligibility, tool evidence, and required communication?
```

목적:

```text
generic ICL / policy reminder baseline.
```

### 4. raw_failure_explanation

oracle annotation의 `failure_reason`을 구조화 없이 전달한다.

목적:

```text
그냥 실패 원인을 알려주면 충분한가?
```

### 5. oracle_failure_card

oracle attribution을 non-leaky runtime memory로 변환한다.

agent-visible fields:

```text
failure pattern
applicable situation
risky action pattern
do
do_not
check_before_tool_or_final_response
```

Format control:

```text
oracle_failure_card
generic_policy_checklist
wrong_or_mismatched_card
```

위 세 조건은 같은 schema와 비슷한 길이를 사용한다.
핵심 비교는 이 format-matched card들 사이에서 한다.

```text
primary specificity contrast:
  oracle_failure_card vs generic_policy_checklist
  oracle_failure_card vs wrong_or_mismatched_card
```

`coarse_reflection_memory`와 `raw_failure_explanation`은 별도 baseline이며, format이 다르므로 secondary contrast로 해석한다.

금지:

```text
exact correct answer
target DB state
exact tool arguments that solve the task
"last time you failed at turn N" 같은 turn-specific hint
```

목적:

```text
정밀 attribution이 structured executable memory가 될 수 있는지 확인.
```

Leakage audit:

```text
1. exact correct answer, target DB state, exact solving tool arguments가 card에 들어가면 사용 금지
2. source trace의 literal entity/value가 card에 과도하게 남으면 regenerate 또는 drop
3. blind reader가 card만 보고 exact solution/tool args를 복원할 수 있으면 사용 금지
4. card가 generic_policy_checklist와 구별되지 않으면 oracle card로 사용하지 않는다
```

### 6. wrong_or_mismatched_card

다른 failure type의 card를 같은 형식과 길이로 제공한다.

목적:

```text
right attribution vs wrong attribution control.
```

주의:

```text
너무 넓게 좋은 verification card를 mismatch로 쓰지 않는다.
```

Orthogonality audit:

```text
1. target failure_type과 다른 source failure_type에서 온다.
2. target task의 actual failure_reason을 우연히 직접 건드리지 않는다.
3. generic_policy_checklist와 사실상 같은 조언이면 mismatch로 쓰지 않는다.
4. target task에 약간 무관하거나 misdirecting한 수준이어야 한다.
```

## Phase 5E: Retry Execution

각 case에 대해 fresh retry를 실행한다.

failed baseline case:
  rescue 조건을 실행한다.

successful baseline case:
  safety / regression 조건을 실행한다.

초기 smoke 규모:

```text
rescue set: 5-10 failed baseline traces
safety set: 5-10 stable-success tasks
rescue conditions: 6
safety conditions: 3
retry attempts per condition: 2 minimum, 3 if budget allows
baseline runs: 36-60
retry runs: 90-270
```

Small-n interpretation:

```text
5-10 cases는 existence signal과 debugging에는 충분하지만,
effect absence를 결론내기에는 부족하다.
따라서 first smoke는 strong positive signal 또는 inconclusive를 낸다.
track-level no-go는 내리지 않는다.
```

primary metric:

```text
official final reward
```

derived metrics:

```text
task_success_rate
retry_rescue_rate
regression_rate
paired_rescue_vs_no_memory
negative_transfer_rate
db_reward
communicate_reward
token_count
cost
```

정의:

```text
retry_rescue =
  baseline failed and condition retry succeeds

retry_regression =
  baseline succeeded and condition retry fails

paired_negative_transfer =
  no_memory_retry succeeds and memory condition fails
```

Primary transition matrix:

| baseline outcome | retry outcome | label | interpretation |
| --- | --- | --- | --- |
| fail | success | rescue | desired improvement |
| fail | fail | persistent failure | no rescue |
| success | success | stable success | no harm |
| success | fail | regression | harmful negative transfer |

Report는 반드시 이 matrix를 condition별로 낸다.

```text
condition | fail->success | fail->fail | success->success | success->fail
```

주의:

```text
no_memory_retry에서도 fail->success 또는 success->fail이 발생할 수 있다.
따라서 card effect는 no_memory_retry transition과 비교해 읽어야 한다.
```

Who&When과 달리 LLM judge는 primary metric이 아니다.

LLM/human annotation은 보조 분석에만 사용한다.

```text
secondary:
  Did the retry avoid the attributed failure mode?
  Did it introduce a new error?
  Did it use the card content?
```

## Phase 5F: First Smoke Decision Rules

Strong continue:

```text
oracle_failure_card improves official success over:
  no_memory_retry
  coarse_reflection_memory
  generic_policy_checklist
  wrong_or_mismatched_card

and negative_transfer is not elevated.
```

구체적으로는:

```text
rescue:
  oracle_failure_card의 fail->success rate가
  no_memory_retry와 generic_policy_checklist보다 높다.

safety:
  memory/card conditions의 success->fail rate가
  no_memory_retry보다 크게 높지 않다.
```

Soft continue:

```text
oracle_failure_card improves over no_memory_retry,
but is similar to generic_policy_checklist.
```

Interpretation:

```text
failure memory helps,
but attribution-specific content is not yet separated from generic policy reminders.
```

Pivot warning:

```text
generic_policy_checklist >= oracle_failure_card
or wrong_or_mismatched_card >= oracle_failure_card
```

Interpretation:

```text
the useful signal may be broad policy caution or retrieval/routing,
not precise attribution content.
```

Do not scale without redesign:

```text
oracle_failure_card does not improve over no_memory_retry,
or increases negative transfer.
```

This is not a final no-go for the research direction.
It means do not scale the current tau2 card-retry design until the failure mode is inspected.

Instead inspect:

```text
1. card renderer too generic
2. baseline model too weak to use memory
3. annotation not actionable
4. task failure not card-recoverable
5. prompt injection location ineffective
6. user simulator variance too high for the current replication count
```

## Why This Is Better Than More Who&When Same-Trace Runs

Who&When showed that attribution-derived guidance can influence a next action.
But the central concern remained:

```text
Are we measuring real improvement,
or just a judge proxy aligned with a gold diagnosis?
```

tau2-bench reduces that concern because:

```text
1. task execution is rerunnable
2. final reward is outcome-based
3. retry starts from a fresh environment
4. success is not defined by the Failure Card text
```

This does not make tau2 perfect.
It simply moves the PoC closer to the research target.

```text
failure attribution -> memory -> retry success
```

## Implementation Plan

Implementation should be incremental.

### Task 1: Clone and Smoke tau2

Files:

```text
third_party/tau2-bench/
```

Steps:

```text
1. clone repo
2. uv sync
3. set API key in third_party/tau2-bench/.env
4. run tau2 check-data
5. run 1-3 retail tasks with --save-to retail_smoke_001
6. inspect results.json
```

### Task 2: Add Result Extractor

Create a small local adapter, not a forked benchmark.

Suggested files:

```text
tau2_card_poc/src/tau2_card_poc/results_io.py
tau2_card_poc/tests/test_results_io.py
```

Responsibilities:

```text
load results.json
extract task_id / reward / conversation / tool calls
identify failed simulations
write failure candidate index
```

### Task 3: Add Annotation Schema

Suggested files:

```text
tau2_card_poc/src/tau2_card_poc/annotations.py
tau2_card_poc/data/annotations/manual_failures.jsonl
```

First version:

```text
manual JSONL annotation for 5-10 failed traces
```

Do not automate attribution yet.

### Task 4: Add Card Renderer

Suggested files:

```text
tau2_card_poc/src/tau2_card_poc/cards.py
tau2_card_poc/tests/test_cards.py
```

Renderer must enforce:

```text
no exact answer
no target DB state
no exact solving tool arguments
condition formats length-matched where possible
```

### Task 5: Add Retry Runner

This is the key integration task.

Goal:

```text
inject memory/card into tau2 agent prompt and rerun the same task.
```

Implementation depends on tau2 agent API after repo inspection.

Minimum acceptable path:

```text
use tau2's custom agent interface or prompt/config hook
to prepend condition-specific memory to the agent instruction.
```

### Task 6: Add Metrics Reporter

Suggested files:

```text
tau2_card_poc/src/tau2_card_poc/metrics.py
tau2_card_poc/reports/tau2_rescue_smoke_summary.md
```

Report:

```text
condition-level success
case-level paired matrix
rescue rate
negative transfer
cost/token count
qualitative notes for oracle-only / generic-only / all-fail cases
```

## Needed From User

Before running Experiment 5, the user needs to provide:

```text
1. API key usable by tau2 via LiteLLM
   recommended first: OpenAI key

2. model choice
   recommended first:
     agent: gpt-4.1-mini or gpt-4o-mini
     user simulator: gpt-4.1-mini or gpt-4o-mini

3. budget limit
   smoke may require roughly 90-225 tau2 runs depending on failure harvest.

4. whether to start with retail or airline
   recommended: retail

5. permission to create a small tau2_card_poc package
   separate from who_when_card_poc
```

OpenRouter can be considered after first smoke if LiteLLM model routing is verified.
For the first run, direct OpenAI is less ambiguous.

## Expected First Deliverable

The first deliverable is not a paper-level result.

It is a team-convincing PoC report:

```text
docs/tau2_rescue_pilot_report.md
```

It should answer:

```text
1. Could we run tau2 locally?
2. Did baseline produce enough failures?
3. Did baseline also produce stable-success tasks for regression analysis?
4. Could we annotate failures into actionable cards?
5. Did oracle cards improve official retry success on failed cases?
6. Did memory/card injection cause success->failure regressions?
7. Did oracle cards beat coarse/generic/wrong controls?
8. Is this direction worth scaling?
```

## Relationship to Future Work

If Experiment 5 works:

```text
Experiment 6:
  predicted card content utility on tau2
  generated failure card instead of manual/oracle card

Experiment 7:
  runnable closed-loop self-improving agent
  fail -> attribute -> store -> retrieve -> retry / held-out success

Experiment 8:
  predicted intervention point / multi-agent wrapper
  explicit who/when intervention in a MAS-style tau2 agent
```

If Experiment 5 fails:

```text
Do not keep polishing card prompts.
Instead inspect whether attribution is more useful for:
  intervention routing
  policy-check selection
  failure prediction before DB mutation
  training/credit assignment
```

The purpose of tau2 is to give us a cleaner decision point than Who&When.
