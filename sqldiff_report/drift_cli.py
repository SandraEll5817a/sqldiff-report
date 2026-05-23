"""CLI sub-commands for drift detection against a saved baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqldiff_report.snapshot_loader import load_snapshot
from sqldiff_report.diff_engine import compute_diff
from sqldiff_report.baseline_manager import load_baseline, BaselineError
from sqldiff_report.drift_detector import detect_drift
from sqldiff_report.drift_formatter import format_drift_text, format_drift_dict


def build_drift_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("drift", help="Detect schema drift against a saved baseline")
    p.add_argument("before", help="Path to the before snapshot (file or directory)")
    p.add_argument("after", help="Path to the after snapshot (file or directory)")
    p.add_argument("--baseline", required=True, help="Baseline label to compare against")
    p.add_argument(
        "--baseline-dir",
        default=".sqldiff_baselines",
        help="Directory where baselines are stored (default: .sqldiff_baselines)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colour output")
    p.set_defaults(func=run_drift)


def run_drift(args: argparse.Namespace) -> int:
    try:
        before = load_snapshot(args.before)
        after = load_snapshot(args.after)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading snapshots: {exc}", file=sys.stderr)
        return 1

    diff = compute_diff(before, after)

    baseline_dir = Path(args.baseline_dir)
    try:
        entries = load_baseline(baseline_dir)
    except BaselineError as exc:
        print(f"Error loading baseline: {exc}", file=sys.stderr)
        return 1

    entry = next((e for e in entries if e.tags and e.tags.get("label") == args.baseline), None)
    if entry is None:
        print(f"Baseline '{args.baseline}' not found in {baseline_dir}", file=sys.stderr)
        return 1

    report = detect_drift(diff, entry)

    if args.format == "json":
        print(json.dumps(format_drift_dict(report), indent=2))
    else:
        colour = not args.no_color
        print(format_drift_text(report, colour=colour))

    return 1 if report.has_drift else 0
