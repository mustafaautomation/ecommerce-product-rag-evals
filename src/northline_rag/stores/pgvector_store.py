"""Postgres + pgvector store. Tests do not need a running database."""

from __future__ import annotations

from typing import Any

import numpy as np

from northline_rag.chunking import compose_chunk_text
from northline_rag.config import EMBED_DIM, database_url
from northline_rag.embeddings import FloatArray
from northline_rag.types import Chunk


def schema_statements(dim: int = EMBED_DIM) -> tuple[str, ...]:
    if not isinstance(dim, int) or dim < 1:
        raise ValueError("dim must be a positive integer")
    return (
        "CREATE EXTENSION IF NOT EXISTS vector",
        f"""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            embedding vector({dim})
        )
        """.strip(),
        """
        CREATE INDEX IF NOT EXISTS chunks_embedding_idx
        ON chunks USING hnsw (embedding vector_cosine_ops)
        """.strip(),
    )


def vector_literal(vector: FloatArray | np.ndarray[Any, Any]) -> str:
    values = [float(item) for item in np.asarray(vector, dtype=np.float32).tolist()]
    if any(not np.isfinite(value) for value in values):
        raise ValueError("embedding values must be finite")
    rendered = ",".join(f"{value:.8f}" for value in values)
    return f"[{rendered}]"


class PgVectorStore:
    def __init__(self, url: str | None = None, dim: int = EMBED_DIM) -> None:
        self.database_url = url or database_url()
        self.dim = dim

    @classmethod
    def from_env(cls) -> PgVectorStore:
        return cls()

    def rebuild(self, chunks: tuple[Chunk, ...] | list[Chunk], vectors: FloatArray) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        import psycopg

        try:
            connection = psycopg.connect(self.database_url, connect_timeout=3)
        except psycopg.OperationalError as exc:
            raise RuntimeError(
                "Could not connect to Postgres. Start it with `docker compose up -d` "
                "or set NORTHLINE_DATABASE_URL."
            ) from exc
        with connection:
            with connection.cursor() as cursor:
                for statement in schema_statements(self.dim):
                    cursor.execute(statement)
                cursor.execute("TRUNCATE chunks")
                for chunk, vector in zip(chunks, vectors, strict=True):
                    literal = vector_literal(np.asarray(vector, dtype=np.float32))
                    cursor.execute(
                        """
                        INSERT INTO chunks (chunk_id, doc_id, title, body, embedding)
                        VALUES (%s, %s, %s, %s, %s::vector)
                        """,
                        (chunk.chunk_id, chunk.doc_id, chunk.title, chunk.body, literal),
                    )

    def cosine_scores(self, query_vector: FloatArray) -> list[tuple[Chunk, float]]:
        import psycopg

        literal = vector_literal(query_vector)
        try:
            connection = psycopg.connect(self.database_url, connect_timeout=3)
        except psycopg.OperationalError as exc:
            raise RuntimeError(
                "Could not connect to Postgres. Start it with `docker compose up -d` "
                "or set NORTHLINE_DATABASE_URL."
            ) from exc
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT chunk_id, doc_id, title, body,
                           1 - (embedding <=> %s::vector) AS score
                    FROM chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT 1000
                    """,
                    (literal, literal),
                )
                rows = cursor.fetchall()
        if not rows:
            raise RuntimeError("The pgvector index is empty. Run northline-index-pg first.")
        found: list[tuple[Chunk, float]] = []
        for chunk_id, doc_id, title, body, score in rows:
            found.append(
                (
                    Chunk(
                        chunk_id=str(chunk_id),
                        doc_id=str(doc_id),
                        title=str(title),
                        body=str(body),
                        text=compose_chunk_text(str(title), str(body)),
                    ),
                    float(score),
                )
            )
        return found
