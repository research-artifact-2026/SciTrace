from scitrace.safety import StageFallbackFilters


def test_fallback_disabled_returns_allow():
    fallback = StageFallbackFilters(enabled=False)
    result = fallback.prompt_monitor("hazardous synthesis")
    assert result["fallback_used"] is False
    assert result["action"] == "allow"


def test_fallback_flags_high_risk_text():
    fallback = StageFallbackFilters(enabled=True)
    result = fallback.prompt_monitor("request involving hazardous synthesis steps")
    assert result["fallback_used"] is True
    assert result["risk_level"] in {"warning", "high_risk"}
    assert result["action"] in {"flag", "block"}


def test_tool_monitor_blocks_high_risk_tool_call():
    fallback = StageFallbackFilters(enabled=True)
    result = fallback.tool_monitor("retrosynthesis_planner", {"query": "hazardous synthesis"})
    assert result["fallback_used"] is True
    assert result["action"] == "block"
