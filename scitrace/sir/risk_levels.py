"""Risk level enumeration and interaction escalation pairs."""

from enum import IntEnum


class RiskLevel(IntEnum):
    """Ordered risk levels for cumulative state tracking."""

    SAFE = 0
    LOW_RISK = 1
    WARNING = 2
    HIGH_RISK = 3
    BLOCK = 4

    @classmethod
    def from_string(cls, s: str) -> "RiskLevel":
        """Parse a risk level string into a RiskLevel enum value."""
        mapping = {
            "safe": cls.SAFE,
            "low_risk": cls.LOW_RISK,
            "low-risk": cls.LOW_RISK,
            "warning": cls.WARNING,
            "high_risk": cls.HIGH_RISK,
            "high-risk": cls.HIGH_RISK,
            "block": cls.BLOCK,
        }
        return mapping[s.lower()]


INTERACTION_ESCALATION_PAIRS = [
    ({"S1", "S2"}, 1),
    ({"S1", "S3"}, 1),
    ({"S2", "S9"}, 1),
    ({"S4", "S6"}, 1),
]
