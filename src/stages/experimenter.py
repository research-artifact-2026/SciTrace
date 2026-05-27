"""Experimenter stage: tools and protocols (CTV or legacy tool monitor)."""

from __future__ import annotations

from src.ctv.verified_tool_proxy import VerifiedToolProxy
from src.stages.base_stage import BaseStage
from src.tools.registry import get_tool_spec, normalize_tool_params


class ExperimenterStage(BaseStage):
    """
    Runs experiments and tool calls.

    - SciTrace: VerifiedToolProxy + CTV (+ SIR)
    - SafeScientist: per-call tool_monitor on the shared tool registry
    - Bare: direct sandbox tool execution
    """

    def __init__(
        self,
        backbone,
        sir,
        cumulative_state,
        safety,
        tool_proxy: VerifiedToolProxy | None,
        tool_registry: dict,
        legacy_monitors=None,
        fallback=None,
    ):
        super().__init__(backbone, sir, cumulative_state, safety, legacy_monitors, fallback)
        self.tool_proxy = tool_proxy
        self.tool_registry = tool_registry

    def run(self, task: dict, context: dict) -> dict:
        desc = task.get("task_description", "")
        thinker = context.get("thinker_output", {})
        if thinker.get("blocked"):
            return {"plan": "Skipped: Thinker stage blocked.", "tool_results": [], "blocked": True}

        if self.safety.sir_enabled:
            self._sir_check("experimenter", desc, context)

        sequence = task.get("tool_sequence") or [
            {"tool": "genome_search", "params": {"organism": "educational_model", "query": "demo"}}
        ]
        tool_results = []
        blocked = False

        if self.safety.ctv_enabled and self.tool_proxy is not None:
            for step in sequence:
                tool_name = step.get("tool", "genome_search")
                get_tool_spec(tool_name)
                params = normalize_tool_params(tool_name, step.get("params", {}))
                entry = self.tool_proxy.call(tool_name, **params)
                tool_results.append(entry)
                if entry.get("action") == "block":
                    blocked = True
                    break
        elif self.safety.legacy_tool_monitor and self.legacy_monitors:
            for step in sequence:
                tool_name = step.get("tool", "genome_search")
                get_tool_spec(tool_name)
                params = normalize_tool_params(tool_name, step.get("params", {}))
                verdict = self.legacy_monitors.tool_monitor(tool_name, params)
                executed = verdict.get("action") != "block"
                result = (
                    self.tool_registry[tool_name](**params)
                    if executed and tool_name in self.tool_registry
                    else {"status": "blocked", "monitor_verdict": verdict}
                )
                tool_results.append(
                    {
                        "tool_name": tool_name,
                        "proposed_params": params,
                        "action": "block" if not executed else "allow",
                        "executed": executed,
                        "execution_result": result,
                        "monitor_verdict": verdict,
                    }
                )
                if not executed:
                    blocked = True
                    break
        else:
            for step in sequence:
                tool_name = step.get("tool", "genome_search")
                get_tool_spec(tool_name)
                params = normalize_tool_params(tool_name, step.get("params", {}))
                if tool_name not in self.tool_registry:
                    raise ValueError(f"Unknown tool: {tool_name}")
                tool_results.append(
                    {
                        "tool_name": tool_name,
                        "executed": True,
                        "execution_result": self.tool_registry[tool_name](**params),
                    }
                )

        plan = "Experiment plan with tool execution (configuration-dependent safety)."
        if self.safety.sir_enabled:
            post = self._sir_check("experimenter", plan, {"tools": len(tool_results)})
            blocked = blocked or post.get("action") in {"block", "flag"}

        return {"plan": plan, "tool_results": tool_results, "blocked": blocked}
