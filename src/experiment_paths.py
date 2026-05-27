"""Paths for runnable YAML experiment configurations."""

from __future__ import annotations

from pathlib import Path

CONFIG_ROOT = Path("configs")
MAIN_CONFIG_DIR = CONFIG_ROOT / "main"


def resolve_config_path(config_path: Path, *, root: Path | None = None) -> Path:
    """Resolve an explicit config path or a YAML filename from ``configs/main``."""
    root = root or Path.cwd()
    candidate = config_path if config_path.is_absolute() else root / config_path
    if candidate.is_file():
        return candidate.resolve()
    if len(config_path.parts) == 1:
        main_candidate = root / MAIN_CONFIG_DIR / config_path.name
        if main_candidate.is_file():
            return main_candidate.resolve()
    raise FileNotFoundError(f"Config not found: {config_path}")


def iter_main_config_paths(root: Path) -> list[Path]:
    """Return the primary experiment configurations in stable order."""
    return sorted((root / MAIN_CONFIG_DIR).glob("*.yaml"))
