# SIR Stage Assessment

Use this skill when a scientific-agent workflow needs stage-aware safety
reasoning that preserves risk context across Thinker, Experimenter, Writer, and
Reviewer stages.

## Inputs

- Current stage name.
- Current stage content.
- Existing cumulative risk state.

## Procedure

1. Retrieve safety checks relevant to the stage content.
2. Identify matching SciTrace risk categories S1-S9.
3. Assign one of SAFE, LOW_RISK, WARNING, HIGH_RISK, or BLOCK.
4. Record a risk signal in the shared cumulative state.
5. Recommend proceed, flag, modify, or block.

## Output

A structured risk signal containing category, risk level, source, rationale, and
recommended action.

## Guardrails

- Prefer safe redirection over operational detail.
- Carry prior warnings forward into later stages.
- Treat cross-stage escalation as meaningful even when the current stage looks benign.
