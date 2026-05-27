"""Paths for experiment config YAML/JSON under ``experiments/``."""

from __future__ import annotations

from pathlib import Path

JSON_SUBDIR = "json"

# Category folder names under experiments/ that hold runnable configs.
CONFIG_GROUPS = frozenset({"configs", "ablations", "adversarial", "discussion_attacker"})

# Multi-replicate benchmark run bundles (Table 2 / CI); outputs under data/results/runs/.
RUN_SPEC_GROUP = "runs"

# Top-level experiments/*.json files that are catalogues, not runnable configs.
_NON_CONFIG_JSON_NAMES = frozenset(
    {"index.json", "defaults.json", "index_benchmark_outputs.json"}
)


def json_config_dir(group_dir: Path) -> Path:
    """Directory holding JSON mirrors for a config group (e.g. ``experiments/configs/json``)."""
    return group_dir / JSON_SUBDIR


def json_path_for_yaml(yaml_path: Path) -> Path:
    """Paired JSON path for a YAML config in ``<group>/*.yaml`` → ``<group>/json/*.json``."""
    return json_config_dir(yaml_path.parent) / f"{yaml_path.stem}.json"


def resolve_config_path(config_path: Path, *, root: Path | None = None) -> Path:
    """Resolve a config path, including legacy locations before the ``json/`` subfolder move."""
    root = root or Path.cwd()
    candidate = config_path if config_path.is_absolute() else root / config_path
    if candidate.is_file():
        return candidate.resolve()

    parts = candidate.parts
    for group in (*CONFIG_GROUPS, RUN_SPEC_GROUP):
        if group not in parts:
            continue
        idx = parts.index(group)
        rel_after = parts[idx + 1 :]
        if not rel_after or rel_after[0] == JSON_SUBDIR:
            break
        legacy = root / Path(*parts[: idx + 1]) / JSON_SUBDIR / Path(*rel_after)
        if legacy.is_file():
            return legacy.resolve()
        break

    raise FileNotFoundError(f"Config not found: {config_path}")


def iter_group_json_configs(group_dir: Path) -> list[Path]:
    """All ``*.json`` runnable configs for a group (``group_dir/json/*.json``)."""
    json_dir = json_config_dir(group_dir)
    if not json_dir.is_dir():
        return []
    return sorted(json_dir.glob("*.json"))


def iter_run_spec_paths(root: Path) -> list[Path]:
    """Discover multi-replicate run bundles under ``experiments/runs/``."""
    runs_dir = root / "experiments" / RUN_SPEC_GROUP
    if not runs_dir.is_dir():
        return []
    paths = list(iter_group_json_configs(runs_dir))
    paths.extend(sorted(runs_dir.glob("*.yaml")))
    paths.extend(sorted(runs_dir.glob("*.yml")))
    return paths


def iter_experiment_config_paths(root: Path) -> list[Path]:
    """Discover runnable experiment config files (JSON + YAML), excluding catalogue JSON."""
    paths: list[Path] = []
    experiments = root / "experiments"
    for group in CONFIG_GROUPS:
        group_dir = experiments / group
        if not group_dir.is_dir():
            continue
        paths.extend(iter_group_json_configs(group_dir))
        paths.extend(sorted(group_dir.glob("*.yaml")))
        paths.extend(sorted(group_dir.glob("*.yml")))
    paths.extend(iter_run_spec_paths(root))
    return paths


def is_runnable_config_json(path: Path) -> bool:
    if path.suffix.lower() != ".json":
        return False
    if path.name in _NON_CONFIG_JSON_NAMES:
        return False
    parts = path.parts
    return any(g in parts and JSON_SUBDIR in parts for g in CONFIG_GROUPS)
