# Exp6 Binding Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and smoke-test Experiment 6, a tau2 dynamic finalization gate that compares no-gate, coarse binding, mode-only binding, oracle binding, and wrong binding interventions.

**Architecture:** Keep the existing static `RuntimeMemoryAgent` path intact. Add a separate binding module with rule-based presence gates, a binding retry runner, and manifest support for binding experiments. Reporting should preserve existing Exp5 CSVs while adding gate metrics when gate metadata is present.

**Revision after Exp6A smoke:** The initial `BindingGateAgent` design fired on every assistant text turn because tau2 half-duplex does not expose agent-side finality. The production run path now uses `BindingGateUserSimulator`, which intercepts only when the user simulator would emit a stop/transfer marker after an assistant response.

**Tech Stack:** Python stdlib, tau2-bench local clone, `unittest`, existing `tau2_card_poc` manifest/runner/reporting structure.

---

### Task 1: Add Binding Gate Primitives

**Files:**
- Create: `tau2_card_poc/src/tau2_card_poc/binding_gates.py`
- Test: `tau2_card_poc/tests/test_binding_gates.py`

- [ ] **Step 1: Write tests for rule-based gate matching**

Test cases:

```python
from tau2_card_poc.binding_gates import (
    BindingGate,
    BindingGateDecision,
    PresenceRule,
    evaluate_binding_gate,
)


def test_presence_rule_requires_all_patterns():
    gate = BindingGate(
        name="money_summary",
        feedback="Missing money summary.",
        rules=[PresenceRule(kind="money", description="money amount")],
    )

    decision = evaluate_binding_gate(gate, "Refund total is $12.34.")

    assert decision.passed is True
    assert decision.failed_rules == []


def test_presence_rule_reports_missing_pattern():
    gate = BindingGate(
        name="tracking_check",
        feedback="Missing tracking number.",
        rules=[PresenceRule(kind="tracking", description="tracking number")],
    )

    decision = evaluate_binding_gate(gate, "The order has shipped.")

    assert decision.passed is False
    assert decision.failed_rules == ["tracking number"]
```

- [ ] **Step 2: Implement minimal gate dataclasses and evaluator**

Implement:

```python
@dataclass(frozen=True)
class PresenceRule:
    kind: str
    description: str


@dataclass(frozen=True)
class BindingGate:
    name: str
    feedback: str
    rules: list[PresenceRule]


@dataclass(frozen=True)
class BindingGateDecision:
    passed: bool
    failed_rules: list[str]
```

Supported rule kinds:

```text
money
count
tracking
status
comparison
any_text
```

- [ ] **Step 3: Run targeted tests**

Run:

```bash
PYTHONPATH=tau2_card_poc/src:third_party/tau2-bench/src python3 -m unittest tau2_card_poc.tests.test_binding_gates
```

Expected:

```text
OK
```

- [ ] **Step 4: Commit**

```bash
git add tau2_card_poc/src/tau2_card_poc/binding_gates.py tau2_card_poc/tests/test_binding_gates.py
git commit -m "Add tau2 binding gate primitives"
```

### Task 2: Add BindingGateUserSimulator and Single-Run Path

**Files:**
- Create: `tau2_card_poc/src/tau2_card_poc/binding_runner.py`
- Modify: `tau2_card_poc/src/tau2_card_poc/specs.py`
- Test: `tau2_card_poc/tests/test_binding_runner.py`

- [ ] **Step 1: Add `BindingRetrySpec`**

Add to `specs.py`:

```python
@dataclass(frozen=True)
class BindingRetrySpec:
    domain: str
    task_id: str
    condition: str
    binding_gate: dict
    seed: int
    trial: int
    agent_model: str
    user_model: str
    task_split_name: str | None = None
    max_steps: int = 100
    max_errors: int = 10
    log_level: str = "INFO"
```

- [ ] **Step 2: Write tests for user-stop interception**

Use a fake user generation sequence:

```python
class FakeBindingUser(BindingGateUserSimulator):
    def __init__(self, responses, **kwargs):
        super().__init__(llm="fake", instructions="scenario", binding_gate=kwargs["binding_gate"])
        self.responses = list(responses)

    def _generate_next_message(self, message, state):
        return self.responses.pop(0)
```

Assertions:

```text
ordinary user responses pass through without gate evaluation
user stop responses trigger evaluation of the previous assistant message
failed attempted final response replaces user stop with synthetic feedback
passing attempted final response lets user stop pass through
gate_events records triggered, passed, failed_rules, retry_used
```

- [ ] **Step 3: Implement `BindingGateUserSimulator`**

Implementation rules:

```text
subclass UserSimulator
override generate_next_message, not system_prompt
call _generate_next_message normally
if generated user message is not a stop/transfer marker, return unchanged
if generated user message would stop, evaluate the previous AssistantMessage
replace failed stop with synthetic UserMessage feedback when retry remains
let passing stop messages through unchanged
record gate events on self.gate_events
```

- [ ] **Step 4: Implement `run_single_binding_retry`**

Mirror `run_single_memory_retry`, but:

```text
register binding_gate_user_simulator_<condition>_<digest>
use the normal llm_agent for agent generation
store binding_gate_condition and binding_gate_events in simulation.info
write standard results.json payload
```

- [ ] **Step 5: Run targeted tests**

Run:

```bash
PYTHONPATH=tau2_card_poc/src:third_party/tau2-bench/src python3 -m unittest tau2_card_poc.tests.test_binding_runner
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit**

```bash
git add tau2_card_poc/src/tau2_card_poc/binding_runner.py tau2_card_poc/src/tau2_card_poc/specs.py tau2_card_poc/tests/test_binding_runner.py
git commit -m "Add tau2 binding gate runner"
```

### Task 3: Add Binding Manifest Support

**Files:**
- Create: `tau2_card_poc/src/tau2_card_poc/binding_manifest.py`
- Create: `tau2_card_poc/src/tau2_card_poc/binding_batch_runner.py`
- Modify: `tau2_card_poc/src/tau2_card_poc/cli.py`
- Test: `tau2_card_poc/tests/test_binding_manifest.py`
- Test: `tau2_card_poc/tests/test_binding_batch_runner.py`

- [ ] **Step 1: Write manifest loading tests**

Manifest shape:

```json
{
  "experiment_id": "exp6a_binding_smoke",
  "domain": "retail",
  "agent_model": "gpt-4.1-mini",
  "user_model": "gpt-4.1-mini",
  "task_ids": [43],
  "seeds": [701],
  "conditions": [
    {"name": "no_gate", "binding_gate": null},
    {
      "name": "coarse_binding_gate",
      "binding_gate": {
        "name": "coarse",
        "feedback": "Re-check all requested outcomes before finalizing.",
        "rules": [{"kind": "any_text", "description": "non-empty final response"}]
      }
    }
  ]
}
```

- [ ] **Step 2: Implement binding manifest dataclasses**

Implement:

```text
BindingExperimentCondition
BindingExperimentManifest
load_binding_experiment_manifest
iter_binding_retry_specs
```

Validation:

```text
condition names unique
task_ids non-empty
seeds non-empty
conditions non-empty
per_task_binding_gate covers all manifest task IDs
```

- [ ] **Step 3: Implement binding batch runner**

Mirror `batch_runner.run_manifest`, but use `run_single_binding_retry`.

- [ ] **Step 4: Add CLI command**

Add:

```text
tau2-card-poc run-binding-manifest <manifest> --output-root <dir> [--no-resume]
```

- [ ] **Step 5: Run tests**

Run:

```bash
PYTHONPATH=tau2_card_poc/src:third_party/tau2-bench/src python3 -m unittest tau2_card_poc.tests.test_binding_manifest tau2_card_poc.tests.test_binding_batch_runner tau2_card_poc.tests.test_cli
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit**

```bash
git add tau2_card_poc/src/tau2_card_poc/binding_manifest.py tau2_card_poc/src/tau2_card_poc/binding_batch_runner.py tau2_card_poc/src/tau2_card_poc/cli.py tau2_card_poc/tests/test_binding_manifest.py tau2_card_poc/tests/test_binding_batch_runner.py tau2_card_poc/tests/test_cli.py
git commit -m "Add manifest support for binding gate experiments"
```

### Task 4: Extend Reporting With Gate Metrics

**Files:**
- Modify: `tau2_card_poc/src/tau2_card_poc/results_io.py`
- Modify: `tau2_card_poc/src/tau2_card_poc/reporting.py`
- Test: `tau2_card_poc/tests/test_results_io.py`
- Test: `tau2_card_poc/tests/test_reporting.py`

- [ ] **Step 1: Add parser tests for gate metadata**

Input simulation info:

```json
{
  "binding_gate_condition": "coarse_binding_gate",
  "binding_gate_events": [
    {"triggered": true, "passed": false, "retry_used": true, "failed_rules": ["money amount"]},
    {"triggered": true, "passed": true, "retry_used": false, "failed_rules": []}
  ]
}
```

Expected record fields:

```text
gate_trigger_count = 2
gate_failure_count = 1
gate_retry_count = 1
gate_final_passed = true
```

- [ ] **Step 2: Extend `ExperimentRecord`**

Add optional integer/bool fields with defaults so Exp5 reports still work.

- [ ] **Step 3: Add gate columns to `per_run_outcomes.csv`**

Columns:

```text
gate_trigger_count
gate_failure_count
gate_retry_count
gate_final_passed
```

- [ ] **Step 4: Add condition-level gate summary**

Either extend `condition_summary.csv` or create `gate_condition_summary.csv`.
Prefer adding a new CSV to avoid breaking prior interpretation.

- [ ] **Step 5: Run tests**

Run:

```bash
PYTHONPATH=tau2_card_poc/src:third_party/tau2-bench/src python3 -m unittest tau2_card_poc.tests.test_results_io tau2_card_poc.tests.test_reporting
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit**

```bash
git add tau2_card_poc/src/tau2_card_poc/results_io.py tau2_card_poc/src/tau2_card_poc/reporting.py tau2_card_poc/tests/test_results_io.py tau2_card_poc/tests/test_reporting.py
git commit -m "Report binding gate metrics"
```

### Task 5: Add Exp6A Smoke Manifest And Run It

**Files:**
- Create: `tau2_card_poc/experiments/exp6a_binding_smoke.json`
- Create: `docs/experiment6_results.md`
- Create after run: `reports/exp6a_binding_smoke/*.csv`

- [ ] **Step 1: Create smoke manifest**

Use:

```text
tasks: [43]
seeds: [701, 702]
conditions:
  no_gate
  mismatched_money_gate
max_steps: 200
max_errors: 10
```

Use an intentionally task-irrelevant money gate for smoke so the rejection path
is exercised:

```json
{
  "name": "smoke_money_presence_gate",
  "feedback": "Re-check the user's requested outcomes before finalizing.",
  "rules": [{"kind": "money", "description": "money amount"}]
}
```

This smoke only proves plumbing; it is not research evidence.

- [ ] **Step 2: Run full unit test suite**

Run:

```bash
PYTHONPATH=tau2_card_poc/src:third_party/tau2-bench/src uv run --project third_party/tau2-bench python -m unittest discover -s tau2_card_poc/tests -p 'test_*.py'
```

Expected:

```text
OK
```

- [ ] **Step 3: Run Exp6A smoke**

Run:

```bash
PYTHONPATH=tau2_card_poc/src:third_party/tau2-bench/src uv run --project third_party/tau2-bench tau2-card-poc run-binding-manifest tau2_card_poc/experiments/exp6a_binding_smoke.json --output-root third_party/tau2-bench/data/simulations
```

Expected:

```text
runs: 4 total
```

- [ ] **Step 4: Summarize Exp6A**

Run:

```bash
PYTHONPATH=tau2_card_poc/src:third_party/tau2-bench/src uv run --project third_party/tau2-bench tau2-card-poc summarize third_party/tau2-bench/data/simulations/exp6a_binding_smoke --out-dir reports/exp6a_binding_smoke
```

Expected:

```text
wrote summaries for 4 records
```

- [ ] **Step 5: Write smoke result note**

Document:

```text
whether no_gate reproduced normal execution
whether gate metadata appeared
whether final response interception corrupted tau2 replay
whether official reward was still computed
```

- [ ] **Step 6: Commit**

```bash
git add tau2_card_poc/experiments/exp6a_binding_smoke.json reports/exp6a_binding_smoke docs/experiment6_results.md
git commit -m "Run tau2 Exp6A binding smoke"
```

### Task 6: Decide Phase 6B Harvest

**Files:**
- Modify: `docs/experiment6_results.md`
- Create only if smoke passes: `tau2_card_poc/experiments/exp6b_binding_harvest.json`

- [ ] **Step 1: Inspect Exp6A**

If Exp6A fails any harness success criterion, stop and fix the harness.

- [ ] **Step 2: If Exp6A passes, draft 6B harvest manifest**

Candidate tasks should exclude the known bad Exp5.5C pool unless they are used
only as diagnostics.

- [ ] **Step 3: Do not run 6B until the smoke result note is reviewed**

This prevents spending on a broken gate harness.
