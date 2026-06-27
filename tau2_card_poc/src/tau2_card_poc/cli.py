from __future__ import annotations

import argparse
from pathlib import Path

from tau2_card_poc.batch_runner import run_manifest
from tau2_card_poc.experiment_manifest import load_experiment_manifest
from tau2_card_poc.reporting import (
    collect_experiment_records,
    condition_summary,
    task_stability_summary,
    write_condition_summary_csv,
    write_task_stability_csv,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tau2-card-poc")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run-manifest")
    run_parser.add_argument("manifest")
    run_parser.add_argument("--output-root", required=True)
    run_parser.add_argument("--no-resume", action="store_true")

    summarize_parser = subparsers.add_parser("summarize")
    summarize_parser.add_argument("experiment_dir")
    summarize_parser.add_argument("--out-dir", required=True)
    summarize_parser.add_argument("--default-condition", default="unknown")

    args = parser.parse_args(argv)
    if args.command == "run-manifest":
        manifest = load_experiment_manifest(args.manifest)
        results = run_manifest(
            manifest,
            output_root=args.output_root,
            resume=not args.no_resume,
        )
        ran = sum(1 for result in results if result.status == "ran")
        skipped = sum(1 for result in results if result.status == "skipped")
        print(f"runs: {len(results)} total, {ran} ran, {skipped} skipped")
        return 0

    if args.command == "summarize":
        experiment_dir = Path(args.experiment_dir)
        out_dir = Path(args.out_dir)
        records = collect_experiment_records(
            experiment_dir,
            default_condition=args.default_condition,
        )
        write_condition_summary_csv(condition_summary(records), out_dir / "condition_summary.csv")
        write_task_stability_csv(task_stability_summary(records), out_dir / "task_stability.csv")
        print(f"wrote summaries for {len(records)} records to {out_dir}")
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
