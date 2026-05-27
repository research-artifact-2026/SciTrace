"""Safety wiring on the retained SafeScientist four-stage workflow."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SafetyConfig:
    """
    Which safety layers run on Thinker → Experimenter → Writer → Reviewer.

    The stage graph is always the SafeScientist scientific-discovery pipeline
    (manuscript §3.1). SciTrace adds SIR + cumulative risk state + safety memory,
    and CTV on tool calls. SafeScientist's original monitors are:

    - **Baseline** (``method=safescientist``): primary defense for experiments.
    - **SciTrace** (``method=scitrace``): superseded by SIR/CTV; monitors only if
      SIR or CTV raises an exception (manuscript §3.1, lines 167–172).
    """

    method: str
    sir_enabled: bool = False
    ctv_enabled: bool = False
    legacy_monitors_primary: bool = False
    legacy_tool_monitor: bool = False
    reviewer_uses_cumulative_state: bool = False
    fallback_on_sir_ctv_error: bool = True

    @classmethod
    def from_experiment_config(cls, config: dict) -> "SafetyConfig":
        method = config.get("method", "scitrace")
        sir_cfg = config.get("sir", {})
        ctv_cfg = config.get("ctv", {})

        if method == "bare":
            return cls(method="bare")

        if method == "safescientist":
            # Paper baseline: original four-layer defense on the shared pipeline
            return cls(
                method="safescientist",
                legacy_monitors_primary=True,
                legacy_tool_monitor=True,
                reviewer_uses_cumulative_state=False,
            )

        if method == "safescientist+sir":
            # Table 4(a): +SIR — SIR replaces independent stage filters
            return cls(
                method="safescientist+sir",
                sir_enabled=sir_cfg.get("enabled", True),
                legacy_monitors_primary=False,
                legacy_tool_monitor=False,
                reviewer_uses_cumulative_state=True,
                fallback_on_sir_ctv_error=True,
            )

        if method == "safescientist+ctv":
            # Table 4(a): +CTV — trajectory verifier on tools; legacy monitors elsewhere
            return cls(
                method="safescientist+ctv",
                ctv_enabled=ctv_cfg.get("enabled", True),
                legacy_monitors_primary=True,
                legacy_tool_monitor=False,
                reviewer_uses_cumulative_state=False,
                fallback_on_sir_ctv_error=True,
            )

        if method == "safescientist_no_review":
            return cls(
                method="safescientist_no_review",
                legacy_monitors_primary=True,
                legacy_tool_monitor=True,
            )

        # SciTrace: SIR at every stage + CTV on tools; legacy monitors = error fallback only
        return cls(
            method="scitrace",
            sir_enabled=sir_cfg.get("enabled", True),
            ctv_enabled=ctv_cfg.get("enabled", True),
            legacy_monitors_primary=False,
            legacy_tool_monitor=False,
            reviewer_uses_cumulative_state=True,
            fallback_on_sir_ctv_error=config.get("fallback_filters", {}).get("enabled", True),
        )
