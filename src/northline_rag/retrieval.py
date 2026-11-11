"""Blend FAISS or pgvector cosine with token coverage."""

from __future__ import annotations

from typing import Protocol

from northline_rag.config import TOP_K
from northline_rag.embeddings import Embedder, FloatArray
from northline_rag.text import token_coverage
from northline_rag.types import Chunk


class VectorStore(Protocol):
    def cosine_scores(self, query_vector: FloatArray) -> list[tuple[Chunk, float]]: ...


class Retriever:
    def __init__(
        self,
        store: VectorStore,
        embedder: Embedder,
        *,
        invert: bool = False,
        k: int = TOP_K,
    ) -> None:
        if k < 1:
            raise ValueError("k must be positive")
        self.store = store
        self.embedder = embedder
        self.invert = invert
        self.k = k

    def ranked(self, question: str) -> list[tuple[float, Chunk]]:
        query = self.embedder.embed_query(question)
        blended: list[tuple[float, Chunk]] = []
        for chunk, cosine in self.store.cosine_scores(query):
            score = float(cosine) + token_coverage(question, chunk.text)
            if self.invert:
                score = -score
            blended.append((score, chunk))
        blended.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return blended

    def retrieve(self, question: str) -> tuple[Chunk, ...]:
        return tuple(chunk for _, chunk in self.ranked(question)[: self.k])
