"""Load per-run calibration targets from experiment specs (configs, manifests, run bundles)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scitrace.experiment_paths import JSON_SUBDIR, RUN_SPEC_GROUP, iter_experiment_config_paths
from scitrace.results_paths import normalize_output_dir

METRIC_ALIASES: dict[str, str] = {
    "safety": "safety_score",
    "safety_score": "safety_score",
    "reject": "reject_rate",
    "reject_rate": "reject_rate",
    "rejection_rate": "reject_rate",
    "discussion_defense_rejection_rate": "reject_rate",
    "tool_safety": "tool_call_safety_rate",
    "tool_call_safety_rate": "tool_call_safety_rate",
    "quality": "quality",
    "clarity": "clarity",
    "overall": "overall",
    "compositional_detection_rate": "compositional_detection_rate",
    "compositional_detection": "compositional_detection_rate",
}

MODEL_LABEL_TO_KEY = {
    "Llama-3.1-70B": "llama31_70b",
    "Qwen2.5-72B": "qwen25_72b",
    "DeepSeek-V3": "deepseekv3",
    "GPT-4o": "gpt4o",
}


def normalize_metric_fields(raw: dict[str, Any]) -> dict[str, float]:
    """Map experiment-spec field names to metrics.json keys."""
    out: dict[str, float] = {}
    for key, value in raw.items():
        if key in ("table", "source", "config_path", "manifest_path"):
            continue
        if not isinstance(value, (int, float)):
            continue
        canonical = METRIC_ALIASES.get(key)
        if canonical:
            out[canonical] = float(value)
    return out


def output_dir_to_run_key(output_dir: str | Path) -> str:
    """``data/results/runs/<run_key>/`` → ``<run_key>`` (posix, no trailing slash)."""
    normalized = normalize_output_dir(Path(output_dir))
    parts = normalized.parts
    if len(parts) >= 4 and parts[0] == "data" and parts[1] == "results" and parts[2] == "runs":
        rel = parts[3:]
        if rel and rel[-1] == "":
            rel = rel[:-1]
        return "/".join(rel).rstrip("/")
    text = str(output_dir).replace("\\", "/").strip("/")
    if "data/results/runs/" in text:
        return text.split("data/results/runs/", 1)[-1].rstrip("/")
    return text.rstrip("/")


def _merge_targets(
    base: dict[str, dict[str, float]],
    run_key: str,
    fields: dict[str, float],
) -> None:
    if not fields:
        return
    base.setdefault(run_key, {}).update(fields)


def _ingest_config_dict(
    targets: dict[str, dict[str, float]],
    cfg: dict[str, Any],
    *,
    config_path: Path | None = None,
) -> None:
    if "output_dir" in cfg:
        run_key = output_dir_to_run_key(cfg["output_dir"])
        if "expected_metrics" in cfg and isinstance(cfg["expected_metrics"], dict):
            _merge_targets(targets, run_key, normalize_metric_fields(cfg["expected_metrics"]))
        if "expected_targets" in cfg and isinstance(cfg["expected_targets"], dict):
            _merge_targets(targets, run_key, normalize_metric_fields(cfg["expected_targets"]))

    for setup in cfg.get("setups") or []:
        if not isinstance(setup, dict):
            continue
        setup_name = setup.get("name")
        parent_out = cfg.get("output_dir")
        if setup_name and parent_out:
            parent_key = output_dir_to_run_key(parent_out)
            run_key = f"{parent_key}/{setup_name}"
        elif "output_dir" in setup:
            run_key = output_dir_to_run_key(setup["output_dir"])
        else:
            continue
        if "expected_metrics" in setup and isinstance(setup["expected_metrics"], dict):
            _merge_targets(targets, run_key, normalize_metric_fields(setup["expected_metrics"]))

    for member in cfg.get("configs") or []:
        if isinstance(member, dict):
            _ingest_config_dict(targets, member, config_path=config_path)

    for run_cfg in cfg.get("run_configs") or []:
        if isinstance(run_cfg, dict):
            _ingest_config_dict(targets, run_cfg, config_path=config_path)

    if "expected_results" in cfg and isinstance(cfg["expected_results"], dict):
        _ingest_expected_results(targets, cfg)



def _ingest_expected_results(targets: dict[str, dict[str, float]], cfg: dict[str, Any]) -> None:
    """Adversarial (model×method) or discussion_attacker (method-only) expected_results."""
    base_out = cfg.get("output_dir")
    if not base_out:
        return
    base_key = output_dir_to_run_key(base_out)
    expected = cfg["expected_results"]
    if not isinstance(expected, dict):
        return

    first_val = next(iter(expected.values()), None)
    if isinstance(first_val, dict):
        for model_label, methods in expected.items():
            model_key = MODEL_LABEL_TO_KEY.get(model_label, model_label)
            if not isinstance(methods, dict):
                continue
            for method, rate in methods.items():
                if isinstance(rate, (int, float)):
                    run_key = f"{base_key}/{model_key}_{method}"
                    _merge_targets(targets, run_key, {"reject_rate": float(rate)})
    else:
        for method, rate in expected.items():
            if isinstance(rate, (int, float)):
                run_key = f"{base_key}/{method}"
                _merge_targets(targets, run_key, {"reject_rate": float(rate)})


def _load_json_targets(path: Path) -> dict[str, dict[str, float]]:
    targets: dict[str, dict[str, float]] = {}
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return targets
    if not isinstance(cfg, dict):
        return targets
    _ingest_config_dict(targets, cfg, config_path=path)
    if "expected_targets" in cfg and isinstance(cfg["expected_targets"], dict):
        run_key = cfg.get("run_key")
        if not run_key and "output_dir" in cfg:
            run_key = output_dir_to_run_key(cfg["output_dir"])
        if run_key:
            _merge_targets(targets, str(run_key).replace("\\", "/"), normalize_metric_fields(cfg["expected_targets"]))
    return targets


def iter_manifest_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for sub in (
        root / "experiments" / RUN_SPEC_GROUP / JSON_SUBDIR / "manifests",
        root / "experiments" / "ablations" / JSON_SUBDIR / "manifests",
    ):
        if sub.is_dir():
            paths.extend(sorted(sub.glob("*.json")))
    return paths


def iter_nested_ablation_run_configs(root: Path) -> list[Path]:
    runs_json = root / "experiments" / "ablations" / "runs" / JSON_SUBDIR
    if not runs_json.is_dir():
        return []
    return sorted(runs_json.rglob("*.json"))


def experiment_run_targets(root: Path) -> dict[str, dict[str, float]]:
    """Targets declared in experiment JSON under ``experiments/`` (not table exports)."""
    merged: dict[str, dict[str, float]] = {}

    for path in iter_experiment_config_paths(root):
        for run_key, fields in _load_json_targets(path).items():
            if run_key.startswith("_"):
                continue
            _merge_targets(merged, run_key, fields)

    for path in iter_nested_ablation_run_configs(root):
        for run_key, fields in _load_json_targets(path).items():
            if run_key.startswith("_"):
                continue
            _merge_targets(merged, run_key, fields)

    for path in iter_manifest_paths(root):
        for run_key, fields in _load_json_targets(path).items():
            if run_key.startswith("_"):
                continue
            _merge_targets(merged, run_key, fields)

    adversarial_dir = root / "experiments" / "adversarial" / JSON_SUBDIR
    discussion_dir = root / "experiments" / "discussion_attacker" / JSON_SUBDIR
    for group_dir in (adversarial_dir, discussion_dir):
        if group_dir.is_dir():
            for path in sorted(group_dir.glob("*.json")):
                for run_key, fields in _load_json_targets(path).items():
                    if run_key.startswith("_"):
                        continue
                    _merge_targets(merged, run_key, fields)

    return merged


def target_source_for_run(
    root: Path,
    run_key: str,
    *,
    experiment_targets: dict[str, dict[str, float]] | None = None,
) -> str:
    """Human-readable label for where targets for *run_key* primarily come from."""
    if experiment_targets is None:
        experiment_targets = experiment_run_targets(root)
    if run_key in experiment_targets and experiment_targets[run_key]:
        fields = experiment_targets[run_key]
        cfg = fields.get("_config_path", "")
        if cfg:
            return f"experiment config: {Path(cfg).name}"
        return "experiment config/manifest"
    if run_key.startswith("adversarial/"):
        return "table fallback (Table 7)"
    if run_key.startswith("discussion_attacker/"):
        return "table fallback (Table 6)"
    if run_key.startswith("ablations/"):
        return "table fallback (ablation table)"
    return "table fallback (Table 2/4/12/13/15)"
