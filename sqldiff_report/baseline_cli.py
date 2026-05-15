"""CLI sub-commands for baseline management (save / load / list / delete)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqldiff_report.baseline_comparator import compare_against_baseline, format_comparison_text
from sqldiff_report.baseline_manager import (
    BaselineError,
    delete_baseline,
    list_baselines,
    load_baseline,
    save_baseline,
)
from sqldiff_report.diff_engine import SchemaDiff
from sqldiff_report.snapshot_loader import load_snapshot
from sqldiff_report.schema_parser import SchemaSnapshot
from sqldiff_report.diff_engine import compute_diff


def _resolve_dir(config_dir: str | None) -> Path:
    return Path(config_dir) if config_dir else Path(".sqldiff_baselines")


def cmd_save(args: argparse.Namespace) -> int:
    """Save current diff as a named baseline."""
    baseline_dir = _resolve_dir(args.baseline_dir)
    try:
        before: SchemaSnapshot = load_snapshot(args.before)
        after: SchemaSnapshot = load_snapshot(args.after)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading snapshots: {exc}", file=sys.stderr)
        return 1

    diff: SchemaDiff = compute_diff(before, after)
    entry = save_baseline(
        baseline_dir,
        args.name,
        diff,
        description=args.description or "",
        tags=args.tag or [],
    )
    print(f"Baseline '{entry.name}' saved to {baseline_dir}.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List available baselines."""
    baseline_dir = _resolve_dir(args.baseline_dir)
    names = list_baselines(baseline_dir)
    if not names:
        print("No baselines found.")
    for name in names:
        print(f"  {name}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a named baseline."""
    baseline_dir = _resolve_dir(args.baseline_dir)
    try:
        delete_baseline(baseline_dir, args.name)
        print(f"Baseline '{args.name}' deleted.")
    except BaselineError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare current diff against a saved baseline."""
    baseline_dir = _resolve_dir(args.baseline_dir)
    try:
        before: SchemaSnapshot = load_snapshot(args.before)
        after: SchemaSnapshot = load_snapshot(args.after)
        baseline = load_baseline(baseline_dir, args.name)
    except (BaselineError, Exception) as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1

    diff: SchemaDiff = compute_diff(before, after)
    cmp = compare_against_baseline(diff, baseline)
    no_colour = getattr(args, "no_color", False)
    print(format_comparison_text(cmp, colour=not no_colour))
    return 1 if cmp.has_regressions else 0


def build_baseline_parser(sub: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register baseline sub-commands onto an existing sub-parser group."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--baseline-dir", default=None)

    p_save = sub.add_parser("baseline-save", parents=[common])
    p_save.add_argument("before")
    p_save.add_argument("after")
    p_save.add_argument("name")
    p_save.add_argument("--description", default="")
    p_save.add_argument("--tag", action="append")
    p_save.set_defaults(func=cmd_save)

    p_list = sub.add_parser("baseline-list", parents=[common])
    p_list.set_defaults(func=cmd_list)

    p_del = sub.add_parser("baseline-delete", parents=[common])
    p_del.add_argument("name")
    p_del.set_defaults(func=cmd_delete)

    p_cmp = sub.add_parser("baseline-compare", parents=[common])
    p_cmp.add_argument("before")
    p_cmp.add_argument("after")
    p_cmp.add_argument("name")
    p_cmp.add_argument("--no-color", action="store_true")
    p_cmp.set_defaults(func=cmd_compare)
