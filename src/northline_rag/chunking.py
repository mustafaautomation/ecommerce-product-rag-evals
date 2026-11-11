"""Paragraph chunker. Short catalog files stay one chunk."""

from __future__ import annotations

import re
from functools import lru_cache

from northline_rag.config import MAX_CHUNK_CHARS
from northline_rag.corpus import load_corpus
from northline_rag.types import Chunk, Document

_PARAGRAPHS = re.compile(r"\n\s*\n")


def compose_chunk_text(title: str, body: str) -> str:
    return f"{title}\n{body}"


def chunk_document(
    document: Document,
    *,
    max_chars: int = MAX_CHUNK_CHARS,
    overlap_paragraphs: int = 1,
) -> tuple[Chunk, ...]:
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    paragraphs = [part.strip() for part in _PARAGRAPHS.split(document.body) if part.strip()]
    if not paragraphs:
        paragraphs = [document.body.strip()]
    groups: list[list[str]] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        addition = len(paragraph) if current_len == 0 else len(paragraph) + 2
        if current and current_len + addition > max_chars:
            groups.append(current)
            current = current[-overlap_paragraphs:] if overlap_paragraphs > 0 else []
            current_len = sum(len(part) + 2 for part in current)
            if current and current_len + len(paragraph) + 2 > max_chars:
                current = []
                current_len = 0
            addition = len(paragraph) if current_len == 0 else len(paragraph) + 2
        current.append(paragraph)
        current_len += addition
    if current:
        groups.append(current)
    chunks: list[Chunk] = []
    for index, group in enumerate(groups):
        body = "\n\n".join(group)
        chunks.append(
            Chunk(
                chunk_id=f"{document.doc_id}-{index}",
                doc_id=document.doc_id,
                title=document.title,
                body=body,
                text=compose_chunk_text(document.title, body),
            )
        )
    return tuple(chunks)


def chunk_documents(
    documents: tuple[Document, ...] | list[Document],
    *,
    max_chars: int = MAX_CHUNK_CHARS,
) -> tuple[Chunk, ...]:
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, max_chars=max_chars))
    return tuple(chunks)


@lru_cache(maxsize=1)
def load_chunks() -> tuple[Chunk, ...]:
    return chunk_documents(load_corpus())
