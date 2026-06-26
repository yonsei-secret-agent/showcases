# Who&When Native Failure Card Experiment Runbook

## Objective

This project tests a narrow PoC claim:

> Gold Who&When attribution can be converted into a standardized runtime Failure Card that reduces recurrence of the decisive error in trace-prefix counterfactual repair.

This is not an end-to-end task rescue claim. The primary unit is the regenerated next action at the
gold intervention point.

## Implemented Pipeline

```text
Who&When JSON traces
-> case audit and structural labels
-> pre-Phase2 no-guidance recurrence pretest
-> failure-prone case selection
-> Phase 2A five-condition generation
-> blind LLM judgment
-> condition and case metrics
```

## Tracked Conditions

```text
no_guidance
strong_generic_guideline
sanitized_raw_gold_explanation
oracle_runtime_card
wrong_mismatched_card
```

`oracle_runtime_card` is agent-visible runtime guidance. It excludes the exact step number, original
failed action, gold answer, and source evidence span.

`sanitized_raw_gold_explanation` intentionally tests whether a cleaned attribution explanation is
enough without structured card conversion.

`wrong_mismatched_card` is selected from a different inferred failure mode when possible. Early smoke
results showed this condition can still help because many cards share generally useful verification
behavior; treat it as a diagnostic control, not a guaranteed negative control.

## Current Selection Logic

The conservative Who&When subset is:

```text
dataset_type == algorithm_generated
mistake_step >= 2
phase2a_status == candidate
history_len <= 10
```

The pre-Phase2 recurrence threshold is:

```text
same_failure_recurrence_rate >= 0.4
```

With 3 no-guidance repeats, this means at least 2 recurring failures out of 3.

## Primary Metrics

```text
same_failure_recurrence_rate
repair_success_rate
mean_repair_score
task_relevance_rate
```

The strongest first-pass signal is:

```text
oracle_runtime_card recurrence < no_guidance recurrence
oracle_runtime_card success > no_guidance success
oracle_runtime_card success > sanitized_raw_gold_explanation success
oracle_runtime_card success > strong_generic_guideline success
```

If `wrong_mismatched_card` is high, do not interpret it as oracle failure by itself. It may indicate
that the card schema is still too generic or that the failure modes in the selected cases are not
orthogonal enough.

## Main Commands

Run from `who_when_card_poc/`.

```bash
PYTHONPATH=src python3 -m ww_card_poc.cli data-audit

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

## Interpretation Boundary

Claim:

```text
Failure Cards can reduce same-failure recurrence at the decisive step.
```

Do not claim from Phase 2A alone:

```text
The original task is solved end-to-end.
The whole multi-agent run is rescued.
The card is reusable across traces.
Predicted Who&When attribution is sufficient.
```

Those require replayable-subset rescue, cross-trace transfer, or Phase 2B predicted-intervention
experiments.
