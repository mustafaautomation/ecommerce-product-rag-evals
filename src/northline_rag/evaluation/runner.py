"""Run a variant and score it."""

from __future__ import annotations

from functools import lru_cache

from northline_rag.evaluation.dataset import load_questions
from northline_rag.evaluation.metrics import score_answers
from northline_rag.evaluation.results import VariantResult
from northline_rag.pipeline import VariantName, build_assistant


@lru_cache(maxsize=2)
def evaluate_variant(variant: VariantName) -> VariantResult:
    assistant = build_assistant(variant)
    pairs = tuple((question, assistant.answer(question.question)) for question in load_questions())
    return score_answers(pairs, variant=variant)
