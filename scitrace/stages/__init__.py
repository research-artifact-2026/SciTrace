"""
SafeScientist core workflow stages (retained).

Thinker → Experimenter → Writer → Reviewer

SciTrace wraps each stage with SIR; Experimenter additionally uses CTV when enabled.
"""

from scitrace.stages.experimenter import ExperimenterStage
from scitrace.stages.reviewer import ReviewerStage
from scitrace.stages.thinker import ThinkerStage
from scitrace.stages.writer import WriterStage

__all__ = ["ThinkerStage", "ExperimenterStage", "WriterStage", "ReviewerStage"]
