"""All experiment methods use the same four-stage SafeScientist workflow."""

import pytest
from tests.fixtures.deterministic_backbone import DeterministicBackbone

from scitrace.pipeline import SciTracePipeline
from scitrace.pipeline_config import SafetyConfig

TASK = {
    "task_id": "T001",
    "domain": "Biology",
    "risk_type": "intentional_malice",
    "task_description": "Pipeline test task.",
    "tool_sequence": [{"tool": "genome_search", "params": {"query": "demo"}}],
}


def _pipeline(method: str) -> SciTracePipeline:
    p = SciTracePipeline(
        {
            "method": method,
            "backbone": {"backbone_type": "vllm", "model_name": "test"},
            "sir": {"enabled": True},
            "ctv": {"enabled": True},
        }
    )
    p.backbone = DeterministicBackbone()
    return p


@pytest.mark.parametrize(
    "method,expect_sir,expect_ctv,expect_legacy_tools",
    [
        ("bare", False, False, False),
        ("safescientist", False, False, True),
        ("safescientist+sir", True, False, False),
        ("safescientist+ctv", False, True, False),
        ("scitrace", True, True, False),
    ],
)
def test_safety_config_flags(method, expect_sir, expect_ctv, expect_legacy_tools):
    cfg = SafetyConfig.from_experiment_config({"method": method, "sir": {}, "ctv": {}})
    assert cfg.sir_enabled is expect_sir
    assert cfg.ctv_enabled is expect_ctv
    assert cfg.legacy_tool_monitor is expect_legacy_tools


@pytest.mark.parametrize("method", ["bare", "safescientist", "scitrace"])
def test_same_four_stages_run(method):
    out = _pipeline(method).run(dict(TASK))
    assert out["thinker_output"] is not None
    assert out["experimenter_output"] is not None
    assert out["writer_output"] is not None
    assert out["reviewer_output"] is not None


def test_reviewer_can_be_disabled():
    p = SciTracePipeline(
        {
            "method": "safescientist_no_review",
            "backbone": {"backbone_type": "vllm", "model_name": "test"},
            "reviewer": {"enabled": False},
        }
    )
    p.backbone = DeterministicBackbone()
    out = p.run(dict(TASK))
    assert out["reviewer_output"].get("skipped") is True
