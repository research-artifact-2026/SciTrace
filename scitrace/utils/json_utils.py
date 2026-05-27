"""JSON load/save helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    """Load JSON from a file path."""
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: str | Path, data: Any, indent: int = 2) -> None:
    """Save data as JSON, creating parent directories if needed."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=indent)


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from LLM output."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def parse_json_response(text: str) -> dict:
    """Parse JSON from raw LLM text."""
    return json.loads(strip_markdown_fences(text))
