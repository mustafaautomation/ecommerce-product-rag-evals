import subprocess
import sys

from northline_rag.evaluation.cli import main
from northline_rag.generators import OpenAIGenerator


def test_offline_cli_passes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    assert main(["offline", "--report-dir", str(tmp_path)]) == 0
    assert (tmp_path / "eval_report.md").is_file()
    assert (tmp_path / "eval_report.html").is_file()


def test_baseline_cli_fails_the_gate() -> None:
    assert main(["offline", "--variant", "baseline", "--no-report"]) == 1


def test_live_cli_without_a_key_does_not_invent_scores(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(["live", "--no-write"]) == 2


def test_openai_generator_requires_a_key(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        OpenAIGenerator().generate("What is the price of the Trailwool Crewneck?", [])
    except RuntimeError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("expected a missing-key error")


def test_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "northline_rag.evaluation.cli", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "offline" in result.stdout
    assert "live" in result.stdout
