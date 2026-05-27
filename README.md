# SciTrace: Trajectory-Aware Safety Reasoning for Scientific Discovery Agents

Anonymous code release for the SciTrace submission.

## Scope

This compact repository contains the core SciTrace pipeline, its SIR and CTV
safety components, the SafeScientist comparison wiring, and the twelve primary
backbone-by-method experiment configurations used for the main comparison.

The executable release scope is the primary experiment suite represented by
Table 2. Compact JSON snapshots for Tables 2, 3, 4(a), and 4(b) are retained in
`results/reference_tables/` for reviewer orientation. Table 3 includes
third-party framework comparisons and Table 4 includes ablations; their
additional framework/ablation execution bundles are intentionally omitted from
this lean core-code release. The Table 3 snapshot is named
`results/reference_tables/table3_comparison.json`.

## Layout

```text
src/                       Core pipeline, SIR, CTV, stages, tools, and evaluation
scripts/                   Experiment runner, result evaluator, optional vLLM launcher
configs/main/              Twelve primary YAML experiment configs
data/scisafetybench/       Lightweight benchmark task and tool metadata JSON files
data/example/              Benign toy inputs for API inspection
results/reference_tables/  Retained Tables 2, 3, and 4 JSON snapshots
results/                   Generated run outputs are written here and gitignored
tests/                     Focused core implementation tests
```

`results/run_metrics_alignment_report.json` is a sanitized archival alignment
report retained for release documentation. It refers to historical generated
outputs, which are intentionally not distributed in this compact repository.
The manuscript-visible targets in that report have been checked against the
submitted PDF; supplemental historical fields not tabulated in the paper are
identified in the report's cross-check note.

## Installation

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

For local vLLM serving, install the optional dependencies:

```bash
pip install -e ".[vllm]"
```

## Environment Setup

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` only when using the GPT-4o backbone or GPT-4o judge.
For local vLLM models, set `VLLM_BASE_URL` if the server is not listening at
`http://localhost:8000/v1`. Do not commit `.env`.

## Data

The release includes the small SciSafetyBench inputs needed by the primary
runner:

- `data/scisafetybench/tasks_research.json`: 240 research tasks.
- `data/scisafetybench/tasks_tool.json`: 120 tool-risk tasks.
- `data/scisafetybench/tool_registry.json`: 30 tool definitions.
- `data/scisafetybench/tool_api_specs.json`: tool API specifications.

`data/example/smoke_tasks.json` contains benign illustrative task objects for
examining the pipeline input format; the primary runner reads SciSafetyBench.

## Smoke Test

This command executes one benchmark item locally with the deterministic
backbone and deterministic grading, without model downloads or API requests:

```bash
python scripts/run_single_config.py \
  --config configs/main/qwen25_72b_scitrace.yaml \
  --max_tasks 1 \
  --offline_deterministic \
  --skip_grading
```

Generated artifacts appear under `results/runs/qwen25_72b_scitrace/`.

## Primary Experiments

Each configuration under `configs/main/` combines one backbone
(`Llama-3.1-70B`, `Qwen2.5-72B`, `DeepSeek-V3`, or `GPT-4o`) with one method
(`bare`, `safescientist`, or `scitrace`).

Run one configuration:

```bash
python scripts/run_single_config.py --config configs/main/qwen25_72b_scitrace.yaml
```

For vLLM-backed configurations, start a compatible server first:

```bash
bash scripts/launch_vllm.sh qwen25_72b
```

Run the twelve primary configurations:

```bash
bash scripts/run_experiments.sh
```

These full runs require the configured model endpoints and GPT-4o judging
credentials where applicable.

## Reproducing Table 2 Metrics

After all twelve primary runs have produced per-task JSON outputs:

```bash
python scripts/evaluate_results.py --table2
```

This recomputes metrics from `results/runs/*/json/*.json` and writes
`results/generated/table2_recomputed.json`. To inspect a single run:

```bash
python scripts/evaluate_results.py \
  --input_dir results/runs/qwen25_72b_scitrace
```

The retained table files are reference snapshots, not substitutes for executing
the primary configurations.

## Expected Outputs

Each generated run directory contains:

```text
results/runs/<experiment_name>/
├── json/<task_id>.json
├── coverage.json
├── metrics.json
├── run_summary.json
└── run_<timestamp>.jsonl
```

Generated runs and console logs are excluded by `.gitignore`.

## Citation

Citation information will be added after anonymous review.

## Anonymity

This release is intended for anonymous review. It excludes author-identifying
metadata, personal paths, credentials, generated trace logs, bulky run output
directories, manuscript figures, and non-core experiment bundles. Only
placeholder credential values appear in `.env.example`.
