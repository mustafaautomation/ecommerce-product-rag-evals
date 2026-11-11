import numpy as np

from northline_rag.config import EMBED_DIM
from northline_rag.stores.pgvector_store import schema_statements, vector_literal


def test_schema_uses_pgvector_cosine_index() -> None:
    statements = "\n".join(schema_statements())
    assert "CREATE EXTENSION IF NOT EXISTS vector" in statements
    assert f"vector({EMBED_DIM})" in statements
    assert "vector_cosine_ops" in statements
    assert "chunks" in statements


def test_vector_literal_is_numeric() -> None:
    rendered = vector_literal(np.array([1.0, -2.5], dtype=np.float32))
    assert rendered == "[1.00000000,-2.50000000]"
