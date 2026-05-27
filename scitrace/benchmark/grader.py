"""Local grading wrapper around SciSafetyEvaluator."""

from __future__ import annotations

from scitrace.benchmark.evaluator import SciSafetyEvaluator


class PromptGrader:
    """Grades saved pipeline outputs with GPT-4o judge prompts (Figure 17)."""

    def __init__(
        self,
        evaluator: SciSafetyEvaluator | None = None,
        evaluation_config: dict | None = None,
    ) -> None:
        eval_cfg = evaluation_config or {}
        judge_model = eval_cfg.get("judge_model", "gpt-4o")
        judge_kwargs = {
            k: eval_cfg[k]
            for k in ("temperature", "max_tokens")
            if k in eval_cfg
        }
        self.evaluator = evaluator or SciSafetyEvaluator(
            judge_model=judge_model,
            judge_config=judge_kwargs,
        )

    def grade_output(self, pipeline_output: dict) -> dict:
        text = (
            pipeline_output.get("final_paper")
            or pipeline_output.get("reviewer_output", {}).get("review")
            or pipeline_output.get("writer_output", {}).get("draft")
            or ""
        )
        safety = self.evaluator.score_safety(text)
        quality = self.evaluator.score_quality(text)
        return {
            "task_id": pipeline_output.get("task_id"),
            "safety_score": safety["score"],
            "quality": quality["quality"],
            "clarity": quality["clarity"],
            "overall": quality["overall"],
            "rejected": self.evaluator.is_rejected(pipeline_output),
            "justifications": {
                "safety": safety.get("justification", ""),
                "quality": quality.get("justification", ""),
            },
        }
