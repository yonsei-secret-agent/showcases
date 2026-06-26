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
from ww_card_poc.phase2a_inputs import build_phase2a_inputs, write_phase2a_inputs
from ww_card_poc.reality_check import (
    inspect_who_when_repo,
    render_reality_check_report,
    write_reality_check_report,
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
    selected = select_smoke_cases(cases, smoke_filter=smoke_filter, limit=limit)

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


def build_phase2a_inputs_cmd(args: argparse.Namespace) -> int:
    dotenv_path = Path(args.env_file) if args.env_file else None
    settings = load_settings(dotenv_path=dotenv_path, override_env=args.override_env)
    config = load_experiment_config(dotenv_path=dotenv_path, override_env=args.override_env)
    cases = load_who_when_cases(settings.paths.who_when_repo_path)
    smoke = config.smoke
    smoke_filter = SmokeCaseFilter.from_config(smoke.get("candidate_filter", {}))
    limit = int(args.limit or smoke.get("main_cases", 10))
    selected = select_smoke_cases(cases, smoke_filter=smoke_filter, limit=limit)
    conditions = list(args.conditions or smoke.get("conditions", []))
    records = build_phase2a_inputs(selected, conditions=conditions)

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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
