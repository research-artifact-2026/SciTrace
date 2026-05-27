"""Backbone factory."""

from __future__ import annotations

from dotenv import load_dotenv

from scitrace.backbone.base_backbone import BaseBackbone
from scitrace.backbone.deterministic_backbone import DeterministicBackbone
from scitrace.backbone.openai_backbone import OpenAIBackbone
from scitrace.backbone.vllm_backbone import VLLMBackbone
from scitrace.config.api_defaults import merge_backbone_config

load_dotenv()


def _apply_completion_defaults(backbone: BaseBackbone, config: dict) -> BaseBackbone:
    merged = merge_backbone_config(config)
    backbone.default_temperature = float(merged["temperature"])
    backbone.default_max_tokens = int(merged["max_tokens"])
    backbone.default_top_p = merged.get("top_p")
    backbone.default_top_k = merged.get("top_k")
    backbone.default_repetition_penalty = merged.get("repetition_penalty")
    backbone.default_presence_penalty = merged.get("presence_penalty")
    backbone.default_frequency_penalty = merged.get("frequency_penalty")
    return backbone


def create_backbone(config: dict) -> BaseBackbone:
    """Create backbone from experiment config."""
    merged = merge_backbone_config(config)
    backbone_type = merged.get("backbone_type")
    if not backbone_type:
        raise ValueError("backbone.backbone_type is required (openai, vllm, or deterministic)")
    if backbone_type == "openai":
        backbone = OpenAIBackbone(model_name=merged.get("model_name", "gpt-4o"))
    elif backbone_type == "vllm":
        backbone = VLLMBackbone(
            model_name=merged["model_name"],
            base_url=merged.get("base_url"),
            tensor_parallel_size=merged.get("tensor_parallel_size", 2),
            quantization=merged.get("quantization", "awq"),
            dtype=merged.get("dtype", "auto"),
        )
    elif backbone_type == "deterministic":
        backbone = DeterministicBackbone()
    else:
        raise ValueError(
            f"Unknown backbone_type: {backbone_type}. Use 'openai', 'vllm', or 'deterministic'."
        )
    return _apply_completion_defaults(backbone, merged)
