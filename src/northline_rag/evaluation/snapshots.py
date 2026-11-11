"""Committed offline pipeline outputs. These files are not judge scores."""

from __future__ import annotations

import json
from pathlib import Path

from northline_rag.config import repo_root
from northline_rag.evaluation.results import VariantResult

SNAPSHOT_NOTE = (
    "Outputs of the deterministic offline provider. "
    "Not RAGAS judge scores. No live judge run was recorded."
)


def snapshot_path(variant: str) -> Path:
    return repo_root() / "evals" / "snapshots" / f"{variant}.jsonl"


def snapshot_text(result: VariantResult) -> str:
    header = {
        "_snapshot": "deterministic-offline-provider",
        "judge_scores": False,
        "note": SNAPSHOT_NOTE,
        "variant": result.variant,
    }
    lines = [json.dumps(header, ensure_ascii=False, sort_keys=True)]
    for row in result.questions:
        payload = {
            "answer": row.answer,
            "id": row.id,
            "question": row.question,
            "refused": row.refused,
            "retrieved_contexts": list(row.retrieved_contexts),
            "retrieved_doc_ids": list(row.retrieved_doc_ids),
        }
        lines.append(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return "\n".join(lines) + "\n"


def write_snapshot(result: VariantResult) -> Path:
    path = snapshot_path(result.variant)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(snapshot_text(result), encoding="utf-8")
    return path


def snapshot_mismatch(result: VariantResult) -> str:
    path = snapshot_path(result.variant)
    if not path.is_file():
        return f"missing snapshot {path}"
    expected = snapshot_text(result)
    actual = path.read_text(encoding="utf-8")
    if actual == expected:
        return ""
    return f"{path} does not match the current {result.variant} pipeline output"
