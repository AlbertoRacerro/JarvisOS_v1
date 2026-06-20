"""Local Gemma evaluation fixtures and deterministic scoring helpers."""

from app.modules.local_ai_eval.loader import category_counts, load_golden_cases
from app.modules.local_ai_eval.models import GoldenCategory, GoldenTestCase, GemmaEvalOutput
from app.modules.local_ai_eval.scoring import EvaluationScore, score_output

__all__ = [
    "EvaluationScore",
    "GemmaEvalOutput",
    "GoldenCategory",
    "GoldenTestCase",
    "category_counts",
    "load_golden_cases",
    "score_output",
]
