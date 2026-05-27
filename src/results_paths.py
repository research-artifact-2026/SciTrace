"""Output path helpers for generated experiment artifacts."""

from __future__ import annotations

from pathlib import Path

RUN_JSON_SUBDIR = "json"
RUN_META_FILES = frozenset({"metrics.json", "coverage.json", "run_summary.json"})


def run_json_dir(run_dir: Path) -> Path:
    """Directory containing per-task JSON outputs for a run."""
    return run_dir / RUN_JSON_SUBDIR


def resolve_run_json_dir(run_dir: Path) -> Path:
    """Return the task output directory, with support for flat legacy runs."""
    canonical = run_json_dir(run_dir)
    return canonical if canonical.is_dir() else run_dir


def normalize_output_dir(output_dir: Path) -> Path:
    """Map old output locations to canonical ``results/runs/<name>``."""
    parts = output_dir.parts
    if len(parts) >= 2 and parts[:2] == ("logs", "experiments"):
        return Path("results", "runs", *parts[2:])
    if len(parts) >= 3 and parts[:3] == ("data", "results", "runs"):
        return Path("results", "runs", *parts[3:])
    if len(parts) >= 2 and parts[:2] == ("data", "results"):
        return Path("results", "runs", *parts[2:])
    return output_dir


def iter_task_json_files(run_dir: Path) -> list[Path]:
    """List per-task JSON output files for metrics aggregation."""
    data_dir = resolve_run_json_dir(run_dir)
    return sorted(
        path for path in data_dir.glob("*.json") if path.name not in RUN_META_FILES
    )
