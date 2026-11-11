"""Paths and constants for the Northline Supply demo."""

from __future__ import annotations

import os
from pathlib import Path

EMBED_DIM = 256
TOP_K = 4
MAX_CHUNK_CHARS = 2500
DEFAULT_DATABASE_URL = "postgresql://northline:northline@localhost:5432/northline"

OFFLINE_METRIC_NAMES = (
    "hit_rate",
    "mrr",
    "non_llm_context_recall",
    "string_presence",
    "refusal_correctness",
)
LIVE_METRIC_NAMES = (
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
)


def repo_root() -> Path:
    """Find the checkout that holds the corpus and the eval files."""
    override = os.environ.get("NORTHLINE_ROOT")
    if override:
        return Path(override)
    start = Path(__file__).resolve()
    for candidate in (Path.cwd(), *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "data" / "corpus").is_dir():
            return candidate
    raise FileNotFoundError("Could not find the Northline Supply repo root.")


def database_url() -> str:
    return os.environ.get("NORTHLINE_DATABASE_URL", DEFAULT_DATABASE_URL)
