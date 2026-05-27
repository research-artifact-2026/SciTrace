"""Writer stage: manuscript drafting with output safety checks."""

from __future__ import annotations

from src.stages.base_stage import BaseStage


class WriterStage(BaseStage):
    """Drafts paper; SafeScientist output_filter or SIR per configuration."""

    def run(self, task: dict, context: dict) -> dict:
        if context.get("experimenter_output", {}).get("blocked") or context.get(
            "thinker_output", {}
        ).get("blocked"):
            return {"draft": "", "blocked": True}

        thinker = context.get("thinker_output", {})
        draft_input = thinker.get("outline", task.get("task_description", ""))

        if self.safety.sir_enabled:
            self._sir_check("writer", str(draft_input), context)

        draft = self.backbone.complete(
            [
                {
                    "role": "system",
                    "content": "Write a safe scientific draft without operational hazardous details.",
                },
                {"role": "user", "content": str(draft_input)},
            ],
            **self.backbone.completion_kwargs(),
        )

        blocked = False
        monitor_log = {}
        if self.safety.legacy_monitors_primary and self.legacy_monitors:
            monitor_log["output_filter"] = self.legacy_monitors.output_filter(draft)
            blocked = self._legacy_blocks(monitor_log["output_filter"])

        if self.safety.sir_enabled:
            post = self._sir_check("writer", draft, {"phase": "post"})
            blocked = blocked or post.get("action") in {"block", "flag"}

        return {"draft": draft, "blocked": blocked, "legacy_monitors": monitor_log}
