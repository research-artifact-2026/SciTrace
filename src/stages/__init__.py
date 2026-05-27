"""
SafeScientist core workflow stages (retained).

Thinker → Experimenter → Writer → Reviewer

SciTrace wraps each stage with SIR; Experimenter additionally uses CTV when enabled.
"""

from src.stages.experimenter import ExperimenterStage
from src.stages.reviewer import ReviewerStage
from src.stages.thinker import ThinkerStage
from src.stages.writer import WriterStage

__all__ = ["ThinkerStage", "ExperimenterStage", "WriterStage", "ReviewerStage"]
