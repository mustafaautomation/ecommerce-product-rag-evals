"""Load the synthetic Northline Supply catalog."""

from __future__ import annotations

import re
from functools import lru_cache

from northline_rag.config import repo_root
from northline_rag.types import Document

_DOC_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_document(doc_id: str, raw: str) -> Document:
    if not _DOC_ID.fullmatch(doc_id):
        raise ValueError(f"Invalid document id: {doc_id}")
    text = raw.strip()
    title = doc_id
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"{doc_id} has an unclosed front matter block")
        for line in parts[1].splitlines():
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"').strip("'")
        body = parts[2].strip()
    if not title or not body:
        raise ValueError(f"{doc_id} needs a title and a body")
    return Document(doc_id=doc_id, title=title, body=body)


@lru_cache(maxsize=1)
def load_corpus() -> tuple[Document, ...]:
    folder = repo_root() / "data" / "corpus"
    paths = sorted(folder.glob("*.md"))
    if not paths:
        raise FileNotFoundError(f"No corpus documents in {folder}")
    return tuple(parse_document(path.stem, path.read_text(encoding="utf-8")) for path in paths)
