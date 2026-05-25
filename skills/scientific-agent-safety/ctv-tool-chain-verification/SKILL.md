# CTV Tool-Chain Verification

Use this skill before a scientific agent executes a tool call that may be safe
alone but risky as part of a longer sequence.

## Inputs

- User or agent request.
- Proposed tool call.
- Prior tool-call history.
- Current cumulative risk state.

## Procedure

1. Score request harmfulness.
2. Score compositional risk from the full trajectory.
3. Score direct tool invocation safety.
4. Map the composite score to allow, modify, or block.
5. Add the resulting signal to the shared cumulative risk state.
6. If needed, generate safe redirection feedback.

## Output

A verification result with action, score, risk category, and feedback.

## Guardrails

- Never provide operational instructions for hazardous conduct.
- Use synthetic, public, aggregate, or non-sensitive alternatives when modifying.
- Block trajectories whose danger emerges only from the combined calls.
