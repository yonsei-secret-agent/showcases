# Who&When Phase 2A Smoke Results

## Scope

This smoke run evaluates the narrow trace-prefix repair claim:

> If a gold Who&When attribution is converted into a runtime Failure Card, does it reduce recurrence of the decisive error at the gold intervention point?

This is not an end-to-end task rescue result.

## Setup

```text
benchmark source: Who&When local clone
subset: algorithm_generated
candidate filter: mistake_step >= 2, phase2a_status == candidate, history_len <= 10
generation model: openai/gpt-4o-mini-2024-07-18
judge model: openai/gpt-4o
backend: OpenRouter, fixed OpenAI provider order, fallbacks disabled
```

## Pre-Phase2 Recurrence Pretest

Purpose: estimate whether no-guidance regeneration still repeats the original decisive error.

```text
candidate cases: 15
repeats per case: 3
generation records: 45
judge records: 45
errors: 0
```

| condition | n | repair_success_rate | same_failure_recurrence_rate | mean_score |
| --- | ---: | ---: | ---: | ---: |
| no_guidance | 45 | 0.2889 | 0.7111 | 1.4222 |

Failure-prone threshold:

```text
same_failure_recurrence_rate >= 0.4
```

Result:

```text
11 / 15 candidate cases passed the failure-prone threshold.
10 cases were selected for the Phase 2A smoke run.
```

## Phase 2A Failure-Prone Smoke

```text
cases: 10
conditions: 5
generation records: 50
judge records: 50
errors: 0
```

| condition | n | repair_success_rate | same_failure_recurrence_rate | mean_score |
| --- | ---: | ---: | ---: | ---: |
| no_guidance | 10 | 0.1 | 0.9 | 1.1 |
| strong_generic_guideline | 10 | 0.2 | 0.8 | 1.3 |
| sanitized_raw_gold_explanation | 10 | 0.3 | 0.6 | 1.5 |
| oracle_runtime_card | 10 | 0.6 | 0.2 | 2.2 |
| wrong_mismatched_card | 10 | 0.8 | 0.2 | 2.6 |

## Initial Read

The positive signal is clear:

```text
oracle_runtime_card improves repair success from 0.1 to 0.6
oracle_runtime_card reduces same-failure recurrence from 0.9 to 0.2
oracle_runtime_card beats generic guidance and sanitized raw gold explanation
```

The control signal is not clean:

```text
wrong_mismatched_card also performs strongly
```

This likely means the current runtime cards are still too broadly useful as verification guidance,
or that the selected failure modes are not orthogonal enough for this negative control. The result
does not invalidate the PoC, but it weakens the specificity claim. The next iteration should make
the mismatched-card control stricter or create failure-mode-specific cards with more differentiated
interventions.

## Claim Boundary

Supported by this smoke run:

```text
Gold attribution-derived runtime cards can reduce same-failure recurrence at the decisive step.
```

Not supported yet:

```text
The original task is solved end-to-end.
Wrong cards reliably hurt.
Predicted Who&When attribution is sufficient.
The card transfers across traces or systems.
```

## Generated Local Artifacts

These files are intentionally ignored by git:

```text
who_when_card_poc/reports/pre_phase2_recurrence_summary.md
who_when_card_poc/reports/phase2a_failure_prone_summary_v2.md
who_when_card_poc/data/runs/pre_phase2_recurrence_generations.jsonl
who_when_card_poc/data/runs/phase2a_failure_prone_generations.jsonl
who_when_card_poc/data/judgments/pre_phase2_recurrence_judgments.jsonl
who_when_card_poc/data/judgments/phase2a_failure_prone_judgments_v2.jsonl
```
