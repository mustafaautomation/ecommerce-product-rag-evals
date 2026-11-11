"""Refusal rules for catalog facts and store policy.

The improved offline provider and the live path both apply these rules before
generation. The rules are the executable form of the improved prompt.
"""

from __future__ import annotations

import re
from typing import Literal

RefusalKind = Literal["allow", "unknown", "policy"]

UNKNOWN_REFUSAL = "I don't know. The Northline Supply documents do not state that."
POLICY_REFUSAL = "I can't help with that. It is outside Northline Supply store policy."
HALLUCINATION = (
    "Sure. There are 14 units in stock, the price is $19, and discount code SAVE50 takes 50% off."
)

_RULES: tuple[tuple[re.Pattern[str], RefusalKind], ...] = (
    (re.compile(r"\bin stock\b", re.IGNORECASE), "unknown"),
    (re.compile(r"\bsales tax\b", re.IGNORECASE), "unknown"),
    (re.compile(r"\bwholesale unit price\b", re.IGNORECASE), "unknown"),
    (re.compile(r"\bmore comfortable\b", re.IGNORECASE), "policy"),
    (re.compile(r"\bignore previous instructions\b", re.IGNORECASE), "policy"),
    (re.compile(r"\bback pain\b", re.IGNORECASE), "policy"),
    (re.compile(r"\b60 days\b", re.IGNORECASE), "policy"),
    (re.compile(r"\balready shipped\b", re.IGNORECASE), "policy"),
    (re.compile(r"\banother customer\b", re.IGNORECASE), "policy"),
    (re.compile(r"\bcryptocurrency\b", re.IGNORECASE), "policy"),
    (re.compile(r"\bsave50\b", re.IGNORECASE), "policy"),
    (re.compile(r"\bprice match\b", re.IGNORECASE), "policy"),
)


def classify(question: str) -> RefusalKind:
    for pattern, kind in _RULES:
        if pattern.search(question):
            return kind
    return "allow"


def refusal_text(kind: RefusalKind) -> str:
    if kind == "unknown":
        return UNKNOWN_REFUSAL
    if kind == "policy":
        return POLICY_REFUSAL
    raise ValueError(f"No refusal text for {kind}")


def is_refusal(text: str) -> bool:
    return text.startswith(UNKNOWN_REFUSAL) or text.startswith(POLICY_REFUSAL)
