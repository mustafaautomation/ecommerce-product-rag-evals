"""Deterministic hashing embedder, plus an optional OpenAI embedder."""

from __future__ import annotations

import hashlib
import os
from typing import Any, Protocol

import numpy as np

from northline_rag.config import EMBED_DIM
from northline_rag.text import tokenize

FloatArray = np.ndarray[Any, np.dtype[np.float32]]


class Embedder(Protocol):
    dim: int

    def embed_query(self, text: str) -> FloatArray: ...

    def embed_texts(self, texts: list[str] | tuple[str, ...]) -> FloatArray: ...


def _normalize(vector: FloatArray) -> FloatArray:
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return vector
    scaled = vector / np.float32(norm)
    return np.asarray(scaled, dtype=np.float32)


class HashingEmbedder:
    """Signed hashing trick over tokens and bigrams. No network and no model download."""

    def __init__(self, dim: int = EMBED_DIM) -> None:
        if dim < 8:
            raise ValueError("dim must be at least 8")
        self.dim = dim

    def embed_query(self, text: str) -> FloatArray:
        vector = np.zeros(self.dim, dtype=np.float32)
        tokens = tokenize(text)
        grams = list(tokens)
        grams.extend(f"{left}_{right}" for left, right in zip(tokens, tokens[1:], strict=False))
        for gram in grams:
            digest = hashlib.sha256(gram.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.dim
            sign = np.float32(1.0 if digest[4] % 2 == 0 else -1.0)
            vector[index] += sign
        return _normalize(vector)

    def embed_texts(self, texts: list[str] | tuple[str, ...]) -> FloatArray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        rows = [self.embed_query(text) for text in texts]
        stacked = np.vstack(rows)
        return np.asarray(stacked, dtype=np.float32)


class OpenAIEmbedder:
    """Live embeddings. Offline evals keep using HashingEmbedder so they stay deterministic."""

    def __init__(self, model: str = "text-embedding-3-small", dim: int = EMBED_DIM) -> None:
        self.model = model
        self.dim = dim

    def embed_query(self, text: str) -> FloatArray:
        rows = self.embed_texts([text])
        return np.asarray(rows[0], dtype=np.float32)

    def embed_texts(self, texts: list[str] | tuple[str, ...]) -> FloatArray:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set")
        from openai import OpenAI

        client = OpenAI()
        response = client.embeddings.create(model=self.model, input=list(texts))
        ordered = sorted(response.data, key=lambda item: item.index)
        matrix = np.asarray([item.embedding[: self.dim] for item in ordered], dtype=np.float32)
        return np.vstack([_normalize(np.asarray(row, dtype=np.float32)) for row in matrix])
