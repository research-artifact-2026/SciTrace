from tests.fixtures.deterministic_backbone import DeterministicBackbone

from src.ctv.ctv_verifier import CTVVerifier
from src.sir.cumulative_risk_state import CumulativeRiskState


def test_ctv_verify_returns_required_fields():
    state = CumulativeRiskState()
    ctv = CTVVerifier(DeterministicBackbone(), state, task_context="compositional tool task")
    verdict = ctv.verify("retrosynthesis_planner", {"compound_id": "demo"}, [])
    for key in ["request_harmful", "compositional_risk", "tool_safety", "score", "action"]:
        assert key in verdict


def test_ctv_writes_signal_to_state():
    state = CumulativeRiskState()
    ctv = CTVVerifier(DeterministicBackbone(), state)
    ctv.verify("genome_search", {"query": "demo"}, [])
    assert len(state.signals) >= 1


def test_ctv_ts_flow_on_block(monkeypatch):
    state = CumulativeRiskState()
    ctv = CTVVerifier(DeterministicBackbone(), state)

    def fake_score(harm, comp, tool):
        return 1.0, "block"

    monkeypatch.setattr("src.ctv.ctv_verifier.compute_ctv_score", fake_score)
    verdict = ctv.verify("retrosynthesis_planner", {"compound_id": "x"}, [{"tool_name": "a"}] * 3)
    assert verdict["action"] == "block"
    assert "ts_flow_feedback" in verdict
