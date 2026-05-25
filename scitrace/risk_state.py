"""Cumulative risk state for SciTrace pipeline runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterable


class RiskLevel(IntEnum):
    """Graduated risk levels from the SciTrace paper."""

    SAFE = 0
    LOW_RISK = 1
    WARNING = 2
    HIGH_RISK = 3
    BLOCK = 4

    @classmethod
    def from_name(cls, name: str) -> "RiskLevel":
        normalized = name.strip().upper().replace("-", "_")
        return cls[normalized]

    @property
    def label(self) -> str:
        return self.name.replace("_", "-")


@dataclass(frozen=True)
class RiskSignal:
    """A safety observation emitted by SIR or CTV."""

    category: str
    level: RiskLevel
    source: str
    description: str
    action: str = "proceed"
    metadata: dict[str, object] = field(default_factory=dict)


INTERACTION_ESCALATION_PAIRS = {
    frozenset(("S1", "S2")),
    frozenset(("S1", "S9")),
    frozenset(("S2", "S9")),
    frozenset(("S4", "S6")),
    frozenset(("S5", "S6")),
}


@dataclass
class CumulativeRiskState:
    """Shared safety memory carried across all stages and tool calls."""

    signals: list[RiskSignal] = field(default_factory=list)

    def add_signal(self, signal: RiskSignal) -> None:
        self.signals.append(signal)

    def extend(self, signals: Iterable[RiskSignal]) -> None:
        for signal in signals:
            self.add_signal(signal)

    @property
    def categories(self) -> set[str]:
        return {signal.category for signal in self.signals if signal.category}

    @property
    def base_level(self) -> RiskLevel:
        if not self.signals:
            return RiskLevel.SAFE
        return max((signal.level for signal in self.signals), default=RiskLevel.SAFE)

    @property
    def overall_level(self) -> RiskLevel:
        level = self.base_level
        if self._has_interaction_escalation() and level < RiskLevel.BLOCK:
            return RiskLevel(level + 1)
        return level

    def recommended_action(self) -> str:
        level = self.overall_level
        if level == RiskLevel.BLOCK:
            return "block"
        if level == RiskLevel.HIGH_RISK:
            return "modify"
        if level == RiskLevel.WARNING:
            return "flag"
        return "proceed"

    def summary(self) -> dict[str, object]:
        return {
            "overall_level": self.overall_level.label,
            "base_level": self.base_level.label,
            "recommended_action": self.recommended_action(),
            "categories": sorted(self.categories),
            "signal_count": len(self.signals),
            "signals": [
                {
                    "category": signal.category,
                    "level": signal.level.label,
                    "source": signal.source,
                    "description": signal.description,
                    "action": signal.action,
                }
                for signal in self.signals
            ],
        }

    def _has_interaction_escalation(self) -> bool:
        categories = self.categories
        return any(pair.issubset(categories) for pair in INTERACTION_ESCALATION_PAIRS)
