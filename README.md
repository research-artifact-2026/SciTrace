# SciTrace: Trajectory-Aware Safety Reasoning for Scientific Discovery Agents

> EMNLP 2026 Submission | [Paper](https://anonymous.4open.science/w/SciTrace-4ED3/)

## Overview

SciTrace weaves safety reasoning into every stage of the scientific discovery agent pipeline. It couples the **Safety-Intrinsic Reasoning Loop (SIR)**, which maintains a cumulative risk state across Thinker → Experimenter → Writer → Reviewer, with the **Compositional Tool-Chain Verifier (CTV)**, which scores each tool call on request harmfulness, compositional risk, and tool invocation safety before execution. On 240 high-risk research tasks and 120 tool-risk tasks (six domains), SciTrace improves tool-call safety by **+14.3 pp** on average vs. SafeScientist, adversarial rejection by **+24.7 pp**, and detects **78.8%** of compositional escapes, with **36.9–43.8%** latency overhead depending on backbone.

## Manuscript Alignment Snapshot

- **Key innovations**: SIR performs stage-specific joint task+safety reasoning with a shared cumulative risk state (five levels: `SAFE`, `LOW-RISK`, `WARNING`, `HIGH-RISK`, `BLOCK`); CTV applies trajectory-aware three-part verification (`request_harmfulness`, `compositional_risk`, `tool_invocation_safety`) with TS-Flow safe-redirection feedback.
- **CTV scoring and default threshold**: `s = 0.4 * 1_harmful + 0.4 * 1_compositional + r_tool`, where `r_tool in {0.0, 0.1, 0.2}` and default gating is `ALLOW` (`s < 0.4`), `MODIFY` (`0.4 <= s <= 0.5`), `BLOCK` (`s > 0.5`).
- **Benchmark setup**: SciSafetyBench with 360 tasks total (`240` research + `120` tool-risk), 6 domains (`Biology`, `Chemistry`, `Physics`, `Medicine`, `Information Science`, `Material Science`), and 30 registered tools (`data/benchmark/scisafetybench/tool_registry.json`).
- **Headline results (paper tables)**: Table 2 reports +14.3 pp average tool safety over SafeScientist across 4 backbones; Table 5/15 report 78.8% compositional escape detection; Table 6/7 report +24.7 pp average adversarial rejection gain; Table 14 reports 36.9-43.8% runtime overhead.
- **Reproducibility source of truth**: manuscript aggregates are canonical in `data/table_data/table*.json` (Tables 2-7, 11-16), while `data/results/runs/<run_name>/` and `data/results/runs/` are run artifacts that may differ from paper aggregates.

## Architecture

SciTrace **extends the SafeScientist four-stage pipeline** (Thinker → Experimenter → Writer → Reviewer). That workflow is the retained core.


| Layer                                                      | When active                                                                              |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **SIR** + cumulative risk state + safety memory            | `method=scitrace` (and `safescientist+sir` ablation)                                     |
| **CTV** + TS-Flow + verified tool proxy                    | `method=scitrace` (and `safescientist+ctv` ablation)                                     |
| **SafeScientist monitors** (prompt/output/tool/discussion) | Primary for `method=safescientist` baseline; error fallback only when SIR/CTV are active |

## Canonical Experimental Results

Refer to tables in `data/table_data/` (and manuscript Tables 2–7, 11–16) for key values and full experimental results. The exports below are the authoritative paper aggregates; per-run folders under `data/results/runs/` are experiment artifacts and may differ.

**Qwen2.5-72B (Table 2)** — safety and quality vs. baselines (`table2_main_results.json`):

| Method | Safety ↑ | Reject (%) ↑ | Tool safety (%) ↑ | Clarity ↑ | Overall ↑ |
| ------ | -------- | ------------ | ----------------- | --------- | --------- |
| Bare LLM | 2.38 | 0.0 | 40.2 | 1.85 | 3.15 |
| SafeScientist | 4.75 | 87.0 | 78.1 | 2.50 | 3.50 |
| SciTrace | 4.89 | 93.0 | 92.5 | 2.65 | 3.72 |

Component ablation on the same backbone (`table4a_component_ablation.json`): SafeScientist → +SIR → +CTV → full SciTrace shows tool safety rising from 78.1% to 92.5% with combined SIR+CTV.

- **Compositional escapes (Table 15 / `table15_compositional_escapes.json`)**: SciTrace detects **78.8%** of compositional tool-chain escapes (63/80 on Qwen2.5-72B).
- **Adversarial rejection (Table 7 / `table7_adversarial_rejection.json`)**: per-attack average rejection improves from **48.3%** (SafeScientist) to **73.6%** (SciTrace) on Llama-3.1-70B (**+25.3 pp**); GPT-4o: **55.6%** → **79.7%** (**+24.1 pp**).

## Installation

```bash
pip install -e .
```

GPU: 2× RTX A5000 with AWQ (`quantization=awq`, `tensor_parallel_size=2`) for 70B-class models via vLLM (manuscript setup). Backbone evaluation defaults: `temperature=0.0`, `max_tokens=4096`. GPT-4o judge (Figure 17): `judge_model=gpt-4o`, `judge_temperature=0.0`.

## Environment Variables

```bash
cp .env.example .env
# OPENAI_API_KEY=...
# VLLM_BASE_URL=http://localhost:8000/v1
```

## Quick Start

```python
from scitrace import SciTracePipeline

config = {
    "method": "scitrace",
    "backbone": {"backbone_type": "openai", "model_name": "gpt-4o"},
    "sir": {"enabled": True, "k_checks": 3},
    "ctv": {"enabled": True, "block_threshold": 0.5},
}
pipeline = SciTracePipeline(config)
out = pipeline.run({
    "task_id": "DEMO_001",
    "domain": "Biology",
    "risk_type": "intentional_malice",
    "task_description": "High-level biology survey (non-operational).",
})
print(out["final_paper"])
```

## Running a Local vLLM Backbone

```bash
bash scripts/launch_vllm.sh qwen25_72b    # Qwen/Qwen2.5-72B-Instruct
bash scripts/launch_vllm.sh llama31_70b   # meta-llama/Llama-3.1-70B-Instruct
bash scripts/launch_vllm.sh deepseekv3    # deepseek-ai/DeepSeek-V3
```

## Data layout

| Path | Role |
|------|------|
| `data/benchmark/scisafetybench/` | SciSafetyBench tasks, `tool_registry.json`, and `tool_api_specs.json` |
| `data/results/runs/<experiment_name>/` | **Run artifacts**: per-config `metrics.json` and task outputs (not required to match table JSON) |
| `data/table_data/` | Table-derived CSV/JSON exports for manuscript Tables 2-7 and 11-16 |
| `data/figure_series/` | Figure/graph datasets for manuscript Figure 4-8 and appendix figure series |
| `data/results/runs/` | **Run artifacts**: `experiment_log.json`, summaries from vLLM logs, JSONL traces |

Committed run artifacts under `data/results/runs/<run>/` may be **representative replicas** or partial runs; paper numbers stay authoritative in `data/table_data/table*.json`. See [data/README.md](data/README.md) for detail.

## Running Experiments

```bash
python scripts/run_single_config.py --config experiments/configs/qwen25_72b_scitrace.yaml
python scripts/run_single_config.py --config experiments/configs/json/qwen25_72b_scitrace.json
python scripts/run_single_config.py --config experiments/configs/qwen25_72b_scitrace.yaml --max_tasks 1 --offline_deterministic --skip_grading
python scripts/backfill_missing_results.py --all_existing --offline_deterministic --skip_grading
bash scripts/run_experiments.sh
```

Default behavior runs full benchmark task coverage for the selected config (research + tool). Use `--max_tasks` only for smoke tests. Each `data/results/runs/<experiment_name>/` run folder now includes `coverage.json` with expected vs produced task coverage by domain and task type.

## Evaluating Saved Results

```bash
python scripts/evaluate_results.py --input_dir data/results/runs/qwen25_72b_scitrace/
python scripts/evaluate_results.py --all
```

Use `--use_judge` only when invoking the GPT-4o judge.



