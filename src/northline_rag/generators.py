"""Answer generators: extractive fake, unguarded fake, and OpenAI."""

from __future__ import annotations

import os
from typing import Protocol

from northline_rag.guardrails import HALLUCINATION, UNKNOWN_REFUSAL, classify
from northline_rag.prompts import IMPROVED_PROMPT
from northline_rag.text import hit_count, split_sentences, token_coverage
from northline_rag.types import Chunk


class Generator(Protocol):
    name: str

    def generate(self, question: str, chunks: tuple[Chunk, ...] | list[Chunk]) -> str: ...


def chunks_for_answer(
    question: str,
    chunks: tuple[Chunk, ...] | list[Chunk],
) -> list[Chunk]:
    if not chunks:
        return []
    scored = [(token_coverage(question, chunk.text), chunk) for chunk in chunks]
    best = max(score for score, _chunk in scored)
    if best <= 0:
        return []
    return [chunk for score, chunk in scored if score > 0 and score >= best - 0.05]


def select_sentences(
    question: str,
    chunks: tuple[Chunk, ...] | list[Chunk],
) -> list[str]:
    chosen = chunks_for_answer(question, chunks)
    selected: list[str] = []
    seen: set[str] = set()
    for chunk in chosen:
        scored = [
            (hit_count(question, sentence), sentence)
            for sentence in split_sentences(chunk.body)
            if hit_count(question, sentence) > 0
        ]
        if not scored:
            continue
        best = max(hits for hits, _sentence in scored)
        for hits, sentence in scored:
            cleaned = sentence.strip()
            if hits == best and cleaned and cleaned not in seen:
                seen.add(cleaned)
                selected.append(cleaned)
    return selected


def extractive_answer(question: str, chunks: tuple[Chunk, ...] | list[Chunk]) -> str:
    sentences = select_sentences(question, chunks)
    if not sentences:
        return UNKNOWN_REFUSAL
    return " ".join(sentences)


class FakeGenerator:
    def __init__(self) -> None:
        self.name = "fake"

    def generate(self, question: str, chunks: tuple[Chunk, ...] | list[Chunk]) -> str:
        return extractive_answer(question, chunks)


class UnguardedFakeGenerator:
    """Offline stand-in for the baseline prompt.

    Policy and unknown questions get a fixed invented stock count and discount.
    Other questions quote whatever the retriever returned.
    """

    def __init__(self) -> None:
        self.name = "unguarded-fake"

    def generate(self, question: str, chunks: tuple[Chunk, ...] | list[Chunk]) -> str:
        if classify(question) != "allow":
            return HALLUCINATION
        return extractive_answer(question, chunks)


class OpenAIGenerator:
    def __init__(self, prompt: str = IMPROVED_PROMPT, model: str | None = None) -> None:
        self.name = "openai"
        self.prompt = prompt
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, question: str, chunks: tuple[Chunk, ...] | list[Chunk]) -> str:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set")
        from openai import OpenAI

        context = "\n\n".join(f"[{chunk.doc_id}] {chunk.text}" for chunk in chunks)
        client = OpenAI()
        completion = client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": self.prompt},
                {
                    "role": "user",
                    "content": f"Documents:\n{context}\n\nQuestion: {question}",
                },
            ],
        )
        message = completion.choices[0].message.content
        return message or ""
