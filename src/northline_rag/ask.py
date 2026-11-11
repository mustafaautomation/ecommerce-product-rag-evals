"""Ask the Northline Supply assistant from the shell."""

from __future__ import annotations

import argparse

from northline_rag.embeddings import HashingEmbedder
from northline_rag.pipeline import VariantName, build_assistant
from northline_rag.stores.pgvector_store import PgVectorStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask the Northline Supply assistant.")
    parser.add_argument("question")
    parser.add_argument("--store", choices=("faiss", "pg"), default="faiss")
    parser.add_argument("--provider", choices=("fake", "openai"), default="fake")
    parser.add_argument("--variant", choices=("improved", "baseline"), default="improved")
    args = parser.parse_args(argv)
    variant: VariantName = args.variant
    if args.store == "pg":
        assistant = build_assistant(
            variant,
            provider=args.provider,
            store=PgVectorStore.from_env(),
            embedder=HashingEmbedder(),
        )
    else:
        assistant = build_assistant(variant, provider=args.provider)
    result = assistant.answer(args.question)
    print(result.text)
    print("---")
    for chunk in result.chunks:
        print(chunk.doc_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
