from pathlib import Path


def test_readme_states_the_measured_scores_and_the_data_source() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    lowered = readme.lower()
    assert "synthetic" in lowered
    assert "northline supply" in lowered
    assert "muhammad mustafa" in lowered
    assert "```mermaid" in readme
    assert "0.9419" in readme
    assert "1.0000" in readme
    assert "0.0000" in readme
    for banned in ("production-ready", "enterprise", "blazing", "respond.io"):
        assert banned not in lowered
