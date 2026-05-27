"""TS-Flow corrective feedback generator."""

from __future__ import annotations

from scitrace.ctv.prompts import ts_flow_prompt
from scitrace.utils.logger import get_logger
from scitrace.utils.pydantic_schemas import TSFlowOutput

logger = get_logger(__name__)


class TSFlowFeedback:
    """Generates constructive alternatives when CTV flags a tool call."""

    def __init__(self, backbone) -> None:
        self.backbone = backbone

    def generate(self, blocked_call: dict, ctv_assessment: dict, task_context: str) -> dict:
        """Return TS-Flow feedback dict."""
        messages = ts_flow_prompt.build_prompt(blocked_call, ctv_assessment, task_context)
        try:
            return self.backbone.complete_json(messages, schema_class=TSFlowOutput)
        except Exception as exc:
            logger.error("TS-Flow generation failed: %s", exc)
            return {
                "explanation": "CTV flagged compositional or harmful risk.",
                "safe_alternative": "Use a benign educational sandbox tool and aggregate statistics only.",
                "modified_call": '{"tool_name": "genome_search", "params": {"organism": "educational_model"}}',
            }
