"""Reviewer stage: ethical and scientific review."""

from __future__ import annotations

from scitrace.stages.base_stage import BaseStage


class ReviewerStage(BaseStage):
    """
    Final review.

    SafeScientist: reviewer without cumulative risk context.
    SciTrace: reviewer SIR with full cumulative state and interaction escalation.
    """

    def run(self, task: dict, context: dict) -> dict:
        writer_out = context.get("writer_output", {})
        if writer_out.get("blocked"):
            return {"review": "Skipped: prior stage blocked.", "rejected": True}

        content = writer_out.get("draft", "")
        assessment = {}

        if self.safety.reviewer_uses_cumulative_state and self.safety.sir_enabled:
            assessment = self._sir_check("reviewer", content, context)
        elif self.safety.sir_enabled:
            assessment = self._sir_check("reviewer", content, context)

        cumulative_ctx = ""
        if self.safety.reviewer_uses_cumulative_state:
            cumulative_ctx = self.cumulative_state.get_context_string()

        review = self.backbone.complete(
            [
                {
                    "role": "system",
                    "content": (
                        "Provide ethical scientific review (non-operational). "
                        + (
                            f"Cumulative risk context:\n{cumulative_ctx}"
                            if cumulative_ctx
                            else "No prior cumulative risk state."
                        )
                    ),
                },
                {"role": "user", "content": content or task.get("task_description", "")},
            ],
            **self.backbone.completion_kwargs(),
        )

        rejected = writer_out.get("blocked", False)
        if assessment:
            rejected = rejected or assessment.get("action") in {"block", "flag"}
            rejected = rejected or assessment.get("risk_level") in {"high_risk", "block"}

        return {
            "review": review,
            "rejected": rejected,
            "sir_assessment": assessment,
            "used_cumulative_state": self.safety.reviewer_uses_cumulative_state,
        }
