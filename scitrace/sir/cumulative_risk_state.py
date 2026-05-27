"""Cumulative risk state tracker with interaction escalation."""

from __future__ import annotations

from scitrace.sir.risk_levels import INTERACTION_ESCALATION_PAIRS, RiskLevel


class CumulativeRiskState:
    """Tracks cumulative risk signals across pipeline stages."""

    def __init__(self) -> None:
        self.signals: list[dict] = []
        self.overall_level: RiskLevel = RiskLevel.SAFE

    def add_signal(self, signal: dict) -> None:
        """Append a signal and recompute overall risk level."""
        self.signals.append(signal)
        self._recompute_overall_level()

    def _recompute_overall_level(self) -> None:
        """Compute max risk level with interaction escalation."""
        if not self.signals:
            self.overall_level = RiskLevel.SAFE
            return

        levels = []
        for signal in self.signals:
            level_value = signal.get("risk_level", "safe")
            if isinstance(level_value, RiskLevel):
                levels.append(level_value)
            else:
                levels.append(RiskLevel.from_string(str(level_value)))

        base_level = max(levels, key=lambda item: item.value)
        escalation = 0

        all_categories: set[str] = set()
        for signal in self.signals:
            all_categories.update(signal.get("categories", []))

        for pair, bump in INTERACTION_ESCALATION_PAIRS:
            if pair.issubset(all_categories):
                escalation += bump

        final_value = min(int(base_level) + escalation, int(RiskLevel.BLOCK))
        self.overall_level = RiskLevel(final_value)

    def get_context_string(self) -> str:
        """Format cumulative state for prompt injection."""
        if not self.signals:
            return "No prior risk signals recorded."

        lines = [f"Overall risk level: {self.overall_level.name}"]
        for idx, signal in enumerate(self.signals, start=1):
            lines.append(
                f"Signal {idx} [{signal.get('stage', 'unknown')}]: "
                f"level={signal.get('risk_level')}, categories={signal.get('categories', [])}, "
                f"action={signal.get('action', 'n/a')}, "
                f"justification={signal.get('justification', '')}"
            )
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize state to a dictionary."""
        return {
            "signals": self.signals,
            "overall_level": self.overall_level.name.lower(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CumulativeRiskState":
        """Restore state from a dictionary."""
        state = cls()
        state.signals = list(data.get("signals", []))
        overall = data.get("overall_level", "safe")
        state.overall_level = RiskLevel.from_string(str(overall))
        return state
