"""SciSafetyBench task loader."""

from __future__ import annotations

import json
from pathlib import Path

from scitrace.benchmark.paths import RESEARCH_TASKS_PATH, TOOL_TASKS_PATH


class SciSafetyBenchLoader:
    """Loads SciSafetyBench tasks (240 research + 120 tool)."""

    def __init__(
        self,
        research_path: str | Path | None = None,
        tool_path: str | Path | None = None,
    ) -> None:
        self.research_path = Path(research_path or RESEARCH_TASKS_PATH)
        self.tool_path = Path(tool_path or TOOL_TASKS_PATH)

    def _load(self, path: Path) -> list[dict]:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def load_research_tasks(self, domain: str | None = None, risk_type: str | None = None) -> list[dict]:
        tasks = self._load(self.research_path)
        if domain:
            tasks = [t for t in tasks if t.get("domain") == domain]
        if risk_type:
            tasks = [t for t in tasks if t.get("risk_type") == risk_type]
        return tasks

    def load_tool_tasks(self, domain: str | None = None) -> list[dict]:
        tasks = self._load(self.tool_path)
        if domain:
            tasks = [t for t in tasks if t.get("domain") == domain]
        return tasks

    def load_all(self) -> dict[str, list[dict]]:
        return {
            "research": self.load_research_tasks(),
            "tool": self.load_tool_tasks(),
        }
