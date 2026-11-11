"""Shared records for documents, retrieval, and answers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    body: str


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str
    body: str


@dataclass(frozen=True)
class Question:
    id: str
    question: str
    reference_answer: str
    reference_doc_ids: tuple[str, ...]
    required_strings: tuple[str, ...]
    expect_refusal: bool
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Answer:
    question: str
    text: str
    refused: bool
    chunks: tuple[Chunk, ...]
