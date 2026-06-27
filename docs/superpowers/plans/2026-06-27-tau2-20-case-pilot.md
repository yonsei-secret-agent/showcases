# tau2 20-Case Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run the next tau2 pilot as a reproducible 20-case decision gate.

**Architecture:** Use tau2 official CLI for no-memory baseline harvest and a manifest-driven `tau2_card_poc` batch runner for memory retry experiments. Each experiment is independent: a manifest defines task IDs, conditions, seeds, and output paths; reports are regenerated from saved results without editing code.

**Tech Stack:** Python stdlib, tau2-bench local clone, `unittest`, existing `tau2_card_poc.memory_runner` and `results_io`.

---

### Task 1: Baseline Harvest Manifest And Documentation

**Files:**
- Create: `tau2_card_poc/experiments/exp5_2_baseline_harvest_30.json`
- Create: `docs/experiment5_2.md`

- [ ] Define 30 candidate retail tasks: prior stable-fail tasks from existing tau2 final results plus low-success mixed tasks.
- [ ] Specify baseline seeds `[401, 402, 403]`, model pair `gpt-4.1-mini`, and no-memory condition.
- [ ] Document the official tau2 CLI command and selection rule for a 20-case rescue set.

### Task 2: Manifest-Driven Batch Runner

**Files:**
- Create: `tau2_card_poc/src/tau2_card_poc/experiment_manifest.py`
- Create: `tau2_card_poc/src/tau2_card_poc/batch_runner.py`
- Create: `tau2_card_poc/src/tau2_card_poc/cli.py`
- Test: `tau2_card_poc/tests/test_experiment_manifest.py`
- Test: `tau2_card_poc/tests/test_batch_runner.py`

- [ ] Add tests for loading manifest conditions and constructing stable per-run output directories.
- [ ] Add tests for resume behavior: existing `results.json` is skipped unless `resume=False`.
- [ ] Implement minimal manifest dataclasses and `run_manifest`.
- [ ] Add CLI subcommands `run-manifest` and `summarize`.

### Task 3: Summary And Case Selection

**Files:**
- Create: `tau2_card_poc/src/tau2_card_poc/reporting.py`
- Test: `tau2_card_poc/tests/test_reporting.py`

- [ ] Add tests for condition-level aggregation from saved `results.json` files.
- [ ] Add tests for baseline task grouping into `stable_failure`, `mixed`, `stable_success`.
- [ ] Implement CSV and Markdown summary generation.
- [ ] Include per-task component scores: final reward, DB, COMMUNICATE, NL_ASSERTION.

### Task 4: Rescue Template

**Files:**
- Create: `tau2_card_poc/experiments/exp5_3_rescue_20_template.json`
- Create: `docs/experiment5_3.md`

- [ ] Define four-condition rescue structure: `no_memory`, `generic_policy_card`, `oracle_single_missing_check_card`, `hard_mismatched_card`.
- [ ] Leave task IDs and oracle cards as manifest fields filled after baseline harvest and annotation.
- [ ] Document leakage and single-missing-check constraints.

### Task 5: Verification And First Execution

**Commands:**
- Run unit tests with `PYTHONPATH=tau2_card_poc/src:third_party/tau2-bench/src python3 -m unittest discover -s tau2_card_poc/tests`.
- Run baseline harvest using tau2 official CLI for 30 tasks × 3 trials.
- Summarize the harvest and select 20 rescue candidates.

**Stop condition:** Do not run 20-case rescue until baseline harvest summary exists and the selected tasks have oracle single-missing-check annotations.
