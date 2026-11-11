from northline_rag.evaluation.runner import evaluate_variant
from northline_rag.evaluation.snapshots import snapshot_path, snapshot_text


def test_committed_snapshots_match_the_pipeline() -> None:
    for variant in ("improved", "baseline"):
        result = evaluate_variant(variant)  # type: ignore[arg-type]
        text = snapshot_path(variant).read_text(encoding="utf-8")
        assert text == snapshot_text(result)
        header = text.splitlines()[0]
        assert '"judge_scores": false' in header
        assert "faithfulness" not in text
        assert "answer_relevancy" not in text
