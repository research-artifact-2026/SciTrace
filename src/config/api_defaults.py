"""Manuscript-aligned API defaults (SafeScientist / Figure 17)."""

from __future__ import annotations

from typing import Any

# Greedy decoding for all experiment backbones (SafeScientist).
BACKBONE_DEFAULTS: dict[str, Any] = {
    "temperature": 0.0,
    "max_tokens": 4096,
    "top_p": 1.0,
    "top_k": None,
    "repetition_penalty": None,
    "presence_penalty": None,
    "frequency_penalty": None,
}

# GPT-4o judge (Figure 17).
JUDGE_DEFAULTS: dict[str, Any] = {
    "model": "gpt-4o",
    "temperature": 0.0,
    "max_tokens": 4096,
}

# Per-tool API limits when not set in tool_registry.json.
TOOL_API_DEFAULTS: dict[str, Any] = {
    "max_output_tokens": 1024,
    "timeout": 60,
}


def merge_backbone_config(config: dict | None) -> dict[str, Any]:
    merged = dict(BACKBONE_DEFAULTS)
    if config:
        merged.update(config)
    return merged


def merge_judge_config(config: dict | None) -> dict[str, Any]:
    merged = dict(JUDGE_DEFAULTS)
    if config:
        merged.update(config)
    return merged
