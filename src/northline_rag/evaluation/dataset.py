"""Labelled questions and threshold config."""

from __future__ import annotations

import json
from functools import lru_cache

from northline_rag.config import repo_root
from northline_rag.types import Question


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{field} must be a list of non-empty strings")
    return tuple(value)


@lru_cache(maxsize=1)
def load_questions() -> tuple[Question, ...]:
    path = repo_root() / "data" / "eval" / "questions.json"
    payload: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("questions.json must be a list")
    questions: list[Question] = []
    seen: set[str] = set()
    for row in payload:
        if not isinstance(row, dict):
            raise ValueError("each question must be an object")
        qid = row.get("id")
        question = row.get("question")
        reference = row.get("reference_answer")
        expect = row.get("expect_refusal")
        if not isinstance(qid, str) or not qid:
            raise ValueError("question id must be a string")
        if qid in seen:
            raise ValueError(f"duplicate question id {qid}")
        seen.add(qid)
        if not isinstance(question, str) or not question:
            raise ValueError(f"{qid} is missing question text")
        if not isinstance(reference, str) or not reference:
            raise ValueError(f"{qid} is missing a reference answer")
        if not isinstance(expect, bool):
            raise ValueError(f"{qid} expect_refusal must be a boolean")
        questions.append(
            Question(
                id=qid,
                question=question,
                reference_answer=reference,
                reference_doc_ids=_string_tuple(
                    row.get("reference_doc_ids"),
                    f"{qid} reference_doc_ids",
                ),
                required_strings=_string_tuple(
                    row.get("required_strings"),
                    f"{qid} required_strings",
                ),
                expect_refusal=expect,
                tags=_string_tuple(row.get("tags"), f"{qid} tags"),
            )
        )
    return tuple(questions)


def _threshold_map(value: object, name: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} thresholds must be an object")
    parsed: dict[str, float] = {}
    for key, raw in value.items():
        if not isinstance(key, str) or not isinstance(raw, (int, float)):
            raise ValueError(f"{name} threshold {key!r} is invalid")
        parsed[key] = float(raw)
    return parsed


@lru_cache(maxsize=1)
def load_thresholds() -> dict[str, dict[str, float]]:
    path = repo_root() / "data" / "thresholds.json"
    payload: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("thresholds.json must be an object")
    return {
        "offline": _threshold_map(payload.get("offline"), "offline"),
        "live": _threshold_map(payload.get("live"), "live"),
    }
