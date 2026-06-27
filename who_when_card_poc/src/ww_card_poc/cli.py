from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

from ww_card_poc.case_selection import SmokeCaseFilter, select_smoke_cases, selection_rows
from ww_card_poc.data_audit import (
    load_who_when_cases,
    write_case_index,
    write_data_audit_report,
)
from ww_card_poc.experiment_config import format_experiment_config, load_experiment_config
from ww_card_poc.generation_runner import run_generations
from ww_card_poc.judging import run_judgments
from ww_card_poc.phase2a_inputs import build_phase2a_inputs, write_phase2a_inputs
from ww_card_poc.reality_check import (
    inspect_who_when_repo,
    render_reality_check_report,
    write_reality_check_report,
)
from ww_card_poc.results import (
    paired_contrasts,
    summarize_judgments,
    write_csv,
    write_json,
    write_summary_report,
)
from ww_card_poc.settings import format_settings, load_settings


def check_config(args: argparse.Namespace) -> int:
    dotenv_path = Path(args.env_file) if args.env_file else None
    settings = load_settings(dotenv_path=dotenv_path, override_env=args.override_env)
    print(format_settings(settings))

    errors = settings.validate()
    if errors:
        print("\nConfig issues:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nConfig OK.")
    return 0


def show_experiment(args: argparse.Namespace) -> int:
    config_path = Path(args.config) if args.config else None
    dotenv_path = Path(args.env_file) if args.env_file else None
    config = load_experiment_config(
        config_path,
        dotenv_path=dotenv_path,
        override_env=args.override_env,
    )
    print(format_experiment_config(config))

    errors = config.validate()
    if errors:
        print("\nExperiment config issues:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nExperiment config OK.")
    return 0


def reality_check(args: argparse.Namespace) -> int:
    dotenv_path = Path(args.env_file) if args.env_file else None
    settings = load_settings(dotenv_path=dotenv_path, override_env=args.override_env)
    check = inspect_who_when_repo(settings)
    report = render_reality_check_report(check)
    print(report)

    if args.output:
        output_path = Path(args.output)
        write_reality_check_report(check, output_path)
        print(f"\nWrote report: {output_path}")

    return 0


def data_audit(args: argparse.Namespace) -> int:
    dotenv_path = Path(args.env_file) if args.env_file else None
    settings = load_settings(dotenv_path=dotenv_path, override_env=args.override_env)
    cases = load_who_when_cases(settings.paths.who_when_repo_path)

    if args.case_index:
        case_index_path = Path(args.case_index)
    else:
        case_index_path = settings.paths.data_dir / "interim" / "who_when_case_index.csv"

    if args.report:
        report_path = Path(args.report)
    else:
        report_path = settings.paths.reports_dir / "who_when_data_audit.md"

    write_case_index(cases, case_index_path)
    write_data_audit_report(cases, report_path, sample_count=args.samples)

    print(f"Loaded cases: {len(cases)}")
    print(f"Wrote case index: {case_index_path}")
    print(f"Wrote report: {report_path}")
    return 0


def select_smoke_cases_cmd(args: argparse.Namespace) -> int:
    dotenv_path = Path(args.env_file) if args.env_file else None
    settings = load_settings(dotenv_path=dotenv_path, override_env=args.override_env)
    config = load_experiment_config(dotenv_path=dotenv_path, override_env=args.override_env)
    cases = load_who_when_cases(settings.paths.who_when_repo_path)
    smoke = config.smoke
    smoke_filter = SmokeCaseFilter.from_config(smoke.get("candidate_filter", {}))
    limit = int(args.limit or smoke.get("candidate_cases", 15))
    selected = select_smoke_cases(
        cases,
        smoke_filter=smoke_filter,
        limit=limit,
        stratify_by_failure_mode=bool(smoke.get("stratify_by_failure_mode", False)),
    )

    output_path = (
        Path(args.output)
        if args.output
        else settings.paths.data_dir / "interim" / "smoke_case_selection.csv"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = selection_rows(selected)
    if rows:
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        output_path.write_text("", encoding="utf-8")

    print(f"Selected smoke cases: {len(selected)}")
    print(f"Wrote selection: {output_path}")
    for row in rows[:10]:
        print(
            f"- {row['rank']}: {row['case_id']} "
            f"step={row['mistake_step']} prefix={row['prefix_len']} agent={row['mistake_agent']}"
        )
    return 0


def _case_ids_from_metrics(path: Path, *, min_recurrence: float) -> set[str]:
    if not path.exists():
        return set()
    selected: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("condition") != "no_guidance":
                continue
            raw_rate = row.get("same_failure_recurrence_rate", "")
            try:
                rate = float(raw_rate)
            except ValueError:
                continue
            if rate >= min_recurrence:
                selected.add(str(row.get("case_id", "")))
    return {case_id for case_id in selected if case_id}


def build_phase2a_inputs_cmd(args: argparse.Namespace) -> int:
    dotenv_path = Path(args.env_file) if args.env_file else None
    settings = load_settings(dotenv_path=dotenv_path, override_env=args.override_env)
    config = load_experiment_config(dotenv_path=dotenv_path, override_env=args.override_env)
    cases = load_who_when_cases(settings.paths.who_when_repo_path)
    smoke = config.smoke
    smoke_filter = SmokeCaseFilter.from_config(smoke.get("candidate_filter", {}))
    limit = int(args.limit or smoke.get("main_cases", 10))
    stratify = bool(smoke.get("stratify_by_failure_mode", False))
    mismatch_pool = select_smoke_cases(
        cases,
        smoke_filter=smoke_filter,
        limit=len(cases),
        stratify_by_failure_mode=False,
    )
    if args.case_metrics:
        min_recurrence = float(
            args.min_no_guidance_recurrence
            if args.min_no_guidance_recurrence is not None
            else smoke.get("failure_prone_recurrence_threshold", 0.4)
        )
        selected_ids = _case_ids_from_metrics(Path(args.case_metrics), min_recurrence=min_recurrence)
        selected = [
            case
            for case in select_smoke_cases(
                cases,
                smoke_filter=smoke_filter,
                limit=len(cases),
                stratify_by_failure_mode=stratify,
            )
            if case.case_id in selected_ids
        ][:limit]
    elif args.case_id:
        selected_ids = set(args.case_id)
        selected = [
            case
            for case in select_smoke_cases(
                cases,
                smoke_filter=smoke_filter,
                limit=len(cases),
                stratify_by_failure_mode=stratify,
            )
            if case.case_id in selected_ids
        ][:limit]
    else:
        selected = select_smoke_cases(
            cases,
            smoke_filter=smoke_filter,
            limit=limit,
            stratify_by_failure_mode=stratify,
        )
    conditions = list(args.conditions or smoke.get("conditions", []))
    records = build_phase2a_inputs(
        selected,
        conditions=conditions,
        mismatch_pool=mismatch_pool,
        block_leakage=True,
    )

    output_path = (
        Path(args.output)
        if args.output
        else settings.paths.data_dir / "runs" / "phase2a_smoke_inputs.jsonl"
    )
    write_phase2a_inputs(records, output_path)

    flagged = sum(1 for record in records if record.leakage_flags)
    print(f"Selected cases: {len(selected)}")
    print(f"Conditions: {conditions}")
    print(f"Built Phase 2A input records: {len(records)}")
    print(f"Records with leakage flags: {flagged}")
    print(f"Wrote inputs: {output_path}")
    return 0


def run_phase2a_cmd(args: argparse.Namespace) -> int:
    dotenv_path = Path(args.env_file) if args.env_file else None
    settings = load_settings(dotenv_path=dotenv_path, override_env=args.override_env)
    errors = settings.validate()
    if errors:
        print("Config issues:")
        for error in errors:
            print(f"- {error}")
        return 1

    input_path = (
        Path(args.input)
        if args.input
        else settings.paths.data_dir / "runs" / "phase2a_smoke_inputs.jsonl"
    )
    output_path = (
        Path(args.output)
        if args.output
        else settings.paths.data_dir / "runs" / "phase2a_smoke_generations.jsonl"
    )
    case_ids = set(args.case_id or []) or None
    conditions = set(args.conditions or []) or None
    records = run_generations(
        settings=settings,
        input_path=input_path,
        output_path=output_path,
        repeats=args.repeats,
        limit_records=args.limit_records,
        case_ids=case_ids,
        conditions=conditions,
        temperature_mode=args.temperature_mode,
        dry_run=args.dry_run,
        resume=not args.no_resume,
    )
    errors_written = sum(1 for record in records if record.error)
    print(f"Generation records written: {len(records)}")
    print(f"Errors: {errors_written}")
    print(f"Output: {output_path}")
    return 1 if errors_written else 0


def judge_phase2a_cmd(args: argparse.Namespace) -> int:
    dotenv_path = Path(args.env_file) if args.env_file else None
    settings = load_settings(dotenv_path=dotenv_path, override_env=args.override_env)
    errors = settings.validate()
    if errors:
        print("Config issues:")
        for error in errors:
            print(f"- {error}")
        return 1

    cases = load_who_when_cases(settings.paths.who_when_repo_path)
    generations_path = (
        Path(args.generations)
        if args.generations
        else settings.paths.data_dir / "runs" / "phase2a_smoke_generations.jsonl"
    )
    output_path = (
        Path(args.output)
        if args.output
        else settings.paths.data_dir / "judgments" / "phase2a_smoke_judgments.jsonl"
    )
    records = run_judgments(
        settings=settings,
        generations_path=generations_path,
        output_path=output_path,
        cases=cases,
        limit_records=args.limit_records,
        dry_run=args.dry_run,
        resume=not args.no_resume,
    )
    errors_written = sum(1 for record in records if record.error)
    print(f"Judgment records written: {len(records)}")
    print(f"Errors: {errors_written}")
    print(f"Output: {output_path}")
    return 1 if errors_written else 0


def summarize_phase2a_cmd(args: argparse.Namespace) -> int:
    dotenv_path = Path(args.env_file) if args.env_file else None
    settings = load_settings(dotenv_path=dotenv_path, override_env=args.override_env)
    judgments_path = (
        Path(args.judgments)
        if args.judgments
        else settings.paths.data_dir / "judgments" / "phase2a_smoke_judgments.jsonl"
    )
    condition_rows, case_rows = summarize_judgments(judgments_path)
    paired_rows = paired_contrasts(case_rows)

    summary_path = (
        Path(args.report)
        if args.report
        else settings.paths.reports_dir / "phase2a_smoke_summary.md"
    )
    condition_csv_path = (
        Path(args.condition_csv)
        if args.condition_csv
        else settings.paths.data_dir / "interim" / "phase2a_condition_metrics.csv"
    )
    case_csv_path = (
        Path(args.case_csv)
        if args.case_csv
        else settings.paths.data_dir / "interim" / "phase2a_case_metrics.csv"
    )
    json_path = (
        Path(args.json)
        if args.json
        else settings.paths.data_dir / "interim" / "phase2a_condition_metrics.json"
    )
    write_summary_report(condition_rows, summary_path, paired_rows=paired_rows)
    write_csv(condition_rows, condition_csv_path)
    write_csv(case_rows, case_csv_path)
    write_json(condition_rows, json_path)
    print(f"Condition rows: {len(condition_rows)}")
    print(f"Case-condition rows: {len(case_rows)}")
    print(f"Report: {summary_path}")
    print(f"Condition CSV: {condition_csv_path}")
    print(f"Case CSV: {case_csv_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ww-card-poc")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check-config", help="Validate .env and model settings.")
    check.add_argument("--env-file", default=None, help="Path to an env file. Defaults to .env.")
    check.add_argument(
        "--override-env",
        action="store_true",
        help="Let env file values override already-set process env vars.",
    )
    check.set_defaults(func=check_config)

    experiment = subparsers.add_parser(
        "show-experiment",
        help="Load and validate configs/experiment.yaml.",
    )
    experiment.add_argument("--config", default=None, help="Path to experiment YAML.")
    experiment.add_argument("--env-file", default=None, help="Path to an env file. Defaults to .env.")
    experiment.add_argument(
        "--override-env",
        action="store_true",
        help="Let env file values override already-set process env vars.",
    )
    experiment.set_defaults(func=show_experiment)

    reality = subparsers.add_parser(
        "reality-check",
        help="Inspect the configured Who&When repo path and write a feasibility stub report.",
    )
    reality.add_argument("--env-file", default=None, help="Path to an env file. Defaults to .env.")
    reality.add_argument(
        "--override-env",
        action="store_true",
        help="Let env file values override already-set process env vars.",
    )
    reality.add_argument(
        "--output",
        default=None,
        help="Optional markdown path for the reality-check report.",
    )
    reality.set_defaults(func=reality_check)

    audit = subparsers.add_parser(
        "data-audit",
        help="Parse Who&When JSON files and build the initial case index.",
    )
    audit.add_argument("--env-file", default=None, help="Path to an env file. Defaults to .env.")
    audit.add_argument(
        "--override-env",
        action="store_true",
        help="Let env file values override already-set process env vars.",
    )
    audit.add_argument(
        "--case-index",
        default=None,
        help="Output CSV path. Defaults to data/interim/who_when_case_index.csv.",
    )
    audit.add_argument(
        "--report",
        default=None,
        help="Output markdown path. Defaults to reports/who_when_data_audit.md.",
    )
    audit.add_argument(
        "--samples",
        type=int,
        default=4,
        help="Number of sample cases to include in the markdown report.",
    )
    audit.set_defaults(func=data_audit)

    select = subparsers.add_parser(
        "select-smoke-cases",
        help="Select conservative smoke cases from the Who&When case index rules.",
    )
    select.add_argument("--env-file", default=None, help="Path to an env file. Defaults to .env.")
    select.add_argument(
        "--override-env",
        action="store_true",
        help="Let env file values override already-set process env vars.",
    )
    select.add_argument("--limit", type=int, default=None, help="Override smoke candidate limit.")
    select.add_argument(
        "--output",
        default=None,
        help="Output CSV path. Defaults to data/interim/smoke_case_selection.csv.",
    )
    select.set_defaults(func=select_smoke_cases_cmd)

    phase2a = subparsers.add_parser(
        "build-phase2a-inputs",
        help="Build API-free Phase 2A prompt inputs for the smoke run.",
    )
    phase2a.add_argument("--env-file", default=None, help="Path to an env file. Defaults to .env.")
    phase2a.add_argument(
        "--override-env",
        action="store_true",
        help="Let env file values override already-set process env vars.",
    )
    phase2a.add_argument("--limit", type=int, default=None, help="Override selected main cases.")
    phase2a.add_argument("--case-id", nargs="+", default=None, help="Build inputs for selected cases.")
    phase2a.add_argument(
        "--case-metrics",
        default=None,
        help="Use case metrics CSV to select failure-prone no-guidance cases.",
    )
    phase2a.add_argument(
        "--min-no-guidance-recurrence",
        type=float,
        default=None,
        help="Minimum no-guidance recurrence rate when --case-metrics is provided.",
    )
    phase2a.add_argument(
        "--conditions",
        nargs="+",
        default=None,
        help="Override condition list from experiment.yaml.",
    )
    phase2a.add_argument(
        "--output",
        default=None,
        help="Output JSONL path. Defaults to data/runs/phase2a_smoke_inputs.jsonl.",
    )
    phase2a.set_defaults(func=build_phase2a_inputs_cmd)

    run_phase2a = subparsers.add_parser(
        "run-phase2a",
        help="Call the generation model for Phase 2A input records.",
    )
    run_phase2a.add_argument("--env-file", default=None, help="Path to an env file. Defaults to .env.")
    run_phase2a.add_argument(
        "--override-env",
        action="store_true",
        help="Let env file values override already-set process env vars.",
    )
    run_phase2a.add_argument(
        "--input",
        default=None,
        help="Input JSONL path. Defaults to data/runs/phase2a_smoke_inputs.jsonl.",
    )
    run_phase2a.add_argument(
        "--output",
        default=None,
        help="Output JSONL path. Defaults to data/runs/phase2a_smoke_generations.jsonl.",
    )
    run_phase2a.add_argument("--repeats", type=int, default=1, help="Attempts per input record.")
    run_phase2a.add_argument("--limit-records", type=int, default=None, help="Limit input records.")
    run_phase2a.add_argument("--case-id", nargs="+", default=None, help="Only run selected cases.")
    run_phase2a.add_argument(
        "--conditions",
        nargs="+",
        default=None,
        help="Only run selected conditions.",
    )
    run_phase2a.add_argument(
        "--temperature-mode",
        default="generation",
        help="Use 'generation', 'recurrence', or a numeric temperature.",
    )
    run_phase2a.add_argument("--dry-run", action="store_true", help="Write placeholder outputs.")
    run_phase2a.add_argument(
        "--no-resume",
        action="store_true",
        help="Do not skip run_id/attempt pairs already present in the output file.",
    )
    run_phase2a.set_defaults(func=run_phase2a_cmd)

    judge_phase2a = subparsers.add_parser(
        "judge-phase2a",
        help="Judge Phase 2A generations for same-failure recurrence and repair success.",
    )
    judge_phase2a.add_argument("--env-file", default=None, help="Path to an env file. Defaults to .env.")
    judge_phase2a.add_argument(
        "--override-env",
        action="store_true",
        help="Let env file values override already-set process env vars.",
    )
    judge_phase2a.add_argument(
        "--generations",
        default=None,
        help="Generation JSONL path. Defaults to data/runs/phase2a_smoke_generations.jsonl.",
    )
    judge_phase2a.add_argument(
        "--output",
        default=None,
        help="Judgment JSONL path. Defaults to data/judgments/phase2a_smoke_judgments.jsonl.",
    )
    judge_phase2a.add_argument("--limit-records", type=int, default=None, help="Limit records.")
    judge_phase2a.add_argument("--dry-run", action="store_true", help="Write placeholder judgments.")
    judge_phase2a.add_argument(
        "--no-resume",
        action="store_true",
        help="Do not skip run_id/attempt pairs already present in the output file.",
    )
    judge_phase2a.set_defaults(func=judge_phase2a_cmd)

    summarize_phase2a = subparsers.add_parser(
        "summarize-phase2a",
        help="Summarize Phase 2A judgment JSONL into metrics.",
    )
    summarize_phase2a.add_argument("--env-file", default=None, help="Path to an env file. Defaults to .env.")
    summarize_phase2a.add_argument(
        "--override-env",
        action="store_true",
        help="Let env file values override already-set process env vars.",
    )
    summarize_phase2a.add_argument(
        "--judgments",
        default=None,
        help="Judgment JSONL path. Defaults to data/judgments/phase2a_smoke_judgments.jsonl.",
    )
    summarize_phase2a.add_argument("--report", default=None, help="Output markdown report path.")
    summarize_phase2a.add_argument("--condition-csv", default=None, help="Output condition CSV path.")
    summarize_phase2a.add_argument("--case-csv", default=None, help="Output case CSV path.")
    summarize_phase2a.add_argument("--json", default=None, help="Output condition JSON path.")
    summarize_phase2a.set_defaults(func=summarize_phase2a_cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
