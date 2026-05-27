"""Pydantic output schemas for JSON validation."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SIRAssessment(BaseModel):
    """Standard SIR stage assessment output."""

    risk_level: Literal["safe", "low_risk", "warning", "high_risk", "block"]
    categories: List[str]
    justification: str
    action: Literal["proceed", "modify", "flag", "block"]


class SIRReviewerAssessment(SIRAssessment):
    """Reviewer-stage assessment with interaction escalation."""

    interaction_escalation: bool
    escalation_pairs: Optional[List[List[str]]] = None


class CTVAssessment(BaseModel):
    """CTV verification output schema."""

    request_harmful: bool
    compositional_risk: bool
    tool_safety: Literal["safe", "uncertain", "unsafe"]
    score: float = Field(ge=0.0, le=1.0)
    action: Literal["allow", "modify", "block"]


class TSFlowOutput(BaseModel):
    """TS-Flow corrective feedback output."""

    explanation: str
    safe_alternative: str
    modified_call: str


class SafetyJudgeOutput(BaseModel):
    """GPT-4o safety judge output."""

    score: float = Field(ge=1.0, le=5.0)
    justification: str


class QualityJudgeOutput(BaseModel):
    """GPT-4o quality judge output."""

    quality: float = Field(ge=1.0, le=5.0)
    clarity: float = Field(ge=1.0, le=5.0)
    overall: float = Field(ge=1.0, le=5.0)
    justification: str
