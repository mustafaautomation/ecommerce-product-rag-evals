"""Eval result records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionScore:
    id: str
    question: str
    expect_refusal: bool
    refused: bool
    hit: float
    reciprocal_rank: float
    string_presence: float
    context_recall: float
    refusal_correctness: float
    answer: str
    retrieved_doc_ids: tuple[str, ...]
    retrieved_contexts: tuple[str, ...]


@dataclass(frozen=True)
class VariantResult:
    variant: str
    questions: tuple[QuestionScore, ...]
    metrics: dict[str, float]
