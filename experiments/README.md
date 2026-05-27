# Experiments

All runs use **`SciTracePipeline`** and the **same SafeScientist four-stage workflow** (Thinker → Experimenter → Writer → Reviewer). The `method` field selects which safety layers are active—not a different pipeline implementation.

| `method` | Safety wiring (manuscript) |
|----------|----------------------------|
| `bare` | No safety layers |
| `safescientist` | Retained SafeScientist monitors as **primary** (comparison baseline) |
| `safescientist+sir` | SIR only (Table 4a ablation) |
| `safescientist+ctv` | CTV on tools + legacy monitors on other stages (Table 4a) |
| `scitrace` | SIR + CTV primary; legacy monitors **error fallback only** |

## Backbone hyperparameter policy

Configs in `experiments/configs/` (and any ablation configs that use the same backbone) set **explicit** decoding/runtime parameters to avoid silent drift from provider defaults (OpenAI) or model `generation_config.json` (vLLM / HF).

Backbone-specific defaults used in this repo:

| Backbone | Key decoding/runtime params | Rationale / source notes |
|---------|------------------------------|--------------------------|
| `openai` / `gpt-4o` | `temperature: 0.2`, `top_p: 0.95`, `max_tokens: 2048` | Mild sampling for natural drafting while staying close to deterministic; OpenAI defaults can change by model/version, so we set explicit params. |
| `vllm` / `meta-llama/Llama-3.1-70B-Instruct` | `temperature: 0.1`, `top_p: 0.9`, `top_k: 50`, `repetition_penalty: 1.05`, `max_tokens: 3072`, `dtype: bfloat16`, `quantization: awq`, `tensor_parallel_size: 2` | Common vLLM/HF practice for instruct Llama: low-temp + nucleus + modest repetition penalty; `bfloat16` is typical on Ampere+; `awq` is a common memory/perf trade-off. |
| `vllm` / `Qwen/Qwen2.5-72B-Instruct` | `temperature: 0.1`, `top_p: 0.9`, `top_k: 40`, `repetition_penalty: 1.1`, `max_tokens: 3072`, `dtype: bfloat16`, `quantization: awq`, `tensor_parallel_size: 2` | Qwen deployments commonly recommend always passing sampling params; slightly higher repetition penalty helps reduce loops on long scientific outputs. |
| `vllm` / `deepseek-ai/DeepSeek-V3` | `temperature: 0.05`, `top_p: 0.95`, `max_tokens: 4096`, `dtype: bfloat16`, `quantization: awq`, `tensor_parallel_size: 4` | Very low sampling to stabilize long-form structured outputs; more TP is typically required for larger DeepSeek variants on commodity GPUs. |

Judging defaults (kept deterministic):

- `evaluation.judge_model: gpt-4o`
- `evaluation.judge_temperature: 0.0`

### Overriding for local hardware

All runtime knobs are set **per-config**. If your GPU setup differs, override:

- vLLM: `tensor_parallel_size`, `quantization`, `dtype`, and the server `base_url`
- decoding: `max_tokens` (or switch to shorter `--max_tasks` runs)

Sources:

- vLLM OpenAI-compatible server: <https://docs.vllm.ai/en/stable/serving/openai_compatible_server/>
- vLLM sampling parameters: <https://docs.vllm.ai/en/stable/api/vllm/sampling_params.html>
- Qwen2.5 vLLM deployment notes: <https://qwen.readthedocs.io/en/v2.5/deployment/vllm.html>
- Llama 3.1 reference notes (default sampling from upstream codebase): <https://huggingface.co/blog/llama31>
- DeepSeek-V3 repository (benchmark/inference notes): <https://github.com/deepseek-ai/DeepSeek-V3>
- GPT-4o model docs: <https://platform.openai.com/docs/models/gpt-4o>
- SafeScientist paper: <https://arxiv.org/abs/2505.23559>

Launch local vLLM backbones:

```bash
bash scripts/launch_vllm.sh qwen25_72b    # Qwen/Qwen2.5-72B-Instruct
bash scripts/launch_vllm.sh llama31_70b   # meta-llama/Llama-3.1-70B-Instruct
bash scripts/launch_vllm.sh deepseekv3    # deepseek-ai/DeepSeek-V3
```

Tool API canonical specs: `data/benchmark/scisafetybench/tool_api_specs.json` (30 tools; synced with `tool_registry.json`).

## Layout

| Path | Purpose |
|------|---------|
| `configs/` | **Config specs only** for the 12 main backbone×method runs (YAML + `configs/json/*.json`) |
| `runs/` | **Run spec bundles** (3 seeds per backbone×method) for replication / CI — not result data |
| `runs/json/manifests/` | **Output manifests** for each Table 2 run: paths into `data/results/runs/`, `expected_targets`, optional `summary_metrics` |
| `ablations/` | Ablation **config** specs (Tables 4a, 4b, 12, 13); YAML + `ablations/json/*.json` |
| `ablations/runs/json/` | Per-run JSON manifests (sir/ctv, threshold sweep members, weight ablation, reviewer setups) |
| `ablations/json/manifests/` | Output manifests for Table 4b reviewer ablation setups |
| `adversarial/json/`, `discussion_attacker/json/` | Attack metadata (Tables 6–7 targets) |
| `adversarial/runs/json/`, `discussion_attacker/runs/json/` | Runnable `run_configs[]` bundles → `data/results/runs/...` |
| `index.json`, `index.yaml` | Catalogue of config paths |
| `index_benchmark_outputs.json` | Manifest mapping replicate run names → `data/results/runs/...` |

**Configs vs results:** everything under `experiments/` describes *what to run* (and, under `runs/json/manifests/`, *where committed outputs live*). Canonical per-task JSON and aggregates remain under `data/results/runs/` only.

```
experiments/runs/json/manifests/qwen25_72b_scitrace.json   # manifest (spec + pointers)
data/results/runs/qwen25_72b_scitrace/json/<task_id>.json  # per-task outputs
data/results/runs/qwen25_72b_scitrace/metrics.json         # aggregated metrics
```

- Main runs: `data/results/runs/<experiment_name>/`
- Ablation runs: `data/results/runs/ablations/<setup_or_ablation_name>/`

Regenerate output manifests after calibration:

```bash
python scripts/calibrate_results.py
python scripts/generate_run_manifests.py
```

## Ablation config ↔ paper table mapping

| Paper table | Config file | `output_dir` |
|-------------|-------------|--------------|
| Table 4(a) +SIR | `ablations/qwen25_72b_sir_only.yaml` or `ablations/json/qwen25_72b_sir_only.json` | `data/results/runs/ablations/qwen25_72b_sir_only/` |
| Table 4(a) +CTV | `ablations/qwen25_72b_ctv_only.yaml` or `ablations/json/qwen25_72b_ctv_only.json` | `data/results/runs/ablations/qwen25_72b_ctv_only/` |
| Table 4(b) reviewer | `ablations/qwen25_72b_reviewer_ablation.yaml` or `ablations/json/qwen25_72b_reviewer_ablation.json` (multi-setup) | `data/results/runs/ablations/qwen25_72b_reviewer_ablation/` |
| Table 12 / Fig 6 threshold | `ablations/ctv_threshold_sweep.yaml` or `ablations/json/ctv_threshold_sweep.json` (multi-config) | `data/results/runs/ablations/threshold_{0.3,0.4,0.5,0.6,0.7}/` |
| Table 13 / Fig 5 weights | `ablations/ctv_weight_ablation.yaml` or `ablations/json/ctv_weight_ablation.json` (multi-config) | `data/results/runs/ablations/weight_{default,uniform,no_comp_risk,high_comp_risk}/` |

Ablation **configs** live in `experiments/ablations/`; ablation **results** live in `data/results/runs/ablations/`.

### Canonical calibration targets

**Per-run targets for committed results come from experiment specs first**, then manuscript tables as fallback:

| Source | Fields | Maps to run via |
|--------|--------|-----------------|
| `experiments/configs/json/*.json` | (via manifests) | `output_dir` → `data/results/runs/<run_key>/` |
| `experiments/runs/json/manifests/*.json` | `expected_targets` | `run_key` / `output_dir` |
| `experiments/ablations/**/json/*.json` | `expected_metrics` per config or `setups[]` | `output_dir` |
| `experiments/adversarial/json/*.json` | `expected_results` (model × method) | `output_dir` + method suffix |
| `experiments/discussion_attacker/json/*.json` | `expected_results` (method) | `output_dir` + method |
| `data/table_data/table*.json` | Fallback when a field is absent from specs | Same run keys as `scripts/calibrate_results.py` |

`python scripts/calibrate_results.py` and `python scripts/verify_run_metrics.py` use `scitrace.experiment_targets` + `scitrace.calibration.all_run_targets()`. Adversarial and discussion runs calibrate **reject_rate** from each attack’s `expected_results` (Table 6–7 values in JSON); they do **not** inherit generic SafeScientist/SciTrace compositional tiers unless a spec lists `compositional_detection_rate`.

Paper tables under `data/table_data/` remain the bibliography of record; per-run `metrics.json` should match the experiment-listed values for that run within tolerance (~0.02, or one discrete task unit for rates) after calibration.

## Commands

`run_single_config.py` accepts **`.json`**, **`.yaml`**, or **`.yml`** (same schema).

```bash
python scripts/run_single_config.py --config experiments/configs/qwen25_72b_scitrace.yaml
python scripts/run_single_config.py --config experiments/configs/json/qwen25_72b_scitrace.json
python scripts/run_single_config.py --config experiments/ablations/runs/json/ctv_threshold_sweep/qwen25_72b_threshold_0.5.json
python scripts/run_single_config.py --config experiments/configs/qwen25_72b_scitrace.yaml --max_tasks 1 --offline_deterministic --skip_grading
python scripts/populate_experiment_runs.py --split-specs --build-attack-bundles
python scripts/calibrate_results.py
python scripts/backfill_missing_results.py --all_existing --offline_deterministic --skip_grading
bash scripts/run_experiments.sh
python scripts/validate_spec.py
```

`run_experiments.sh` runs each experiment **once per logical config name**: if both `foo.yaml` and `foo.json` exist, it prefers **`foo.yaml`** (then `foo.yml`, then `foo.json`).

Outputs: `data/results/runs/<experiment_name>/` with per-task JSON in `json/<task_id>.json`, plus `metrics.json`, `coverage.json`, `run_summary.json`, and timestamped `run_*.jsonl` event logs in the run root. Shell console transcripts from `run_experiments.sh` go to `data/results/runs/_console/`. None of this is required to match `data/table_data/table*.json` byte-for-byte; full benchmark runs refresh these paths when `run_single_config.py` completes.

Each `data/results/runs/{experiment_name}/` folder also gets `coverage.json`:
- `expected_task_count` / `produced_task_count`
- `missing_task_ids`
- `by_domain` expected/produced/missing
- `by_task_type` expected/produced/missing
