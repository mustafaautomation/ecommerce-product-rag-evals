"""Non-LLM RAGAS metrics plus refusal and retrieval checks."""

from __future__ import annotations

import asyncio
import math
import statistics
import warnings
from collections.abc import Mapping, Sequence

from northline_rag.chunking import load_chunks
from northline_rag.config import OFFLINE_METRIC_NAMES
from northline_rag.evaluation.results import QuestionScore, VariantResult
from northline_rag.types import Answer, Chunk, Question


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("cannot average an empty metric")
    return round(statistics.fmean(values), 6)


def reference_contexts(question: Question, chunks: Sequence[Chunk]) -> list[str]:
    wanted = set(question.reference_doc_ids)
    return [chunk.text for chunk in chunks if chunk.doc_id in wanted]


def retrieval_hit(
    reference_ids: Sequence[str],
    retrieved_ids: Sequence[str],
) -> tuple[float, float]:
    wanted = set(reference_ids)
    for index, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in wanted:
            return 1.0, 1.0 / index
    return 0.0, 0.0


def failing_metrics(
    metrics: Mapping[str, float],
    thresholds: Mapping[str, float],
) -> dict[str, float]:
    failed: dict[str, float] = {}
    for name, threshold in thresholds.items():
        if name not in metrics:
            raise KeyError(f"missing metric {name}")
        if metrics[name] < threshold:
            failed[name] = metrics[name]
    return failed


def aggregate(rows: Sequence[QuestionScore]) -> dict[str, float]:
    metrics = {
        "hit_rate": _mean([row.hit for row in rows]),
        "mrr": _mean([row.reciprocal_rank for row in rows]),
        "non_llm_context_recall": _mean([row.context_recall for row in rows]),
        "string_presence": _mean([row.string_presence for row in rows]),
        "refusal_correctness": _mean([row.refusal_correctness for row in rows]),
    }
    return {name: metrics[name] for name in OFFLINE_METRIC_NAMES}


async def _score_rows(
    pairs: Sequence[tuple[Question, Answer]],
    chunks: Sequence[Chunk],
) -> list[QuestionScore]:
    # ragas 0.4.3 still exposes NonLLMContextRecall from ragas.metrics.
    # The collections package does not export that class, even though the
    # deprecation warning tells callers to import it from there.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"Importing NonLLMContextRecall.*",
            category=DeprecationWarning,
        )
        from ragas.dataset_schema import SingleTurnSample
        from ragas.metrics import NonLLMContextRecall
        from ragas.metrics.collections import StringPresence

    recall_metric = NonLLMContextRecall()
    presence = StringPresence()
    scored: list[QuestionScore] = []
    for question, answer in pairs:
        contexts = reference_contexts(question, chunks)
        if not contexts:
            raise ValueError(f"{question.id} does not match any corpus chunk")
        retrieved = [chunk.text for chunk in answer.chunks]
        sample = SingleTurnSample(
            retrieved_contexts=retrieved or [" "],
            reference_contexts=contexts,
        )
        recall = float(await recall_metric.single_turn_ascore(sample))
        if math.isnan(recall):
            recall = 0.0
        present_scores: list[float] = []
        for required in question.required_strings:
            result = await presence.ascore(reference=required, response=answer.text)
            present_scores.append(float(result.value))
        presence_score = _mean(present_scores)
        retrieved_ids = tuple(chunk.doc_id for chunk in answer.chunks)
        hit, reciprocal = retrieval_hit(question.reference_doc_ids, retrieved_ids)
        refusal_correctness = 1.0 if answer.refused == question.expect_refusal else 0.0
        scored.append(
            QuestionScore(
                id=question.id,
                question=question.question,
                expect_refusal=question.expect_refusal,
                refused=answer.refused,
                hit=hit,
                reciprocal_rank=reciprocal,
                string_presence=presence_score,
                context_recall=recall,
                refusal_correctness=refusal_correctness,
                answer=answer.text,
                retrieved_doc_ids=retrieved_ids,
                retrieved_contexts=tuple(retrieved),
            )
        )
    return scored


def score_answers(pairs: Sequence[tuple[Question, Answer]], *, variant: str) -> VariantResult:
    rows = asyncio.run(_score_rows(pairs, load_chunks()))
    return VariantResult(variant=variant, questions=tuple(rows), metrics=aggregate(rows))
