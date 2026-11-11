"""RAGAS LLM-judged metrics. This module runs only when OPENAI_API_KEY is set."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Sequence

from northline_rag.config import LIVE_METRIC_NAMES
from northline_rag.evaluation.dataset import load_questions
from northline_rag.evaluation.metrics import _mean
from northline_rag.pipeline import build_assistant
from northline_rag.types import Question


async def _judge(pairs: Sequence[tuple[Question, str, list[str]]]) -> dict[str, float]:
    from openai import AsyncOpenAI
    from ragas.embeddings.base import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics.collections import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    client = AsyncOpenAI()
    llm = llm_factory(model, client=client)
    embeddings = embedding_factory("openai", model="text-embedding-3-small", client=client)
    faithfulness = Faithfulness(llm=llm)
    relevancy = AnswerRelevancy(
        llm=llm,
        embeddings=embeddings,  # type: ignore[arg-type]
    )
    precision = ContextPrecision(llm=llm)
    recall = ContextRecall(llm=llm)
    faith_scores: list[float] = []
    relevancy_scores: list[float] = []
    precision_scores: list[float] = []
    recall_scores: list[float] = []
    for question, response, contexts in pairs:
        faith = await faithfulness.ascore(
            user_input=question.question,
            response=response,
            retrieved_contexts=contexts,
        )
        relevant = await relevancy.ascore(user_input=question.question, response=response)
        precise = await precision.ascore(
            user_input=question.question,
            reference=question.reference_answer,
            retrieved_contexts=contexts,
        )
        recalled = await recall.ascore(
            user_input=question.question,
            retrieved_contexts=contexts,
            reference=question.reference_answer,
        )
        faith_scores.append(float(faith.value))
        relevancy_scores.append(float(relevant.value))
        precision_scores.append(float(precise.value))
        recall_scores.append(float(recalled.value))
    metrics = {
        "faithfulness": _mean(faith_scores),
        "answer_relevancy": _mean(relevancy_scores),
        "context_precision": _mean(precision_scores),
        "context_recall": _mean(recall_scores),
    }
    return {name: metrics[name] for name in LIVE_METRIC_NAMES}


def run_live() -> dict[str, float]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Live judge scores were not invented.")
    assistant = build_assistant("improved", provider="openai")
    pairs: list[tuple[Question, str, list[str]]] = []
    for question in load_questions():
        answer = assistant.answer(question.question)
        pairs.append((question, answer.text, [chunk.text for chunk in answer.chunks]))
    return asyncio.run(_judge(pairs))
