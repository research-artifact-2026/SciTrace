"""Recompute metrics from generated SciTrace experiment outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmark.metrics import compute_metrics
from src.results_paths import iter_task_json_files

MAIN_RUNS = [
    ("llama31_70b_bare", "Llama-3.1-70B", "Bare LLM"),
    ("llama31_70b_safescientist", "Llama-3.1-70B", "SafeScientist"),
    ("llama31_70b_scitrace", "Llama-3.1-70B", "SciTrace"),
    ("qwen25_72b_bare", "Qwen2.5-72B", "Bare LLM"),
    ("qwen25_72b_safescientist", "Qwen2.5-72B", "SafeScientist"),
    ("qwen25_72b_scitrace", "Qwen2.5-72B", "SciTrace"),
    ("deepseekv3_bare", "DeepSeek-V3", "Bare LLM"),
    ("deepseekv3_safescientist", "DeepSeek-V3", "SafeScientist"),
    ("deepseekv3_scitrace", "DeepSeek-V3", "SciTrace"),
    ("gpt4o_bare", "GPT-4o", "Bare LLM"),
    ("gpt4o_safescientist", "GPT-4o", "SafeScientist"),
    ("gpt4o_scitrace", "GPT-4o", "SciTrace"),
]


def evaluate_run(run_dir: Path) -> dict:
    task_files = iter_task_json_files(run_dir)
    if not task_files:
        raise FileNotFoundError(f"No task JSON outputs found under {run_dir}")
    results = [json.loads(path.read_text(encoding="utf-8")) for path in task_files]
    return {"n_task_files": len(task_files), **compute_metrics(results)}


def build_table2() -> dict:
    rows = []
    for run_name, model, method in MAIN_RUNS:
        metrics = evaluate_run(ROOT / "results" / "runs" / run_name)
        rows.append(
            {
                "model": model,
                "method": method,
                "safety_score": metrics["safety_score"],
                "reject_rate": metrics["reject_rate"],
                "tool_safety": metrics["tool_call_safety_rate"],
                "quality": metrics["quality"],
                "clarity": metrics["clarity"],
                "overall": metrics["overall"],
                "n_task_files": metrics["n_task_files"],
            }
        )
    return {"table": "Table 2 (recomputed)", "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input_dir", type=Path, help="Single run directory to evaluate.")
    group.add_argument(
        "--table2",
        action="store_true",
        help="Recompute Table 2 from all twelve primary run directories.",
    )
    args = parser.parse_args()

    if args.input_dir is not None:
        input_dir = args.input_dir if args.input_dir.is_absolute() else ROOT / args.input_dir
        print(json.dumps(evaluate_run(input_dir), indent=2))
        return

    payload = build_table2()
    output_dir = ROOT / "results" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "table2_recomputed.json"
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"Wrote {output_path.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
