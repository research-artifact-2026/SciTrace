"""Compositional Tool-Chain Verifier."""

from __future__ import annotations

from dataclasses import dataclass

from .risk_state import CumulativeRiskState, RiskLevel, RiskSignal


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: str

    @classmethod
    def parse(cls, raw: str) -> "ToolCall":
        if ":" in raw:
            name, arguments = raw.split(":", 1)
            return cls(name=name.strip(), arguments=arguments.strip())
        return cls(name=raw.strip(), arguments="")


@dataclass(frozen=True)
class VerificationResult:
    action: str
    score: float
    signal: RiskSignal
    feedback: str


class CompositionalToolChainVerifier:
    """Scores each tool call in the context of the full call history."""

    def __init__(self, block_threshold: float = 0.5, modify_threshold: float = 0.4) -> None:
        self.block_threshold = block_threshold
        self.modify_threshold = modify_threshold

    def verify(
        self,
        request: str,
        call: ToolCall,
        history: list[ToolCall],
        state: CumulativeRiskState,
    ) -> VerificationResult:
        harmful = self._request_harmfulness(request)
        compositional = self._compositional_risk(call, history)
        tool_risk = self._tool_invocation_risk(call)
        score = round((0.4 * harmful) + (0.4 * compositional) + tool_risk, 3)
        action = self._action(score)
        category = "S9" if compositional else self._category_for_call(call)
        level = self._level(action)
        feedback = self._feedback(action, call)
        signal = RiskSignal(
            category=category,
            level=level,
            source="CTV",
            description=(
                f"CTV score={score} harmful={harmful} "
                f"compositional={compositional} tool_risk={tool_risk}"
            ),
            action=action,
            metadata={
                "tool": call.name,
                "arguments": call.arguments,
                "history_length": len(history),
            },
        )
        state.add_signal(signal)
        return VerificationResult(action=action, score=score, signal=signal, feedback=feedback)

    def _request_harmfulness(self, request: str) -> int:
        lowered = request.lower()
        markers = (
            "weapon",
            "pathogen",
            "toxic",
            "exploit",
            "private data",
            "credential",
            "hazardous synthesis",
        )
        return int(any(marker in lowered for marker in markers))

    def _compositional_risk(self, call: ToolCall, history: list[ToolCall]) -> int:
        joined = " ".join([entry.name + " " + entry.arguments for entry in history + [call]]).lower()
        risky_sequences = (
            ("genome", "resistance", "structure"),
            ("retrieve", "synthesis", "optimize"),
            ("patient", "record", "export"),
            ("credential", "scan", "exploit"),
        )
        return int(any(all(term in joined for term in sequence) for sequence in risky_sequences))

    def _tool_invocation_risk(self, call: ToolCall) -> float:
        lowered = f"{call.name} {call.arguments}".lower()
        unsafe_terms = ("synthesis", "exploit", "credential", "private", "pathogen")
        uncertain_terms = ("optimize", "bulk", "sequence", "screen")
        if any(term in lowered for term in unsafe_terms):
            return 0.2
        if any(term in lowered for term in uncertain_terms):
            return 0.1
        return 0.0

    def _category_for_call(self, call: ToolCall) -> str:
        lowered = f"{call.name} {call.arguments}".lower()
        if "private" in lowered or "patient" in lowered:
            return "S4"
        if "credential" in lowered or "exploit" in lowered:
            return "S5"
        if "pathogen" in lowered:
            return "S2"
        if "synthesis" in lowered or "toxic" in lowered:
            return "S1"
        return ""

    def _action(self, score: float) -> str:
        if score > self.block_threshold:
            return "block"
        if score >= self.modify_threshold:
            return "modify"
        return "allow"

    def _level(self, action: str) -> RiskLevel:
        if action == "block":
            return RiskLevel.BLOCK
        if action == "modify":
            return RiskLevel.HIGH_RISK
        return RiskLevel.SAFE

    def _feedback(self, action: str, call: ToolCall) -> str:
        if action == "allow":
            return f"Allow {call.name}; no trajectory-level risk detected."
        if action == "modify":
            return (
                f"Modify {call.name}; use aggregate public data, non-sensitive examples, "
                "or a non-hazardous model workflow."
            )
        return (
            f"Block {call.name}; the call contributes to a high-risk tool trajectory. "
            "Redirect to a safe educational or synthetic-data alternative."
        )
