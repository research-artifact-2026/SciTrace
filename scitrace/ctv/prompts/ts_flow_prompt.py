"""TS-Flow corrective feedback prompt (Figure 16)."""

from __future__ import annotations

import json


def build_prompt(blocked_call: dict, ctv_assessment: dict, task_context: str) -> list[dict]:
    """Build TS-Flow feedback messages."""
    system = (
        "You are TS-Flow corrective feedback for SciTrace. Responsibilities: "
        "(1) Explain why the call was flagged, citing S categories; "
        "(2) Suggest a concrete safe alternative preserving scientific validity; "
        "(3) Frame feedback constructively. Return JSON only."
    )
    user = f"""Task context:
{task_context}

Blocked/modified call:
{json.dumps(blocked_call, indent=2)}

CTV assessment:
{json.dumps(ctv_assessment, indent=2)}

Return JSON: explanation, safe_alternative, modified_call
(modified_call may be a JSON object with tool_name and params for a registered sandbox tool)."""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
