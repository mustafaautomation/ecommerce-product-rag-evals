"""Token helpers shared by retrieval and the extractive generator."""

from __future__ import annotations

import re
from collections import Counter

STOPWORDS = frozenset(
    {
        "a",
        "about",
        "ago",
        "am",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "by",
        "can",
        "did",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "just",
        "me",
        "much",
        "my",
        "not",
        "now",
        "of",
        "on",
        "or",
        "our",
        "out",
        "over",
        "please",
        "say",
        "says",
        "so",
        "tell",
        "than",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "this",
        "to",
        "under",
        "up",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "whose",
        "will",
        "with",
        "you",
        "your",
    }
)

_TOKEN = re.compile(r"[a-z0-9]+")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def stem(token: str) -> str:
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in _TOKEN.findall(text.lower()):
        if len(raw) < 2 or raw in STOPWORDS:
            continue
        tokens.append(stem(raw))
    return tokens


def content_tokens(text: str) -> list[str]:
    seen: list[str] = []
    for token in tokenize(text):
        if token not in seen:
            seen.append(token)
    return seen


def token_coverage(question: str, text: str) -> float:
    """Fraction of question tokens found in text, with a small repeat bonus."""
    query = content_tokens(question)
    if not query:
        return 0.0
    counts = Counter(tokenize(text))
    hits = 0.0
    for token in query:
        count = counts[token]
        if count:
            hits += 1.0 + 0.02 * min(count, 5)
    return hits / len(query)


def hit_count(question: str, text: str) -> int:
    query = content_tokens(question)
    present = set(content_tokens(text))
    return sum(1 for token in query if token in present)


def split_sentences(text: str) -> list[str]:
    parts = _SENTENCE.split(text.strip())
    return [part.strip() for part in parts if part.strip()]
