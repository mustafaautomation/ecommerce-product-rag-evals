from northline_rag.evaluation.dataset import load_thresholds
from northline_rag.evaluation.metrics import failing_metrics
from northline_rag.evaluation.runner import evaluate_variant


def test_gate_passes_improved_and_rejects_baseline() -> None:
    thresholds = load_thresholds()["offline"]
    improved = evaluate_variant("improved")
    baseline = evaluate_variant("baseline")
    assert failing_metrics(improved.metrics, thresholds) == {}
    failed = failing_metrics(baseline.metrics, thresholds)
    assert set(failed) == set(thresholds)
    for score in baseline.metrics.values():
        assert score == 0.0
