"""Canonical SciSafetyBench data paths."""

from __future__ import annotations

import os
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SCISAFETYBENCH_DIR = Path(
    os.getenv("SCITRACE_BENCHMARK_ROOT", _PACKAGE_ROOT / "data" / "scisafetybench")
)

RESEARCH_TASKS_PATH = Path(
    os.getenv("SCISAFETYBENCH_RESEARCH_TASKS", SCISAFETYBENCH_DIR / "tasks_research.json")
)
TOOL_TASKS_PATH = Path(
    os.getenv("SCISAFETYBENCH_TOOL_TASKS", SCISAFETYBENCH_DIR / "tasks_tool.json")
)
TOOL_REGISTRY_PATH = Path(
    os.getenv("SCISAFETYBENCH_TOOL_REGISTRY", SCISAFETYBENCH_DIR / "tool_registry.json")
)
TOOL_API_SPECS_PATH = Path(
    os.getenv("SCISAFETYBENCH_TOOL_API_SPECS", SCISAFETYBENCH_DIR / "tool_api_specs.json")
)
