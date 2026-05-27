"""Canonical + backward-compatible result path helpers."""

from __future__ import annotations

from pathlib import Path

TABLES_SUBDIR = Path("tables/json")
TABLE_DATA_SUBDIR = Path("../table_data")
RUNS_SUBDIR = Path("runs")
RUN_JSON_SUBDIR = "json"
RUN_META_FILES = frozenset({"metrics.json", "coverage.json", "benchmark_coverage.json"})
TABLE_EXPORT_FILENAME_MAP = {
    "main_results_table2.json": "table2_main_results.json",
    "main_results_table3.json": "table3_baseline_comparison.json",
    "ablation_table4a.json": "table4a_component_ablation.json",
    "ablation_table4b.json": "table4b_reviewer_ablation.json",
    "per_domain_table5.json": "table5_per_domain.json",
    "adversarial_table6.json": "table6_discussion_attacker.json",
    "adversarial_table7.json": "table7_adversarial_rejection.json",
    "tool_distribution_table11.json": "table11_tool_distribution.json",
    "ctv_threshold_sweep_table12.json": "table12_ctv_threshold_sweep.json",
    "ctv_weight_ablation_table13.json": "table13_ctv_weight_ablation.json",
    "latency_table14.json": "table14_latency.json",
    "compositional_escape_details_table15.json": "table15_compositional_escapes.json",
    "table16_confidence_interval.json": "table16_confidence_interval.json",
}


def canonical_tables_dir(results_root: Path) -> Path:
    return results_root / TABLES_SUBDIR


def canonical_table_exports_dir(results_root: Path) -> Path:
    return results_root / TABLE_DATA_SUBDIR


def table_file_path(results_root: Path, filename: str) -> Path:
    """Resolve canonical table file from data/table_data first, then legacy paths."""
    mapped_name = TABLE_EXPORT_FILENAME_MAP.get(filename, filename)
    canonical_export = canonical_table_exports_dir(results_root) / mapped_name
    if canonical_export.exists():
        return canonical_export

    canonical = canonical_tables_dir(results_root) / filename
    if canonical.exists():
        return canonical
    return results_root / filename


def canonical_run_dir(results_root: Path, run_key: str | Path) -> Path:
    run_rel = Path(run_key)
    return results_root / RUNS_SUBDIR / run_rel


def resolve_run_dir(results_root: Path, run_key: str | Path) -> Path:
    """Resolve run directory from canonical layout, then legacy layout."""
    run_rel = Path(run_key)
    canonical = canonical_run_dir(results_root, run_rel)
    if canonical.is_dir():
        return canonical
    legacy = results_root / run_rel
    if legacy.is_dir():
        return legacy
    return canonical


def run_json_dir(run_dir: Path) -> Path:
    return run_dir / RUN_JSON_SUBDIR


def resolve_run_json_dir(run_dir: Path) -> Path:
    canonical = run_json_dir(run_dir)
    if canonical.is_dir():
        return canonical
    return run_dir


def normalize_output_dir(output_dir: Path) -> Path:
    """Map legacy paths to canonical ``data/results/runs/<name>``."""
    parts = output_dir.parts
    if len(parts) >= 2 and parts[0] == "logs" and parts[1] == "experiments":
        suffix = parts[2:] if len(parts) > 2 else ()
        return Path("data", "results", "runs", *suffix)
    if len(parts) >= 2 and parts[0] == "data" and parts[1] == "results":
        if len(parts) >= 3 and parts[2] == "runs":
            return output_dir
        return Path("data", "results", "runs", *parts[2:])
    return output_dir


def iter_task_json_files(run_dir: Path) -> list[Path]:
    """Return task output JSON files, preferring canonical ``json/`` layout."""
    data_dir = resolve_run_json_dir(run_dir)
    return sorted(path for path in data_dir.glob("*.json") if path.name not in RUN_META_FILES)
