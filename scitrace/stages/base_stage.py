"""Abstract base for the four-stage scientific discovery workflow."""

from __future__ import annotations

from abc import ABC, abstractmethod

from scitrace.pipeline_config import SafetyConfig
from scitrace.sir.cumulative_risk_state import CumulativeRiskState
from scitrace.sir.sir_module import SIRModule
from scitrace.utils.logger import get_logger

logger = get_logger(__name__)


class BaseStage(ABC):
    """
    Shared stage scaffold from the SafeScientist workflow.

    SciTrace adds SIR (all stages) and CTV (Experimenter). Retained SafeScientist
    monitors run as the primary layer when ``method=safescientist``, and only as
    error fallback when SIR/CTV fails in ``method=scitrace``.
    """

    def __init__(
        self,
        backbone,
        sir: SIRModule,
        cumulative_state: CumulativeRiskState,
        safety: SafetyConfig,
        legacy_monitors=None,
        fallback=None,
    ):
        self.backbone = backbone
        self.sir = sir
        self.cumulative_state = cumulative_state
        self.safety = safety
        self.legacy_monitors = legacy_monitors
        self.fallback = fallback

    @abstractmethod
    def run(self, task: dict, context: dict) -> dict:
        """Execute stage logic."""

    def _sir_check(self, stage_name: str, content: str, extra: dict | None = None) -> dict:
        """SIR assessment when enabled; legacy fallback only on SciTrace + failure."""
        if not self.safety.sir_enabled:
            return {
                "risk_level": "safe",
                "categories": [],
                "justification": "SIR not enabled for this configuration.",
                "action": "proceed",
            }
        try:
            return self.sir.assess(stage_name, content, self.cumulative_state, extra)
        except Exception:
            logger.exception("SIR failed at %s", stage_name)
            if self.safety.fallback_on_sir_ctv_error and self.fallback is not None:
                result = self.fallback.prompt_monitor(content)
                signal = {
                    "stage": stage_name,
                    "risk_level": result.get("risk_level", "warning"),
                    "categories": [],
                    "justification": result.get("reason", "fallback"),
                    "action": result.get("action", "flag"),
                }
                self.cumulative_state.add_signal(signal)
                return signal
            raise

    def _legacy_blocks(self, monitor_result: dict) -> bool:
        return monitor_result.get("action") in {"block", "flag"}
