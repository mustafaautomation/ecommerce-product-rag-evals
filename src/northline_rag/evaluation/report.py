"""Markdown and HTML eval reports."""

from __future__ import annotations

from html import escape
from pathlib import Path

from northline_rag.config import OFFLINE_METRIC_NAMES
from northline_rag.corpus import load_corpus
from northline_rag.evaluation.dataset import load_questions
from northline_rag.evaluation.results import QuestionScore, VariantResult

_METRIC_HELP = {
    "hit_rate": "Share of questions whose labelled document was retrieved.",
    "mrr": "Mean reciprocal rank of the first labelled document.",
    "non_llm_context_recall": "RAGAS NonLLMContextRecall. Labelled source text was retrieved.",
    "string_presence": "RAGAS StringPresence. Required catalog strings appear in the answer.",
    "refusal_correctness": "Refusals match the labelled out-of-scope and in-policy questions.",
}


def _fmt(value: float) -> str:
    return f"{value:.4f}"


def _failures(result: VariantResult) -> list[QuestionScore]:
    return [
        row
        for row in result.questions
        if row.hit < 1.0
        or row.string_presence < 1.0
        or row.refusal_correctness < 1.0
        or row.context_recall < 1.0
    ]


def render_markdown(
    improved: VariantResult,
    baseline: VariantResult,
    thresholds: dict[str, float],
) -> str:
    docs = len(load_corpus())
    questions = len(load_questions())
    lines = [
        "# Northline Supply offline eval",
        "",
        "Synthetic catalog. The improved column is the guarded retriever.",
        "The baseline column is an inverted retriever plus an unguarded fake provider",
        "that invents a stock count and the discount code SAVE50 on policy questions.",
        "LLM-judged RAGAS metrics were not run for this report.",
        "",
        f"Documents: {docs}. Questions: {questions}.",
        "",
        "## Metric comparison",
        "",
        "| Metric | Baseline | Improved | Delta | Threshold | Improved gate |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for name in OFFLINE_METRIC_NAMES:
        before = baseline.metrics[name]
        after = improved.metrics[name]
        threshold = thresholds[name]
        gate = "pass" if after >= threshold else "fail"
        lines.append(
            f"| {name} | {_fmt(before)} | {_fmt(after)} | {_fmt(after - before)} | "
            f"{_fmt(threshold)} | {gate} |"
        )
    lines.extend(["", "## What the metrics check", ""])
    for name in OFFLINE_METRIC_NAMES:
        lines.append(f"- `{name}`: {_METRIC_HELP[name]}")
    for title, result in (("Improved failures", improved), ("Baseline failures", baseline)):
        lines.extend(["", f"## {title}", ""])
        failed = _failures(result)
        if not failed:
            lines.append("No per-question failures.")
            continue
        lines.append("| Id | Hit | MRR | Recall | String presence | Refusal | Question |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
        for row in failed:
            question = row.question.replace("|", "/")
            lines.append(
                f"| {row.id} | {_fmt(row.hit)} | {_fmt(row.reciprocal_rank)} | "
                f"{_fmt(row.context_recall)} | {_fmt(row.string_presence)} | "
                f"{_fmt(row.refusal_correctness)} | {question} |"
            )
    lines.append("")
    return "\n".join(lines)


def render_html(
    improved: VariantResult,
    baseline: VariantResult,
    thresholds: dict[str, float],
) -> str:
    rows: list[str] = []
    for name in OFFLINE_METRIC_NAMES:
        after = improved.metrics[name]
        before = baseline.metrics[name]
        threshold = thresholds[name]
        width = max(0, min(100, int(round(after * 100))))
        gate = "pass" if after >= threshold else "fail"
        rows.append(
            "<tr>"
            f"<td>{escape(name)}</td>"
            f"<td>{_fmt(before)}</td>"
            f"<td>{_fmt(after)}</td>"
            f"<td>{_fmt(after - before)}</td>"
            f"<td>{_fmt(threshold)}</td>"
            f"<td>{gate}</td>"
            f'<td><div class="bar" style="width:{width}%"></div></td>'
            "</tr>"
        )
    failure_blocks: list[str] = []
    for title, result in (("Improved failures", improved), ("Baseline failures", baseline)):
        failed = _failures(result)
        if not failed:
            body = "<p>No per-question failures.</p>"
        else:
            body_rows = []
            for row in failed:
                body_rows.append(
                    "<tr>"
                    f"<td>{escape(row.id)}</td>"
                    f"<td>{_fmt(row.hit)}</td>"
                    f"<td>{_fmt(row.reciprocal_rank)}</td>"
                    f"<td>{_fmt(row.context_recall)}</td>"
                    f"<td>{_fmt(row.string_presence)}</td>"
                    f"<td>{_fmt(row.refusal_correctness)}</td>"
                    f"<td>{escape(row.question)}</td>"
                    "</tr>"
                )
            body = (
                "<table><thead><tr><th>Id</th><th>Hit</th><th>MRR</th><th>Recall</th>"
                "<th>String presence</th><th>Refusal</th><th>Question</th></tr></thead>"
                f"<tbody>{''.join(body_rows)}</tbody></table>"
            )
        failure_blocks.append(f"<h2>{escape(title)}</h2>{body}")
    help_items = "".join(
        f"<li><code>{escape(name)}</code>: {escape(_METRIC_HELP[name])}</li>"
        for name in OFFLINE_METRIC_NAMES
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Northline Supply offline eval</title>
<style>
body {{ font-family: Georgia, serif; margin: 2rem auto; max-width: 960px; color: #1c1917; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{
  border-bottom: 1px solid #d6d3d1;
  text-align: left;
  padding: 0.4rem;
  vertical-align: top;
}}
td:nth-child(n+2):not(:last-child) {{ text-align: right; font-variant-numeric: tabular-nums; }}
.bar {{ background: #0f766e; height: 0.7rem; }}
code {{ font-family: ui-monospace, monospace; }}
</style>
</head>
<body>
<h1>Northline Supply offline eval</h1>
<p>Synthetic catalog. Improved is the guarded retriever. Baseline is an inverted retriever
and an unguarded fake provider. LLM-judged RAGAS metrics were not run for this report.</p>
<p>Documents: {len(load_corpus())}. Questions: {len(load_questions())}.</p>
<h2>Metric comparison</h2>
<table>
<thead><tr><th>Metric</th><th>Baseline</th><th>Improved</th><th>Delta</th><th>Threshold</th><th>Gate</th><th>Improved</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
<h2>What the metrics check</h2>
<ul>{help_items}</ul>
{"".join(failure_blocks)}
</body>
</html>
"""


def write_reports(
    improved: VariantResult,
    baseline: VariantResult,
    thresholds: dict[str, float],
    report_dir: Path,
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = report_dir / "eval_report.md"
    html_path = report_dir / "eval_report.html"
    markdown_path.write_text(render_markdown(improved, baseline, thresholds), encoding="utf-8")
    html_path.write_text(render_html(improved, baseline, thresholds), encoding="utf-8")
    return markdown_path, html_path
