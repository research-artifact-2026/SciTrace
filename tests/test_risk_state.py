from scitrace.risk_state import CumulativeRiskState, RiskLevel, RiskSignal


def test_interaction_escalates_dual_use_sequence() -> None:
    state = CumulativeRiskState()
    state.add_signal(RiskSignal("S2", RiskLevel.WARNING, "test", "dual-use warning"))
    state.add_signal(RiskSignal("S9", RiskLevel.WARNING, "test", "trajectory warning"))

    assert state.base_level == RiskLevel.WARNING
    assert state.overall_level == RiskLevel.HIGH_RISK
    assert state.recommended_action() == "modify"


def test_empty_state_is_safe() -> None:
    state = CumulativeRiskState()

    assert state.overall_level == RiskLevel.SAFE
    assert state.summary()["signal_count"] == 0
