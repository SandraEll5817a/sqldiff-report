"""CLI sub-command: ``sqldiff-report stats`` — print diff statistics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from sqldiff_report.snapshot_loader import load_snapshot, SnapshotLoadError
from sqldiff_report.diff_engine import compute_diff
from sqldiff_report.diff_stats_exporter import export_stats, OutputFormat


def build_stats_parser(subparsers: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the *stats* sub-command onto *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "stats",
        help="Print machine-readable diff statistics between two schema snapshots.",
    )
    parser.add_argument("before", metavar="BEFORE", help="Path to the 'before' SQL file or directory.")
    parser.add_argument("after", metavar="AFTER", help="Path to the 'after' SQL file or directory.")
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["json", "csv", "tsv"],
        default="json",
        help="Output format for the statistics (default: json).",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        default=None,
        help="Write statistics to FILE instead of stdout.",
    )
    return parser


def run_stats(args: argparse.Namespace) -> int:
    """Execute the *stats* sub-command; return an exit code."""
    try:
        before_snapshot = load_snapshot(args.before)
        after_snapshot = load_snapshot(args.after)
    except SnapshotLoadError as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    diff = compute_diff(before_snapshot, after_snapshot)
    fmt: OutputFormat = args.fmt  # type: ignore[assignment]
    output = export_stats(diff, fmt=fmt)

    if args.output:
        try:
            Path(args.output).write_text(output, encoding="utf-8")
        except OSError as exc:
            print(f"Error writing output file: {exc}", file=sys.stderr)
            return 1
    else:
        print(output, end="")

    return 0
