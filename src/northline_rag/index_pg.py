"""Build the pgvector index from the synthetic corpus."""

from __future__ import annotations

import numpy as np

from northline_rag.chunking import load_chunks
from northline_rag.embeddings import HashingEmbedder
from northline_rag.stores.pgvector_store import PgVectorStore


def main(argv: list[str] | None = None) -> int:
    del argv
    chunks = load_chunks()
    embedder = HashingEmbedder()
    vectors = embedder.embed_texts([chunk.text for chunk in chunks])
    PgVectorStore.from_env().rebuild(chunks, np.asarray(vectors, dtype=np.float32))
    print(f"Indexed {len(chunks)} chunks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
