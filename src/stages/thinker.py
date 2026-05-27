"""Thinker stage: ideation and discussion (SafeScientist workflow + SIR)."""

from __future__ import annotations

from src.stages.base_stage import BaseStage


class ThinkerStage(BaseStage):
    """Generates research outline; SafeScientist prompt/discussion monitors when configured."""

    def run(self, task: dict, context: dict) -> dict:
        desc = task.get("task_description", "")
        blocked = False
        monitor_log = {}

        if self.safety.legacy_monitors_primary and self.legacy_monitors:
            monitor_log["prompt_monitor"] = self.legacy_monitors.prompt_monitor(desc)
            blocked = self._legacy_blocks(monitor_log["prompt_monitor"])

        if self.safety.sir_enabled and not blocked:
            self._sir_check("thinker", desc, context)

        outline = ""
        if not blocked:
            outline = self.backbone.complete(
                [
                    {
                        "role": "system",
                        "content": "Draft a high-level scientific research outline (safe, non-operational).",
                    },
                    {"role": "user", "content": desc},
                ],
                **self.backbone.completion_kwargs(),
            )
            if self.safety.sir_enabled:
                post = self._sir_check("thinker", outline, {"phase": "post"})
                blocked = blocked or post.get("action") in {"block", "flag"}

        discussion = [{"role": "user", "content": desc}]
        if self.safety.legacy_monitors_primary and self.legacy_monitors:
            monitor_log["discussion_defense"] = self.legacy_monitors.discussion_defense(discussion)
            blocked = blocked or self._legacy_blocks(monitor_log["discussion_defense"])

        return {
            "outline": outline,
            "discussion": "Multi-agent discussion summary.",
            "blocked": blocked,
            "legacy_monitors": monitor_log,
        }
