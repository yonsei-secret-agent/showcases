# Who&When Card PoC

This project implements a Who&When-native smoke experiment for testing whether
attribution-derived runtime Failure Cards reduce recurrence of decisive errors in trace-prefix
counterfactual repair.

The current runner covers:

```text
Who&When case audit
Pre-Phase2 no-guidance recurrence pretest
Failure-prone case selection
Phase 2A gold-intervention generation
Blind LLM judgment
Condition-level and case-level metrics
```

## Setup

1. Fill API keys in `.env`.
2. Keep the first smoke run on fixed model slugs; do not use auto-routed models.
3. Run config checks before adding Who&When data.

```bash
cd who_when_card_poc
PYTHONPATH=src python3 -m ww_card_poc.cli check-config
PYTHONPATH=src python3 -m ww_card_poc.cli show-experiment
```

`check-config` requires the active API key. `show-experiment` only validates the experiment YAML.

## Reality Check

After cloning or copying Who&When into `third_party/Agents_Failure_Attribution`, run:

```bash
PYTHONPATH=src python3 -m ww_card_poc.cli reality-check --output reports/who_when_reality_check.md
PYTHONPATH=src python3 -m ww_card_poc.cli data-audit
```

The report is intentionally not a final verdict. It lists candidate data/code files and the manual
questions that must be answered from 2-3 real annotated traces:

```text
Can we locate gold who/when/why?
Are trajectories ordered and agent-attributed?
Can we cut at t*-1 with enough context?
Is the responsible agent role recoverable?
Is the decisive step local enough for next-action regeneration?
```

`data-audit` parses all local Who&When JSON files and writes:

```text
data/interim/who_when_case_index.csv
reports/who_when_data_audit.md
```

The case index is the first source for selecting Phase 2A candidates. Cases marked
`candidate_initial_step` are usable but need prompts built from the task and role context because
the decisive error is at step 0. Cases marked `warning` need manual inspection before inclusion.

## Default Backend

The first smoke run is configured for OpenRouter using:

```text
generation: openai/gpt-4o-mini-2024-07-18
card: openai/gpt-4o
judge: openai/gpt-4o
attribution: openai/gpt-4o
```

The generation model is intentionally cheaper and weaker for smoke tests so no-guidance
recurrence remains observable. This is not a claim that mini matches the original Who&When trace
generation model. Runtime card generation and future attribution-method reproduction use GPT-4o
because they define the oracle card quality and should not be bottlenecked by a weak offline model.

OpenAI direct can be enabled by setting:

```text
MODEL_BACKEND=openai
```

## Current Scope

Initial implementation target:

```text
Phase 0: Who&When data audit
Pre-Phase 2: no-guidance recurrence pretest
Phase 2A: gold-intervention trace-prefix repair smoke
```

Expensive Who&When method reproduction is intentionally off by default:

```text
phase0_method_reproduction: false
```

The conservative first smoke set should be selected from:

```text
dataset_type = algorithm_generated
mistake_step >= 2
phase2a_status = candidate
warnings excluded
```

Build API-free smoke inputs before any model calls:

```bash
PYTHONPATH=src python3 -m ww_card_poc.cli select-smoke-cases
PYTHONPATH=src python3 -m ww_card_poc.cli build-phase2a-inputs
```

This writes:

```text
data/interim/smoke_case_selection.csv
data/runs/phase2a_smoke_inputs.jsonl
```

## Smoke Run

Run the recurrence pretest first. This estimates whether no-guidance regenerations still repeat
the original decisive error.

```bash
PYTHONPATH=src python3 -m ww_card_poc.cli build-phase2a-inputs \
  --limit 15 \
  --conditions no_guidance \
  --output data/runs/pre_phase2_recurrence_inputs.jsonl

PYTHONPATH=src python3 -m ww_card_poc.cli run-phase2a \
  --input data/runs/pre_phase2_recurrence_inputs.jsonl \
  --output data/runs/pre_phase2_recurrence_generations.jsonl \
  --repeats 3 \
  --temperature-mode recurrence

PYTHONPATH=src python3 -m ww_card_poc.cli judge-phase2a \
  --generations data/runs/pre_phase2_recurrence_generations.jsonl \
  --output data/judgments/pre_phase2_recurrence_judgments.jsonl

PYTHONPATH=src python3 -m ww_card_poc.cli summarize-phase2a \
  --judgments data/judgments/pre_phase2_recurrence_judgments.jsonl \
  --report reports/pre_phase2_recurrence_summary.md \
  --condition-csv data/interim/pre_phase2_recurrence_condition_metrics.csv \
  --case-csv data/interim/pre_phase2_recurrence_case_metrics.csv \
  --json data/interim/pre_phase2_recurrence_condition_metrics.json
```

Then build the Phase 2A input set from failure-prone no-guidance cases and run the 5-condition
smoke.

```bash
PYTHONPATH=src python3 -m ww_card_poc.cli build-phase2a-inputs \
  --case-metrics data/interim/pre_phase2_recurrence_case_metrics.csv \
  --limit 10 \
  --output data/runs/phase2a_failure_prone_inputs.jsonl

PYTHONPATH=src python3 -m ww_card_poc.cli run-phase2a \
  --input data/runs/phase2a_failure_prone_inputs.jsonl \
  --output data/runs/phase2a_failure_prone_generations.jsonl

PYTHONPATH=src python3 -m ww_card_poc.cli judge-phase2a \
  --generations data/runs/phase2a_failure_prone_generations.jsonl \
  --output data/judgments/phase2a_failure_prone_judgments.jsonl

PYTHONPATH=src python3 -m ww_card_poc.cli summarize-phase2a \
  --judgments data/judgments/phase2a_failure_prone_judgments.jsonl \
  --report reports/phase2a_failure_prone_summary.md \
  --condition-csv data/interim/phase2a_failure_prone_condition_metrics.csv \
  --case-csv data/interim/phase2a_failure_prone_case_metrics.csv \
  --json data/interim/phase2a_failure_prone_condition_metrics.json
```

The runner appends JSONL records and resumes by default. Use `--no-resume` only when intentionally
writing a fresh output path or rerunning a condition into a separate file.
