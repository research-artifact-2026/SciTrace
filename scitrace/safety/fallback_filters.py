"""SciTrace error-path wrapper around retained SafeScientist monitors."""

from __future__ import annotations

from typing import Any

from scitrace.safety.safescientist_monitors import SafescientistStageMonitors


class StageFallbackFilters:
    """Invoked only when SIR or CTV raises or cannot parse a response."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._monitors = SafescientistStageMonitors(enabled=enabled)

    def _wrap(self, result: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {
                "fallback_used": False,
                "risk_level": "safe",
                "action": "allow",
                "reason": "Fallback filters are disabled.",
            }
        return {
            "fallback_used": True,
            "risk_level": result.get("risk_level", "warning"),
            "action": result.get("action", "flag"),
            "reason": result.get("reason", "SafeScientist fallback invoked."),
        }

    def prompt_monitor(self, text: str) -> dict[str, Any]:
        return self._wrap(self._monitors.prompt_monitor(text))

    def output_filter(self, text: str) -> dict[str, Any]:
        return self._wrap(self._monitors.output_filter(text))

    def tool_monitor(self, tool_name: str, tool_params: dict) -> dict[str, Any]:
        return self._wrap(self._monitors.tool_monitor(tool_name, tool_params))

    def discussion_defense(self, messages: list[dict]) -> dict[str, Any]:
        return self._wrap(self._monitors.discussion_defense(messages))


# Spec alias
SafeScientistFallbackFilters = StageFallbackFilters
