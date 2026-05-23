"""CLI sub-command for schema version tagging."""
from __future__ import annotations

import argparse
import json
import sys

from sqldiff_report.snapshot_loader import load_snapshot, SnapshotLoadError
from sqldiff_report.diff_engine import compute_diff
from sqldiff_report.schema_version_tagger import suggest_next_version
from sqldiff_report.version_tag_formatter import format_version_text, format_version_dict


def build_version_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "version-tag",
        help="Suggest a semantic version bump based on schema diff",
    )
    p.add_argument("before", help="Path to the 'before' SQL file or directory")
    p.add_argument("after", help="Path to the 'after' SQL file or directory")
    p.add_argument(
        "--current-version",
        default="0.1.0",
        metavar="VERSION",
        help="Current schema version (default: 0.1.0)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--no-colour",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
    return p


def run_version_tag(args: argparse.Namespace) -> int:
    """Execute the version-tag command. Returns an exit code."""
    try:
        before_snap = load_snapshot(args.before)
        after_snap = load_snapshot(args.after)
    except SnapshotLoadError as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    diff = compute_diff(before_snap, after_snap)
    suggested = suggest_next_version(args.current_version, diff)

    if args.format == "json":
        data = format_version_dict(args.current_version, suggested)
        print(json.dumps(data, indent=2))
    else:
        use_colour = not args.no_colour
        print(format_version_text(args.current_version, suggested, use_colour=use_colour))

    # Exit 0 if no version change needed, 2 if a bump is suggested
    return 0 if suggested.label == args.current_version else 2
