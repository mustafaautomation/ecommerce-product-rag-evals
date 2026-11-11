"""Assemble the offline and live assistants."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

import numpy as np

from northline_rag.chunking import load_chunks
from northline_rag.config import TOP_K
from northline_rag.embeddings import Embedder, HashingEmbedder
from northline_rag.generators import (
    FakeGenerator,
    Generator,
    OpenAIGenerator,
    UnguardedFakeGenerator,
)
from northline_rag.guardrails import classify, is_refusal, refusal_text
from northline_rag.retrieval import Retriever, VectorStore
from northline_rag.stores.faiss_store import FaissStore
from northline_rag.types import Answer, Chunk

VariantName = Literal["improved", "baseline"]
ProviderName = Literal["fake", "openai"]


@lru_cache(maxsize=1)
def faiss_resources() -> tuple[FaissStore, HashingEmbedder]:
    chunks = load_chunks()
    embedder = HashingEmbedder()
    vectors = embedder.embed_texts([chunk.text for chunk in chunks])
    return FaissStore(chunks, np.asarray(vectors, dtype=np.float32)), embedder


class Assistant:
    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        *,
        guardrails: bool,
        variant: str,
    ) -> None:
        self.retriever = retriever
        self.generator = generator
        self.guardrails = guardrails
        self.variant = variant

    def answer(self, question: str) -> Answer:
        chunks = self.retriever.retrieve(question)
        kind = classify(question)
        if self.guardrails and kind != "allow":
            text = refusal_text(kind)
        else:
            text = self.generator.generate(question, chunks)
        return Answer(question=question, text=text, refused=is_refusal(text), chunks=chunks)


def build_assistant(
    variant: VariantName = "improved",
    *,
    provider: ProviderName = "fake",
    store: VectorStore | None = None,
    embedder: Embedder | None = None,
) -> Assistant:
    if store is None or embedder is None:
        faiss_store, hashing = faiss_resources()
        if store is None:
            store = faiss_store
        if embedder is None:
            embedder = hashing
    if provider == "openai" and variant != "improved":
        raise ValueError("The OpenAI provider is only wired for the improved variant.")
    if provider == "openai":
        generator: Generator = OpenAIGenerator()
    elif variant == "baseline":
        generator = UnguardedFakeGenerator()
    else:
        generator = FakeGenerator()
    return Assistant(
        retriever=Retriever(store, embedder, invert=variant == "baseline", k=TOP_K),
        generator=generator,
        guardrails=variant == "improved",
        variant=variant,
    )


def index_chunks() -> tuple[Chunk, ...]:
    return load_chunks()
