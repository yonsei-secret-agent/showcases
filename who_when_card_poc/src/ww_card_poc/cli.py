from __future__ import annotations

import argparse
from pathlib import Path
import sys

from ww_card_poc.data_audit import (
    load_who_when_cases,
    write_case_index,
    write_data_audit_report,
)
from ww_card_poc.experiment_config import format_experiment_config, load_experiment_config
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
