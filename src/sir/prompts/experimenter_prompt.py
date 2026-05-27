"""Experimenter-stage SIR prompt."""

from __future__ import annotations

from src.sir.cumulative_risk_state import CumulativeRiskState


def build_prompt(
    task_content: str,
    cumulative_state: CumulativeRiskState,
    retrieved_checks: list[str],
) -> list[dict]:
    """Build messages for Experimenter SIR assessment."""
    checks = "\n".join(f"- {c}" for c in retrieved_checks) or "- (none retrieved)"
    system = (
        "You are the SIR module at the Experimenter stage. Focus on tool and protocol safety, "
        "dual-use artifact production, and heightened scrutiny when prior stages flagged risk."
    )
    user = f"""Task content:
{task_content}

Cumulative risk state:
{cumulative_state.get_context_string()}

Retrieved safety checks:
{checks}

Return JSON: risk_level, categories (S1-S9), justification, action."""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
