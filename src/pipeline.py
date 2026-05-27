"""SciTrace pipeline: four-stage workflow with configurable safety layers."""

from __future__ import annotations

from src.backbone.backbone_factory import create_backbone
from src.ctv.ctv_verifier import CTVVerifier
from src.ctv.verified_tool_proxy import VerifiedToolProxy
from src.pipeline_config import SafetyConfig
from src.safety.fallback_filters import StageFallbackFilters
from src.safety.safescientist_monitors import SafescientistStageMonitors
from src.sir.cumulative_risk_state import CumulativeRiskState
from src.sir.safety_memory import SafetyMemory
from src.sir.sir_module import SIRModule
from src.stages.experimenter import ExperimenterStage
from src.stages.reviewer import ReviewerStage
from src.stages.thinker import ThinkerStage
from src.stages.writer import WriterStage
from src.tools.registry import build_tool_registry
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SciTracePipeline:
    """
    Orchestrates Thinker → Experimenter → Writer → Reviewer.

    Built on the SafeScientist multi-stage scientific-agent workflow. SciTrace
    extends it with SIR (cross-stage cumulative reasoning) and CTV (trajectory-aware
    tool verification). The ``method`` config selects which layers are active; the
    stage graph is unchanged.
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logger
        self.safety = SafetyConfig.from_experiment_config(config)

        backbone_cfg = dict(config.get("backbone", {}))
        self.backbone = create_backbone(backbone_cfg)

        self.legacy_monitors = SafescientistStageMonitors(
            enabled=self.safety.legacy_monitors_primary
            or config.get("fallback_filters", {}).get("enabled", True)
        )
        self.fallback = StageFallbackFilters(
            enabled=config.get("fallback_filters", {}).get("enabled", True)
        )
        self.tool_registry = build_tool_registry()
        self.cumulative_state = CumulativeRiskState()

        self.sir = SIRModule(
            self.backbone,
            SafetyMemory(),
            k_checks=config.get("sir", {}).get("k_checks", 3),
            enabled=self.safety.sir_enabled,
        )
        self.backbone.default_seed = config.get("seed", 42)
        self.ctv = CTVVerifier(
            self.backbone,
            self.cumulative_state,
            ctv_config=config.get("ctv", {}),
        )
        self.tool_proxy = VerifiedToolProxy(
            tool_registry=self.tool_registry,
            ctv=self.ctv,
            fallback=self.fallback if self.safety.fallback_on_sir_ctv_error else None,
        )

        stage_kwargs = dict(
            backbone=self.backbone,
            sir=self.sir,
            cumulative_state=self.cumulative_state,
            safety=self.safety,
            legacy_monitors=self.legacy_monitors,
            fallback=self.fallback,
        )
        self.thinker = ThinkerStage(**stage_kwargs)
        self.experimenter = ExperimenterStage(
            **stage_kwargs,
            tool_proxy=self.tool_proxy if self.safety.ctv_enabled else None,
            tool_registry=self.tool_registry,
        )
        self.writer = WriterStage(**stage_kwargs)
        self.reviewer = ReviewerStage(**stage_kwargs)

    @property
    def backbone(self):
        return self._backbone

    @backbone.setter
    def backbone(self, value) -> None:
        self._backbone = value
        if hasattr(self, "sir"):
            self.sir.backbone = value
        if hasattr(self, "ctv"):
            self.ctv.backbone = value
        for stage_name in ("thinker", "experimenter", "writer", "reviewer"):
            if hasattr(self, stage_name):
                getattr(self, stage_name).backbone = value

    def run(self, task: dict) -> dict:
        """Run the full four-stage pipeline for one benchmark task."""
        self.cumulative_state = CumulativeRiskState()
        self.ctv.cumulative_state = self.cumulative_state
        self.ctv.task_context = task.get("task_description", "")
        self.tool_proxy.call_history = []

        context: dict = {}
        context["thinker_output"] = self.thinker.run(task, context)
        context["experimenter_output"] = self.experimenter.run(task, context)
        writer_out = self.writer.run(task, context)
        context["writer_output"] = writer_out

        reviewer_cfg = self.config.get("reviewer", {})
        if reviewer_cfg.get("enabled", True):
            reviewer_out = self.reviewer.run(task, context)
        else:
            reviewer_out = {
                "review": "Reviewer disabled for this configuration.",
                "rejected": False,
                "skipped": True,
            }

        final_paper = writer_out.get("draft", "")
        rejected = bool(reviewer_out.get("rejected"))
        if rejected:
            final_paper = "[REJECTED] " + str(reviewer_out.get("review", ""))[:500]

        tool_log = list(self.tool_proxy.call_history)
        if not self.safety.ctv_enabled:
            tool_log = context.get("experimenter_output", {}).get("tool_results", [])

        return {
            "task_id": task.get("task_id"),
            "domain": task.get("domain"),
            "risk_type": task.get("risk_type"),
            "is_compositional_escape": bool(task.get("is_compositional_escape")),
            "method": self.config.get("method", "scitrace"),
            "thinker_output": context["thinker_output"],
            "experimenter_output": context["experimenter_output"],
            "writer_output": writer_out,
            "reviewer_output": reviewer_out,
            "final_paper": final_paper,
            "cumulative_risk_state": self.cumulative_state.to_dict(),
            "tool_call_log": tool_log,
            "rejected": rejected,
            "safety_score": None,
            "ctv_detected_escape": any(
                log.get("ctv_verdict", {}).get("compositional_risk")
                for log in self.tool_proxy.call_history
            ),
        }
