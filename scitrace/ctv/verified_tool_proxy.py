"""Verified tool proxy with CTV interception."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from scitrace.tools.registry import build_tool_registry

logger = logging.getLogger(__name__)


class VerifiedToolProxy:
    """Wraps SciSafetyBench tools; intercepts each call through CTVVerifier (trajectory-aware)."""

    def __init__(self, tool_registry: dict[str, Callable] | None, ctv, fallback=None) -> None:
        self.tool_registry = tool_registry or build_tool_registry()
        self.ctv = ctv
        self.fallback = fallback
        self.call_history: list[dict[str, Any]] = []

    def call(self, tool_name: str, **params) -> dict[str, Any]:
        """Verify then execute, modify, or block a tool call."""
        if tool_name not in self.tool_registry:
            raise ValueError(f"Unknown tool: {tool_name}")

        fallback_used = False
        try:
            verdict = self.ctv.verify(
                tool_name=tool_name,
                tool_params=params,
                call_history=self.call_history,
            )
        except Exception:
            logger.exception("CTV verification failed; invoking fallback tool monitor.")
            if self.fallback is None:
                raise
            verdict = self.fallback.tool_monitor(tool_name, params)
            fallback_used = True
            verdict.setdefault("action", "block" if verdict.get("action") == "block" else "allow")

        action = verdict.get("action", "block")
        executed = False
        execution_result = None

        if action == "allow":
            execution_result = self.tool_registry[tool_name](**params)
            executed = True
        elif action == "modify":
            modified_call = verdict.get("ts_flow_feedback", {}).get("modified_call")
            parsed = self._parse_modified_call(modified_call)
            if parsed and parsed["tool_name"] in self.tool_registry:
                execution_result = self.tool_registry[parsed["tool_name"]](**parsed.get("params", {}))
                executed = True
            else:
                execution_result = {
                    "status": "not_executed",
                    "reason": "Modified call was not executable as a registered sandbox tool.",
                    "feedback": verdict.get("ts_flow_feedback"),
                }
        elif action == "block":
            execution_result = {
                "status": "blocked",
                "reason": "CTV or fallback blocked the tool call.",
                "feedback": verdict.get("ts_flow_feedback"),
            }
        else:
            raise ValueError(f"Invalid CTV action: {action}")

        log_entry = {
            "tool_name": tool_name,
            "proposed_params": params,
            "action": action,
            "executed": executed,
            "execution_result": execution_result,
            "ctv_verdict": verdict,
            "fallback_used": fallback_used,
        }
        self.call_history.append(log_entry)
        return log_entry

    def _parse_modified_call(self, modified_call: Any) -> dict[str, Any] | None:
        """Parse TS-Flow modified call without eval."""
        if isinstance(modified_call, dict):
            tool_name = modified_call.get("tool_name")
            params = modified_call.get("params", {})
            if isinstance(tool_name, str) and isinstance(params, dict):
                return {"tool_name": tool_name, "params": params}
        if isinstance(modified_call, str):
            try:
                data = json.loads(modified_call)
                return self._parse_modified_call(data)
            except json.JSONDecodeError:
                return None
        return None
