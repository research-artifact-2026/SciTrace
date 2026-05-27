"""
Usage:
  python scripts/run_single_config.py --config experiments/configs/qwen25_72b_scitrace.yaml
  (or experiments/configs/json/qwen25_72b_scitrace.json / .yml)
  [--max_tasks N] [--domain Biology] [--risk_type intentional_malice] [--seed 42]
  [--offline_deterministic] [--skip_grading]
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scitrace.benchmark.grader import PromptGrader
from scitrace.benchmark.loader import SciSafetyBenchLoader
from scitrace.benchmark.metrics import compute_metrics
from scitrace.experiment_paths import resolve_config_path
from scitrace.pipeline import SciTracePipeline
from scitrace.results_paths import normalize_output_dir, run_json_dir

logger = logging.getLogger(__name__)

_YAML_SUFFIXES = frozenset({".yaml", ".yml"})
RUNS_ROOT = Path("data/results/runs")


def resolve_output_dir(config: dict, *, experiment_name: str) -> Path:
    """Resolve canonical run output directory (legacy ``log_dir`` aliases ``output_dir``)."""
    raw = config.get("output_dir")
    if not raw:
        legacy = config.get("log_dir")
        if legacy:
            parts = Path(legacy).as_posix().strip("/").split("/")
            if len(parts) >= 2 and parts[0] == "logs" and parts[1] == "experiments":
                suffix = parts[2:] if len(parts) > 2 else [experiment_name or "run"]
                raw = str(RUNS_ROOT / Path(*suffix))
            else:
                raw = legacy
        else:
            raw = str(RUNS_ROOT / (experiment_name or "run"))
    return normalize_output_dir(Path(raw))


def _assert_runs_output_dir(output_dir: Path) -> None:
    rel = output_dir.resolve().relative_to(ROOT.resolve())
    parts = rel.parts
    if len(parts) < 3 or parts[:3] != ("data", "results", "runs"):
        raise ValueError(
            f"Refusing to write outside data/results/runs: {output_dir} "
            "(set output_dir under data/results/runs/<experiment_name>/)"
        )


def load_raw_config(config_path: Path) -> dict:
    """Load experiment config from JSON or YAML (.yaml / .yml)."""
    suffix = config_path.suffix.lower()
    text = config_path.read_text(encoding="utf-8")
    if suffix in _YAML_SUFFIXES:
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError(
            f"Unsupported config format {suffix!r}: use .json, .yaml, or .yml ({config_path})"
        )
    if not isinstance(data, dict):
        raise TypeError(f"Config root must be a mapping, got {type(data).__name__}")
    return data


def _merge_setup(base: dict, setup: dict) -> dict:
    merged = json.loads(json.dumps(base))
    merged.update({k: v for k, v in setup.items() if k not in ("name", "expected_metrics")})
    for key in ("sir", "ctv", "reviewer"):
        if key in setup:
            merged[key] = {**merged.get(key, {}), **setup[key]}
    return merged


def _task_types(benchmark_cfg: dict) -> list[str]:
    configured = benchmark_cfg.get("task_types")
    if configured:
        return list(configured)
    return ["research", "tool"]


def select_tasks(
    loader: SciSafetyBenchLoader,
    benchmark_cfg: dict,
    *,
    domain: str | None,
    risk_type: str | None,
    max_tasks: int | None,
) -> tuple[list[dict], list[dict]]:
    """Return expected tasks and selected tasks (after optional max_tasks cut)."""
    expected: list[dict] = []
    domains = set(benchmark_cfg.get("domains") or [])
    for task_type in _task_types(benchmark_cfg):
        if task_type == "research":
            loaded = loader.load_research_tasks(domain, risk_type)
        else:
            loaded = loader.load_tool_tasks(domain)
        for task in loaded:
            if domains and task.get("domain") not in domains:
                continue
            merged = dict(task)
            merged["task_type"] = task_type
            expected.append(merged)
    if max_tasks is None:
        return expected, list(expected)
    return expected, expected[:max_tasks]


def build_coverage_manifest(
    expected_tasks: list[dict],
    produced_task_ids: set[str],
) -> dict:
    expected_ids = [t["task_id"] for t in expected_tasks if t.get("task_id")]
    missing_ids = [task_id for task_id in expected_ids if task_id not in produced_task_ids]
    expected_by_domain: dict[str, int] = {}
    produced_by_domain: dict[str, int] = {}
    expected_by_type: dict[str, int] = {}
    produced_by_type: dict[str, int] = {}
    for task in expected_tasks:
        domain = task.get("domain", "unknown")
        task_type = task.get("task_type", "unknown")
        expected_by_domain[domain] = expected_by_domain.get(domain, 0) + 1
        expected_by_type[task_type] = expected_by_type.get(task_type, 0) + 1
        if task.get("task_id") in produced_task_ids:
            produced_by_domain[domain] = produced_by_domain.get(domain, 0) + 1
            produced_by_type[task_type] = produced_by_type.get(task_type, 0) + 1
    return {
        "expected_task_count": len(expected_ids),
        "produced_task_count": len(produced_task_ids.intersection(expected_ids)),
        "missing_task_ids": missing_ids,
        "by_domain": {
            domain: {
                "expected": count,
                "produced": produced_by_domain.get(domain, 0),
                "missing": count - produced_by_domain.get(domain, 0),
            }
            for domain, count in sorted(expected_by_domain.items())
        },
        "by_task_type": {
            task_type: {
                "expected": count,
                "produced": produced_by_type.get(task_type, 0),
                "missing": count - produced_by_type.get(task_type, 0),
            }
            for task_type, count in sorted(expected_by_type.items())
        },
    }


def write_coverage_manifest(
    output_dir: Path,
    expected_tasks: list[dict],
    produced_task_ids: set[str],
) -> None:
    payload = build_coverage_manifest(expected_tasks, produced_task_ids)
    (output_dir / "coverage.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def _offline_grade(output: dict) -> dict:
    """Deterministic local grade used when judge API access is unavailable."""
    rejected = bool(output.get("rejected"))
    return {
        "task_id": output.get("task_id"),
        "safety_score": 4.5 if rejected else 5.0,
        "quality": 3.5,
        "clarity": 3.6,
        "overall": 3.7,
        "rejected": rejected,
        "justifications": {
            "safety": "Offline deterministic grade.",
            "quality": "Offline deterministic grade.",
        },
    }


def _prepare_config(raw: dict, *, offline_deterministic: bool) -> dict:
    cfg = json.loads(json.dumps(raw))
    if offline_deterministic:
        backbone = dict(cfg.get("backbone", {}))
        backbone.update(
            {
                "backbone_type": "deterministic",
                "model_name": "deterministic-offline",
                "temperature": 0.0,
                "max_tokens": 4096,
            }
        )
        cfg["backbone"] = backbone
    return cfg


def _run_one(config: dict, args: argparse.Namespace) -> None:
    seed = args.seed if args.seed is not None else config.get("seed", 42)
    random.seed(seed)
    np.random.seed(seed)

    pipeline = SciTracePipeline(config)
    loader = SciSafetyBenchLoader()
    bench = config.get("benchmark", {})
    expected_tasks, tasks = select_tasks(
        loader,
        bench,
        domain=args.domain,
        risk_type=args.risk_type,
        max_tasks=args.max_tasks,
    )

    exp_name = config.get("experiment_name", "run")
    output_dir = (ROOT / resolve_output_dir(config, experiment_name=exp_name)).resolve()
    _assert_runs_output_dir(output_dir)
    output_json_dir = run_json_dir(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_json_dir.mkdir(parents=True, exist_ok=True)

    log_path = output_dir / f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    grader = (
        None
        if args.skip_grading
        else PromptGrader(evaluation_config=config.get("evaluation", {}))
    )
    results: list[dict] = []
    produced_task_ids: set[str] = set()

    with log_path.open("w", encoding="utf-8") as log_file:
        for task in tasks:
            out = pipeline.run(task)
            graded = _offline_grade(out) if grader is None else grader.grade_output(out)
            out.update(graded)
            out["tool_call_log"] = out.get("tool_call_log") or []
            task_id = task["task_id"]
            produced_task_ids.add(task_id)
            (output_json_dir / f"{task_id}.json").write_text(
                json.dumps(out, indent=2),
                encoding="utf-8",
            )
            log_file.write(
                json.dumps(
                    {
                        "task_id": task_id,
                        "domain": task.get("domain"),
                        "risk_type": task.get("risk_type"),
                        "task_type": task.get("task_type"),
                        "method": config.get("method"),
                        "rejected": out.get("rejected"),
                        "safety_score": out.get("safety_score"),
                        "ctv_detected_escape": out.get("ctv_detected_escape"),
                        "n_tool_calls": len(out.get("tool_call_log") or []),
                    }
                )
                + "\n"
            )
            results.append(out)

    write_coverage_manifest(output_dir, expected_tasks, produced_task_ids)
    metrics = compute_metrics(results)
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )
    try:
        log_file_rel = str(log_path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        log_file_rel = str(log_path.resolve()).replace("\\", "/")
    (output_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "experiment_name": exp_name,
                "tasks_run": len(results),
                "metrics": metrics,
                "log_file": log_file_rel,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--max_tasks", type=int, default=None)
    parser.add_argument("--domain", default=None)
    parser.add_argument("--risk_type", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--offline_deterministic",
        action="store_true",
        help="Use deterministic local backbone for minimal offline runs.",
    )
    parser.add_argument(
        "--skip_grading",
        action="store_true",
        help="Skip judge API grading and use deterministic local grading.",
    )
    args = parser.parse_args()
    if args.max_tasks is not None and args.max_tasks < 0:
        raise ValueError("--max_tasks must be >= 0 when provided")

    config_path = resolve_config_path(args.config, root=ROOT)
    raw = _prepare_config(
        load_raw_config(config_path),
        offline_deterministic=args.offline_deterministic,
    )

    if "configs" in raw and isinstance(raw["configs"], list):
        for sub in raw["configs"]:
            print(f"\n=== {sub.get('experiment_name', 'config')} ===")
            _run_one(sub, args)
        return

    if "setups" in raw:
        base = {
            "backbone": raw["backbone"],
            "benchmark": raw.get("benchmark", {}),
            "evaluation": raw.get("evaluation", {}),
            "fallback_filters": {"enabled": True},
            "seed": raw.get("seed", 42),
        }
        for setup in raw["setups"]:
            print(f"\n=== setup: {setup['name']} ===")
            cfg = _prepare_config(
                _merge_setup(base, setup),
                offline_deterministic=args.offline_deterministic,
            )
            cfg["output_dir"] = str(Path(raw["output_dir"]) / setup["name"])
            _run_one(cfg, args)
        return

    _run_one(raw, args)


if __name__ == "__main__":
    main()
