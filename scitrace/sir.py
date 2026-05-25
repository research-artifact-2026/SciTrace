"""Safety-Intrinsic Reasoning Loop implementation."""

from __future__ import annotations

from dataclasses import dataclass

from .risk_state import CumulativeRiskState, RiskLevel, RiskSignal
from .safety_memory import SafetyMemory
from .taxonomy import KEYWORD_RULES

STAGE_PRIORS = {
    "thinker": "dual-use research direction",
    "experimenter": "tool and protocol safety",
    "writer": "information disclosure and publication risk",
    "reviewer": "ethical and scientific review",
}


@dataclass
class StageAssessment:
    stage: str
    signal: RiskSignal
    retrieved_checks: list[str]


class SafetyIntrinsicReasoner:
    """Deterministic SIR scaffold for demos and tests."""

    def __init__(self, memory: SafetyMemory | None = None) -> None:
        self.memory = memory or SafetyMemory.with_default_checks()

    def assess(
        self,
        stage: str,
        content: str,
        state: CumulativeRiskState,
    ) -> StageAssessment:
        stage_key = stage.lower()
        query = f"{STAGE_PRIORS.get(stage_key, stage_key)} {content}"
        checks = self.memory.retrieve(query)
        category = self._detect_category(content)
        level = self._level_for_category(category, content, state)
        action = self._action_for_level(level)
        description = self._describe(stage_key, category, level, state)
        signal = RiskSignal(
            category=category,
            level=level,
            source=f"SIR:{stage_key}",
            description=description,
            action=action,
            metadata={"retrieved_checks": [check.title for check in checks]},
        )
        state.add_signal(signal)
        return StageAssessment(
            stage=stage_key,
            signal=signal,
            retrieved_checks=[check.title for check in checks],
        )

    def _detect_category(self, content: str) -> str:
        lowered = content.lower()
        for category, keywords in KEYWORD_RULES:
            if any(keyword in lowered for keyword in keywords):
                return category
        return ""

    def _level_for_category(
        self,
        category: str,
        content: str,
        state: CumulativeRiskState,
    ) -> RiskLevel:
        lowered = content.lower()
        if "safe" in lowered or "non-sensitive" in lowered or "non-hazardous" in lowered:
            candidate = RiskLevel.LOW_RISK if category else RiskLevel.SAFE
        elif category in {"S1", "S2", "S3", "S5"}:
            candidate = RiskLevel.HIGH_RISK
        elif category in {"S4", "S6", "S7", "S8", "S9"}:
            candidate = RiskLevel.WARNING
        else:
            candidate = RiskLevel.SAFE

        if state.overall_level >= RiskLevel.HIGH_RISK and candidate < RiskLevel.WARNING:
            return RiskLevel.WARNING
        return candidate

    def _action_for_level(self, level: RiskLevel) -> str:
        if level >= RiskLevel.BLOCK:
            return "block"
        if level >= RiskLevel.HIGH_RISK:
            return "modify"
        if level >= RiskLevel.WARNING:
            return "flag"
        return "proceed"

    def _describe(
        self,
        stage: str,
        category: str,
        level: RiskLevel,
        state: CumulativeRiskState,
    ) -> str:
        if not category:
            return f"{stage} stage has no matching high-risk category."
        prior = " with prior state carried forward" if state.signals else ""
        return f"{stage} stage matched {category} at {level.label}{prior}."
