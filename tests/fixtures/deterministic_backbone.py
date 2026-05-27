"""Deterministic LLM stand-in for unit tests only (not used in experiment runs)."""

from __future__ import annotations

import json
from typing import Any

from src.backbone.base_backbone import BaseBackbone


class DeterministicBackbone(BaseBackbone):
    """Returns schema-valid JSON from message content hints."""

    def __init__(self, default_response: dict[str, Any] | None = None) -> None:
        self.default_response = default_response or {
            "risk_level": "safe",
            "categories": [],
            "justification": "Deterministic test assessment.",
            "action": "proceed",
        }

    def complete(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        joined = " ".join(str(m.get("content", "")) for m in messages).lower()
        system = " ".join(
            str(m.get("content", "")) for m in messages if m.get("role") == "system"
        ).lower()
        if "sir module" in joined or "safety-intrinsic reasoning" in joined:
            payload = dict(self.default_response)
            if "reviewer stage" in joined:
                payload = {
                    **payload,
                    "interaction_escalation": False,
                    "escalation_pairs": None,
                }
        elif "compositional tool-chain verifier" in joined or "three-dimension" in joined:
            payload = {
                "request_harmful": False,
                "compositional_risk": False,
                "tool_safety": "safe",
                "score": 0.0,
                "action": "allow",
            }
        elif "ts-flow" in joined or "ts_flow" in joined:
            payload = {
                "explanation": "TS-Flow corrective explanation.",
                "safe_alternative": "Use a benign educational analogue.",
                "modified_call": json.dumps(
                    {"tool_name": "genome_search", "params": {"organism": "educational_model"}}
                ),
            }
        elif "quality judge" in system:
            payload = {
                "quality": 3.5,
                "clarity": 3.6,
                "overall": 3.7,
                "justification": "Deterministic quality judge.",
            }
        elif "safety judge" in system:
            payload = {"score": 4.5, "justification": "Deterministic safety judge."}
        else:
            payload = dict(self.default_response)
        return json.dumps(payload)
