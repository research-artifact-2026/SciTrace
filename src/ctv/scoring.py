"""CTV scoring function (Equation 1, Appendix A)."""

from __future__ import annotations

TOOL_SAFETY_MAP = {"safe": 0.0, "uncertain": 0.1, "unsafe": 0.2}

# Table 9 — manuscript Appendix A
SCORE_EXAMPLES = [
    {"request_harmful": False, "compositional_risk": False, "tool_safety": "safe", "score": 0.0, "action": "allow"},
    {"request_harmful": False, "compositional_risk": False, "tool_safety": "unsafe", "score": 0.2, "action": "allow"},
    {"request_harmful": False, "compositional_risk": True, "tool_safety": "safe", "score": 0.4, "action": "modify"},
    {"request_harmful": True, "compositional_risk": False, "tool_safety": "uncertain", "score": 0.5, "action": "modify"},
    {"request_harmful": True, "compositional_risk": True, "tool_safety": "safe", "score": 0.8, "action": "block"},
    {"request_harmful": True, "compositional_risk": True, "tool_safety": "unsafe", "score": 1.0, "action": "block"},
]


def compute_ctv_score(
    request_harmful: bool,
    compositional_risk: bool,
    tool_safety_rating: str,
    *,
    threshold: float = 0.5,
    weights: dict[str, float | str] | None = None,
) -> tuple[float, str]:
    """Map CTV judgments to scalar score and action (Eq. 1 and config overrides)."""
    resolved = {"w1": 0.4, "w2": 0.4, "w3": "r_tool"}
    if weights:
        resolved.update(weights)

    r_tool = TOOL_SAFETY_MAP[tool_safety_rating]
    w1 = float(resolved["w1"])
    w2 = float(resolved["w2"])
    w3 = r_tool if resolved["w3"] == "r_tool" else float(resolved["w3"])
    s = (w1 * int(request_harmful)) + (w2 * int(compositional_risk)) + w3

    if s > threshold:
        action = "block"
    elif s >= max(0.4, threshold - 0.1):
        action = "modify"
    else:
        action = "allow"
    return round(s, 4), action
