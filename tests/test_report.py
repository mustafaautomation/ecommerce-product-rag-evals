from pathlib import Path

from northline_rag.config import repo_root
from northline_rag.evaluation.dataset import load_thresholds
from northline_rag.evaluation.report import render_html, render_markdown
from northline_rag.evaluation.runner import evaluate_variant


def test_committed_report_matches_the_renderer() -> None:
    improved = evaluate_variant("improved")
    baseline = evaluate_variant("baseline")
    thresholds = load_thresholds()["offline"]
    docs = repo_root() / "docs"
    assert (docs / "eval_report.md").read_text(encoding="utf-8") == render_markdown(
        improved, baseline, thresholds
    )
    assert (docs / "eval_report.html").read_text(encoding="utf-8") == render_html(
        improved, baseline, thresholds
    )
    assert "No per-question failures." in Path(docs / "eval_report.md").read_text(encoding="utf-8")
