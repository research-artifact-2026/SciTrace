from scitrace.sir.cumulative_risk_state import CumulativeRiskState
from scitrace.sir.safety_memory import SafetyMemory


def test_cumulative_risk_state_updates_level():
    state = CumulativeRiskState()
    state.add_signal(
        {
            "stage": "thinker",
            "risk_level": "warning",
            "categories": ["S2"],
            "justification": "test fixture",
            "action": "flag",
        }
    )
    assert state.overall_level.name == "WARNING"


def test_interaction_escalation_s1_s2():
    state = CumulativeRiskState()
    state.add_signal(
        {
            "stage": "thinker",
            "risk_level": "warning",
            "categories": ["S1"],
            "justification": "a",
            "action": "flag",
        }
    )
    state.add_signal(
        {
            "stage": "experimenter",
            "risk_level": "warning",
            "categories": ["S2"],
            "justification": "b",
            "action": "flag",
        }
    )
    assert state.overall_level.value >= 2


def test_get_context_string_nonempty():
    state = CumulativeRiskState()
    state.add_signal(
        {
            "stage": "thinker",
            "risk_level": "safe",
            "categories": [],
            "justification": "ok",
            "action": "proceed",
        }
    )
    assert state.get_context_string()


def test_safety_memory_retrieval():
    memory = SafetyMemory()
    results = memory.retrieve("pathogen genome query", k=3)
    assert len(results) <= 3
    assert all(isinstance(item, str) for item in results)


def test_empty_memory_returns_empty():
    memory = SafetyMemory()
    memory._entries = []
    assert memory.retrieve("anything", k=3) == []
