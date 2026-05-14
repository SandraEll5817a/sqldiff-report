"""Command-line interface for sqldiff-report."""

import argparse
import sys
from pathlib import Path

from sqldiff_report.schema_parser import SchemaSnapshot
from sqldiff_report.diff_engine import compute_diff
from sqldiff_report.report_formatter import format_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqldiff-report",
        description="Generate a human-readable schema diff report between two SQL snapshots.",
    )
    parser.add_argument(
        "before",
        metavar="BEFORE_SQL",
        type=Path,
        help="Path to the SQL file representing the old schema snapshot.",
    )
    parser.add_argument(
        "after",
        metavar="AFTER_SQL",
        type=Path,
        help="Path to the SQL file representing the new schema snapshot.",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="OUTPUT_FILE",
        type=Path,
        default=None,
        help="Write the report to a file instead of stdout.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color codes in the output.",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    for path in (args.before, args.after):
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            return 1

    before_sql = args.before.read_text(encoding="utf-8")
    after_sql = args.after.read_text(encoding="utf-8")

    before_snapshot = SchemaSnapshot.from_sql(before_sql)
    after_snapshot = SchemaSnapshot.from_sql(after_sql)

    diff = compute_diff(before_snapshot, after_snapshot)
    report = format_report(diff, use_color=not args.no_color)

    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)

    return 0 if not diff.has_changes() else 2


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
