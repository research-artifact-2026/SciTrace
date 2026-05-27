from tests.fixtures.deterministic_backbone import DeterministicBackbone
from src.pipeline import SciTracePipeline


def test_pipeline_run_completes():
    config = {
        "method": "scitrace",
        "backbone": {"backbone_type": "vllm", "model_name": "test"},
        "sir": {"enabled": True, "k_checks": 3},
        "ctv": {"enabled": True},
    }
    pipeline = SciTracePipeline(config)
    pipeline.backbone = DeterministicBackbone()
    task = {
        "task_id": "BIO_001",
        "domain": "Biology",
        "risk_type": "intentional_malice",
        "task_description": "Biology research task for pipeline test.",
        "tool_sequence": [{"tool": "genome_search", "params": {"query": "demo"}}],
    }
    output = pipeline.run(task)

    required = {
        "task_id",
        "domain",
        "risk_type",
        "thinker_output",
        "experimenter_output",
        "writer_output",
        "reviewer_output",
        "final_paper",
        "cumulative_risk_state",
        "tool_call_log",
        "rejected",
    }
    assert required.issubset(output.keys())
    assert output["cumulative_risk_state"]["signals"]
