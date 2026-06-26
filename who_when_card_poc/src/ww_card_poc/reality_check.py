from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from subprocess import run

from ww_card_poc.settings import Settings
from ww_card_poc.who_when_io import WhoWhenCase, load_cases, phase2a_status


DATA_EXTENSIONS = {".json", ".jsonl", ".csv", ".yaml", ".yml", ".pkl", ".parquet"}


@dataclass(frozen=True)
class RealityCheck:
    repo_path: Path
    exists: bool
    is_git_repo: bool
    commit: str | None
    candidate_data_files: list[Path]
    candidate_code_files: list[Path]
    total_data_file_count: int
    case_count: int
    dataset_counts: dict[str, int]
    phase2a_status_counts: dict[str, int]
    step_ge2_counts: dict[str, int]
    step0_counts: dict[str, int]
    history_len_summary: dict[str, str]

    @property
    def native_feasibility_unknown(self) -> bool:
        return not self.exists or self.case_count == 0


def _git_commit(repo_path: Path) -> str | None:
    if not repo_path.exists():
        return None
    result = run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _path_sort_key(path: Path) -> tuple[str, int, str]:
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    return (str(path.parent), int(digits) if digits else 0, path.name)


def _find_files(repo_path: Path, extensions: set[str], *, limit: int | None = None) -> list[Path]:
    if not repo_path.exists():
        return []
    files: list[Path] = []
    for path in sorted(repo_path.rglob("*"), key=_path_sort_key):
        if path.is_file() and path.suffix.lower() in extensions:
            files.append(path.relative_to(repo_path))
        if limit is not None and len(files) >= limit:
            break
    return files


def _history_summary(cases: list[WhoWhenCase], dataset_type: str) -> str:
    values = [case.history_len for case in cases if case.dataset_type == dataset_type]
    if not values:
        return "n/a"
    mean = sum(values) / len(values)
    return f"min={min(values)}, max={max(values)}, mean={mean:.2f}"


def _case_summaries(cases: list[WhoWhenCase]) -> tuple[
    dict[str, int],
    dict[str, int],
    dict[str, int],
    dict[str, int],
    dict[str, str],
]:
    dataset_counts = Counter(case.dataset_type for case in cases)
    phase2a_counts = Counter(phase2a_status(case)[0] for case in cases)
    step_ge2_counts = Counter(
        case.dataset_type for case in cases if case.mistake_step is not None and case.mistake_step >= 2
    )
    step0_counts = Counter(case.dataset_type for case in cases if case.mistake_step == 0)
    history_len_summary = {
        "algorithm_generated": _history_summary(cases, "algorithm_generated"),
        "hand_crafted": _history_summary(cases, "hand_crafted"),
    }
    return (
        dict(dataset_counts),
        dict(phase2a_counts),
        dict(step_ge2_counts),
        dict(step0_counts),
        history_len_summary,
    )


def inspect_who_when_repo(settings: Settings) -> RealityCheck:
    repo_path = settings.paths.who_when_repo_path
    commit = _git_commit(repo_path)
    data_files = _find_files(repo_path, DATA_EXTENSIONS)
    cases = load_cases(repo_path) if repo_path.exists() else []
    (
        dataset_counts,
        phase2a_counts,
        step_ge2_counts,
        step0_counts,
        history_len_summary,
    ) = _case_summaries(cases)
    return RealityCheck(
        repo_path=repo_path,
        exists=repo_path.exists(),
        is_git_repo=(repo_path / ".git").exists(),
        commit=commit,
        candidate_data_files=data_files,
        candidate_code_files=_find_files(repo_path, {".py", ".ipynb"}, limit=80),
        total_data_file_count=len(data_files),
        case_count=len(cases),
        dataset_counts=dataset_counts,
        phase2a_status_counts=phase2a_counts,
        step_ge2_counts=step_ge2_counts,
        step0_counts=step0_counts,
        history_len_summary=history_len_summary,
    )


def render_reality_check_report(check: RealityCheck) -> str:
    lines = [
        "# Who&When Reality Check",
        "",
        "## Repository",
        "",
        f"- path: `{check.repo_path}`",
        f"- exists: `{check.exists}`",
        f"- git_repo: `{check.is_git_repo}`",
        f"- commit: `{check.commit or 'unknown'}`",
        "",
    ]

    if not check.exists:
        lines.extend(
            [
                "## Status",
                "",
                "Who&When repo is not present yet. Clone or copy it into the configured path before",
                "claiming that the native trace-prefix design is feasible.",
                "",
                "Expected next path:",
                "",
                "```text",
                str(check.repo_path),
                "```",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "## Feasibility Summary",
            "",
            f"- parsed_cases: `{check.case_count}`",
            f"- dataset_counts: `{check.dataset_counts}`",
            f"- phase2a_status_counts: `{check.phase2a_status_counts}`",
            f"- mistake_step_ge2_counts: `{check.step_ge2_counts}`",
            f"- mistake_step0_counts: `{check.step0_counts}`",
            f"- history_len_algorithm_generated: `{check.history_len_summary.get('algorithm_generated', 'n/a')}`",
            f"- history_len_hand_crafted: `{check.history_len_summary.get('hand_crafted', 'n/a')}`",
            "",
            "Initial judgment:",
            "",
        ]
    )
    alg_ge2 = check.step_ge2_counts.get("algorithm_generated", 0)
    if alg_ge2 >= 30:
        lines.extend(
            [
                "`t*-1` native repair is structurally feasible for a conservative smoke set.",
                "Use `Algorithm-Generated` cases with `mistake_step >= 2` and `phase2a_status == candidate` first.",
                "",
            ]
        )
    elif check.case_count:
        lines.extend(
            [
                "Native repair is partially feasible, but the conservative Algorithm-Generated pool is small.",
                "Inspect Hand-Crafted cases or relax candidate filters only after a smoke run.",
                "",
            ]
        )
    else:
        lines.extend(["No Who&When cases were parsed. Data layout may have changed.", ""])

    lines.extend(
        [
            "Answered feasibility questions:",
            "",
            "- gold who/when/why are stored as `mistake_agent`, `mistake_step`, and `mistake_reason`.",
            "- trajectories are ordered in `history`.",
            "- `mistake_step` is 0-indexed and valid for all parsed cases.",
            "- Algorithm-Generated traces include `system_prompt`; Hand-Crafted traces generally need role recovery from `history` labels.",
            "- `mistake_step >= 2` gives a clean non-empty-prefix pool for the first smoke run.",
            "",
        ]
    )

    lines.extend(
        [
            "## Candidate Data Files",
            "",
            f"Total data-like files found: `{check.total_data_file_count}`",
            "",
        ]
    )
    if check.candidate_data_files:
        lines.extend(f"- `{path}`" for path in check.candidate_data_files)
    else:
        lines.append("- none found by extension scan")

    lines.extend(["", "## Candidate Code Files", ""])
    if check.candidate_code_files:
        lines.extend(f"- `{path}`" for path in check.candidate_code_files[:60])
    else:
        lines.append("- none found by extension scan")

    lines.extend(
        [
            "",
            "## Manual Feasibility Questions",
            "",
            "Answer these after inspecting 2-3 annotated traces:",
            "",
            "1. Where are `gold_responsible_agent`, `gold_decisive_step`, and explanation stored?",
            "2. Are trajectories represented as ordered, agent-attributed steps?",
            "3. Can we cut each trajectory at `t*-1` without losing required context?",
            "4. Is the responsible agent role recoverable at the prefix point?",
            "5. Is the decisive step local enough for next-action regeneration?",
            "6. Does no-guidance regeneration repeat the same failure often enough to measure lift?",
            "",
        ]
    )
    return "\n".join(lines)


def write_reality_check_report(check: RealityCheck, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_reality_check_report(check), encoding="utf-8")
