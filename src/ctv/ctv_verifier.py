"""Compositional Tool-Chain Verifier."""

from __future__ import annotations

from src.ctv.prompts import ctv_verification_prompt
from src.ctv.scoring import compute_ctv_score
from src.ctv.ts_flow import TSFlowFeedback
from src.sir.cumulative_risk_state import CumulativeRiskState
from src.utils.logger import get_logger
from src.utils.pydantic_schemas import CTVAssessment

logger = get_logger(__name__)


class CTVVerifier:
    """Trajectory-aware tool call verification before execution."""

    def __init__(
        self,
        backbone,
        cumulative_state: CumulativeRiskState,
        task_context: str = "",
        ctv_config: dict | None = None,
    ):
        self.backbone = backbone
        self.cumulative_state = cumulative_state
        self.task_context = task_context
        self.ts_flow = TSFlowFeedback(backbone)
        self.ctv_config = ctv_config or {}

    def verify(
        self,
        tool_name: str,
        tool_params: dict,
        call_history: list[dict],
    ) -> dict:
        """Verify a tool call and optionally generate TS-Flow feedback."""
        messages = ctv_verification_prompt.build_prompt(
            tool_name=tool_name,
            tool_params=tool_params,
            call_history=call_history,
            task_context=self.task_context,
            cumulative_context=self.cumulative_state.get_context_string(),
        )
        try:
            parsed = self.backbone.complete_json(messages, schema_class=CTVAssessment)
        except Exception as exc:
            logger.error("CTV parse failed: %s", exc)
            parsed = {
                "request_harmful": False,
                "compositional_risk": False,
                "tool_safety": "uncertain",
                "score": 0.1,
                "action": "allow",
            }

        threshold = float(self.ctv_config.get("block_threshold", 0.5))
        weights = self.ctv_config.get("weights")
        if threshold == 0.5 and weights is None:
            score, action = compute_ctv_score(
                parsed["request_harmful"],
                parsed["compositional_risk"],
                parsed["tool_safety"],
            )
        else:
            score, action = compute_ctv_score(
                parsed["request_harmful"],
                parsed["compositional_risk"],
                parsed["tool_safety"],
                threshold=threshold,
                weights=weights,
            )
        if abs(score - float(parsed.get("score", score))) > 0.05:
            logger.warning("CTV LLM score %.4f differs from computed %.4f", parsed.get("score"), score)
        parsed["score"] = score
        parsed["action"] = action

        self.cumulative_state.add_signal(
            {
                "stage": "ctv",
                "risk_level": "high_risk" if action == "block" else "warning" if action == "modify" else "safe",
                "categories": ["S9"] if parsed["compositional_risk"] else [],
                "justification": f"CTV {action} for {tool_name}",
                "action": action,
            }
        )

        verdict = dict(parsed)
        if action != "allow":
            blocked_call = {"tool_name": tool_name, "params": tool_params}
            verdict["ts_flow_feedback"] = self.ts_flow.generate(
                blocked_call, verdict, self.task_context
            )
        return verdict
