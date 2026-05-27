"""Safety-Intrinsic Reasoning Loop (SIR) core module."""

from __future__ import annotations

from src.sir.cumulative_risk_state import CumulativeRiskState
from src.sir.prompts import experimenter_prompt, reviewer_prompt, thinker_prompt, writer_prompt
from src.sir.safety_memory import SafetyMemory
from src.utils.logger import get_logger
from src.utils.pydantic_schemas import SIRAssessment, SIRReviewerAssessment

logger = get_logger(__name__)

_STAGE_BUILDERS = {
    "thinker": thinker_prompt.build_prompt,
    "experimenter": experimenter_prompt.build_prompt,
    "writer": writer_prompt.build_prompt,
    "reviewer": reviewer_prompt.build_prompt,
}


class SIRModule:
    """Joint task-and-safety reasoning at each pipeline stage."""

    def __init__(
        self,
        backbone,
        safety_memory: SafetyMemory | None = None,
        k_checks: int = 3,
        enabled: bool = True,
    ):
        self.backbone = backbone
        self.safety_memory = safety_memory or SafetyMemory()
        self.k_checks = k_checks
        self.enabled = enabled

    def assess(
        self,
        stage: str,
        task_content: str,
        cumulative_state: CumulativeRiskState,
        extra_context: dict | None = None,
    ) -> dict:
        """Run SIR assessment and update cumulative_state in-place."""
        if not self.enabled:
            return {
                "risk_level": "safe",
                "categories": [],
                "justification": "SIR disabled for this configuration.",
                "action": "proceed",
            }

        builder = _STAGE_BUILDERS.get(stage)
        if builder is None:
            raise ValueError(f"Unknown SIR stage: {stage}")

        query = task_content
        if extra_context:
            query += " " + str(extra_context)

        retrieved = self.safety_memory.retrieve(query, k=self.k_checks)
        messages = builder(task_content, cumulative_state, retrieved)

        schema = SIRReviewerAssessment if stage == "reviewer" else SIRAssessment
        try:
            parsed = self.backbone.complete_json(messages, schema_class=schema)
        except Exception as exc:
            logger.error("SIR parse failed at %s: %s", stage, exc)
            parsed = {
                "risk_level": "warning",
                "categories": [],
                "justification": "Parse failure; defaulting to warning.",
                "action": "flag",
            }
            if stage == "reviewer":
                parsed["interaction_escalation"] = False

        signal = {
            "stage": stage,
            "risk_level": parsed["risk_level"],
            "categories": parsed.get("categories", []),
            "justification": parsed.get("justification", ""),
            "action": parsed.get("action", "flag"),
        }
        cumulative_state.add_signal(signal)
        return parsed
