from scitrace.ctv import ToolCall
from scitrace.pipeline import SciTracePipeline


def test_pipeline_carries_stage_state() -> None:
    pipeline = SciTracePipeline()
    run = pipeline.run("Design a safe synthetic-data classroom demonstration.")
    summary = run.summary()

    assert len(summary["stages"]) == 4
    assert summary["risk_state"]["signal_count"] == 4


def test_pipeline_records_tool_results() -> None:
    pipeline = SciTracePipeline()
    run = pipeline.run(
        "Compare public, non-sensitive literature metadata",
        [ToolCall("search_literature", "public abstracts")],
    )

    assert run.tool_results[0].action == "allow"
