"""Eval CLI. Offline mode is the CI gate. Live mode needs OPENAI_API_KEY."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from northline_rag.config import LIVE_METRIC_NAMES, OFFLINE_METRIC_NAMES, repo_root
from northline_rag.evaluation.dataset import load_thresholds
from northline_rag.evaluation.live import run_live
from northline_rag.evaluation.metrics import failing_metrics
from northline_rag.evaluation.report import write_reports
from northline_rag.evaluation.runner import evaluate_variant
from northline_rag.evaluation.snapshots import snapshot_mismatch, write_snapshot
from northline_rag.pipeline import VariantName


def _print_metrics(title: str, metrics: dict[str, float], names: tuple[str, ...]) -> None:
    print(title)
    for name in names:
        print(f"  {name}: {metrics[name]:.4f}")


def _offline(args: argparse.Namespace) -> int:
    variant: VariantName = args.variant
    result = evaluate_variant(variant)
    thresholds = load_thresholds()["offline"]
    if args.write_snapshot:
        write_snapshot(result)
    if args.variant == "improved" and not args.no_report:
        baseline = evaluate_variant("baseline")
        if args.write_snapshot:
            write_snapshot(baseline)
        write_reports(result, baseline, thresholds, args.report_dir)
        if not args.no_snapshot_check:
            mismatch = snapshot_mismatch(baseline)
            if mismatch:
                print(mismatch, file=sys.stderr)
                return 1
    if not args.no_snapshot_check:
        mismatch = snapshot_mismatch(result)
        if mismatch:
            print(mismatch, file=sys.stderr)
            return 1
    _print_metrics(variant, result.metrics, OFFLINE_METRIC_NAMES)
    failed = failing_metrics(result.metrics, thresholds)
    if failed:
        print("Gate failed:", file=sys.stderr)
        for name, score in failed.items():
            print(f"  {name}={score:.4f} < {thresholds[name]:.4f}", file=sys.stderr)
        return 1
    print("Gate passed.")
    return 0


def _live(args: argparse.Namespace) -> int:
    try:
        metrics = run_live()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    thresholds = load_thresholds()["live"]
    _print_metrics("live", metrics, LIVE_METRIC_NAMES)
    if not args.no_write:
        out = repo_root() / "evals" / "live" / "judge_scores.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(metrics, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote {out}")
    failed = failing_metrics(metrics, thresholds)
    if failed:
        print("Live gate failed:", file=sys.stderr)
        for name, score in failed.items():
            print(f"  {name}={score:.4f} < {thresholds[name]:.4f}", file=sys.stderr)
        return 1
    print("Live gate passed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score the Northline Supply assistant.")
    sub = parser.add_subparsers(dest="command", required=True)
    offline = sub.add_parser("offline", help="Score the deterministic provider and apply the gate.")
    offline.add_argument("--variant", choices=("improved", "baseline"), default="improved")
    offline.add_argument("--report-dir", type=Path, default=repo_root() / "docs")
    offline.add_argument("--no-report", action="store_true")
    offline.add_argument("--write-snapshot", action="store_true")
    offline.add_argument("--no-snapshot-check", action="store_true")
    live = sub.add_parser("live", help="Run RAGAS LLM metrics. Requires OPENAI_API_KEY.")
    live.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "offline":
        return _offline(args)
    if args.command == "live":
        return _live(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
