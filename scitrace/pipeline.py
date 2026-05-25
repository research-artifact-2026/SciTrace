"""Four-stage SciTrace pipeline scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from .ctv import CompositionalToolChainVerifier, ToolCall, VerificationResult
from .risk_state import CumulativeRiskState
from .sir import SafetyIntrinsicReasoner, StageAssessment

PIPELINE_STAGES = ("thinker", "experimenter", "writer", "reviewer")


@dataclass
class PipelineRun:
    task: str
    stage_assessments: list[StageAssessment] = field(default_factory=list)
    tool_results: list[VerificationResult] = field(default_factory=list)
    state: CumulativeRiskState = field(default_factory=CumulativeRiskState)

    def summary(self) -> dict[str, object]:
        return {
            "task": self.task,
            "stages": [
                {
                    "stage": assessment.stage,
                    "level": assessment.signal.level.label,
                    "action": assessment.signal.action,
                    "category": assessment.signal.category,
                    "checks": assessment.retrieved_checks,
                }
                for assessment in self.stage_assessments
            ],
            "tools": [
                {
                    "action": result.action,
                    "score": result.score,
                    "feedback": result.feedback,
                    "category": result.signal.category,
                }
                for result in self.tool_results
            ],
            "risk_state": self.state.summary(),
        }


class SciTracePipeline:
    """Runs a safe, deterministic approximation of the paper pipeline."""

    def __init__(
        self,
        reasoner: SafetyIntrinsicReasoner | None = None,
        verifier: CompositionalToolChainVerifier | None = None,
    ) -> None:
        self.reasoner = reasoner or SafetyIntrinsicReasoner()
        self.verifier = verifier or CompositionalToolChainVerifier()

    def run(self, task: str, tool_calls: list[ToolCall] | None = None) -> PipelineRun:
        run = PipelineRun(task=task)
        stage_content = task
        for stage in PIPELINE_STAGES:
            assessment = self.reasoner.assess(stage, stage_content, run.state)
            run.stage_assessments.append(assessment)
            stage_content = self._next_stage_content(task, stage, run.state.recommended_action())

        history: list[ToolCall] = []
        for call in tool_calls or []:
            result = self.verifier.verify(task, call, history, run.state)
            run.tool_results.append(result)
            if result.action == "allow":
                history.append(call)
            elif result.action == "modify":
                history.append(ToolCall(name=call.name, arguments="safe alternative"))

        return run

    def _next_stage_content(self, task: str, stage: str, action: str) -> str:
        if action in {"modify", "block"}:
            return f"{task} Redirect toward safe alternatives after {stage}."
        if action == "flag":
            return f"{task} Continue with flagged safety context from {stage}."
        return task
