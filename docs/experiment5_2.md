# Experiment 5.2: tau2 Retail Baseline Harvest

## 상태

```text
status: ready_to_run
type: baseline harvest
benchmark: tau2-bench retail
goal scale: 30 candidate tasks x 3 seeds
```

## 실험 목표

Experiment 5.2는 20-case rescue 실험을 바로 시작하지 않고, 먼저 tau2 retail에서 **실제로 반복 실패하는 task pool**을 만드는 실험이다.

해소하려는 질문:

```text
1. gpt-4.1-mini agent/user setting에서 어떤 retail task가 안정적으로 실패하는가?
2. 실패 task가 한 가지 failure type에 몰려 있는가, 아니면 여러 type을 포함하는가?
3. 20-case rescue gate를 구성할 만큼 충분한 실패 후보가 있는가?
```

## 왜 필요한가

이전 task 2 pilot은 신호가 있었지만, task 1개와 seed 3개뿐이었다.

남은 핵심 불확실성:

```text
oracle card가 rescue를 유발했나?
아니면 task 2 / seed 303이 우연히 winnable했던 것인가?
```

이 불확실성을 줄이려면 조건 수를 늘리는 것이 아니라 다음을 늘려야 한다.

```text
task 수
failure type 다양성
cell-level seed replication
```

## 후보 구성

후보 task는 기존 tau2 repo에 포함된 retail final result를 prior로 사용해 고른다.

기존 4-trial 결과 기준:

```text
stable fail: 17 tasks
mixed: 53 tasks
stable success: 44 tasks
```

Experiment 5.2 후보:

```text
30 candidate tasks
= prior stable-fail 17
+ low-success mixed 13
```

Manifest:

```text
tau2_card_poc/experiments/exp5_2_baseline_harvest_30.json
```

## 실행 구성

```text
domain: retail
agent model: gpt-4.1-mini
user model: gpt-4.1-mini
condition: no_memory
candidate tasks: 30
seeds: 401, 402, 403
max steps: 200
```

총 실행 수:

```text
30 tasks x 3 seeds = 90 runs
```

## 실행 방법

권장 실행은 tau2 공식 CLI다. no-memory baseline은 memory wrapper가 필요 없으므로 공식 runner가 더 빠르고 단순하다.

실행 전 credential preflight:

```bash
python3 - <<'PY'
from pathlib import Path
p = Path("third_party/tau2-bench/.env")
for name in ["OPENAI_API_KEY", "OPENROUTER_API_KEY"]:
    value = ""
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith(name + "="):
                value = line.split("=", 1)[1].strip().strip('"')
    if not value or "your_key" in value.lower():
        print(f"{name}: missing_or_placeholder")
    else:
        print(f"{name}: set")
PY
```

`OPENAI_API_KEY`가 placeholder면 아래 OpenAI direct command는 실패한다.
OpenRouter를 쓸 경우에는 tau2/litellm model slug를 별도로 smoke-test한 뒤 같은 harvest 구조를 사용한다.

```bash
cd third_party/tau2-bench
uv run tau2 run \
  --domain retail \
  --agent-llm gpt-4.1-mini \
  --user-llm gpt-4.1-mini \
  --agent-llm-args '{"temperature": 0}' \
  --user-llm-args '{"temperature": 0}' \
  --task-ids 2 3 4 20 27 28 34 36 41 56 71 79 103 104 109 111 112 0 16 43 95 98 99 110 1 7 14 15 19 33 \
  --num-trials 3 \
  --max-concurrency 3 \
  --seed 401 \
  --timeout 300 \
  --auto-resume \
  --save-to exp5_2_baseline_harvest_30
```

## 산출물

```text
third_party/tau2-bench/data/simulations/exp5_2_baseline_harvest_30/results.json
reports/exp5_2_baseline_harvest_30/task_stability.csv
reports/exp5_2_baseline_harvest_30/condition_summary.csv
```

요약 생성:

```bash
cd third_party/tau2-bench
PYTHONPATH=/home/depa/showcases/tau2_card_poc/src:/home/depa/showcases/third_party/tau2-bench/src \
  uv run python -m tau2_card_poc.cli summarize \
  data/simulations/exp5_2_baseline_harvest_30 \
  --default-condition no_memory \
  --out-dir /home/depa/showcases/reports/exp5_2_baseline_harvest_30
```

## 선택 규칙

20-case rescue set은 다음 순서로 고른다.

```text
1. baseline 3회 중 2회 이상 실패한 task 우선
2. 가능하면 stable_failure를 우선 포함
3. failure type이 하나에 몰리지 않도록 분산
4. oracle single-missing-check card를 쓸 수 있을 만큼 actionability가 있는 task만 포함
```

failure type 예시:

```text
availability/count communication failure
DB/write/update failure
policy/tool eligibility failure
premature finalization
wrong or incomplete user communication
```

## 결과 해석

GREEN:

```text
20개 이상 actionable failed task를 확보하고,
2개 이상의 failure type을 포함한다.
```

AMBER:

```text
20개 후보는 있지만 대부분 한 failure type에 몰려 있다.
```

RED:

```text
20개 actionable failed task를 확보하지 못한다.
이 경우 후보 task 수를 늘리거나 domain/model을 조정한다.
```

## Claim Boundary

이 실험은 card 효과를 측정하지 않는다.

가능한 claim:

```text
tau2 retail에서 20-case rescue pilot을 구성할 baseline failure pool을 확보했다.
```

불가능한 claim:

```text
failure card가 task success를 올렸다.
attribution-specific utility가 입증됐다.
self-improving agent가 검증됐다.
```
