"""In-memory FAISS index used by tests and the offline eval."""

from __future__ import annotations

from typing import Any

import numpy as np

from northline_rag.embeddings import FloatArray
from northline_rag.types import Chunk


class FaissStore:
    def __init__(self, chunks: tuple[Chunk, ...] | list[Chunk], vectors: FloatArray) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        if len(chunks) == 0:
            raise ValueError("FAISS store needs at least one chunk")
        import faiss

        matrix = np.ascontiguousarray(vectors, dtype=np.float32)
        index = faiss.IndexFlatIP(int(matrix.shape[1]))
        index.add(matrix)
        self.chunks = list(chunks)
        self._index: Any = index

    def cosine_scores(self, query_vector: FloatArray) -> list[tuple[Chunk, float]]:
        query = np.ascontiguousarray(query_vector, dtype=np.float32).reshape(1, -1)
        scores, ids = self._index.search(query, len(self.chunks))
        found: list[tuple[Chunk, float]] = []
        for score, idx in zip(scores[0].tolist(), ids[0].tolist(), strict=True):
            position = int(idx)
            if position < 0:
                continue
            found.append((self.chunks[position], float(score)))
        return found
