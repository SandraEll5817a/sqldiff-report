"""watch_cli.py – CLI entry-point for --watch mode."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from sqldiff_report.snapshot_loader import load_snapshot
from sqldiff_report.diff_engine import compute_diff
from sqldiff_report.report_formatter import format_report
from sqldiff_report.watch_mode import watch


def _build_callback(
    before_path: Path,
    after_path: Path,
    colour: bool = True,
) -> "Callable[[], None]":
    """Return a zero-argument callable that loads, diffs, and prints."""

    def _run() -> None:
        try:
            before = load_snapshot(str(before_path))
            after = load_snapshot(str(after_path))
        except Exception as exc:  # noqa: BLE001
            print(f"[watch] Error loading snapshots: {exc}", file=sys.stderr)
            return

        diff = compute_diff(before, after)
        report = format_report(diff, colour=colour)
        # Clear screen for readability
        print("\033[2J\033[H", end="")
        print(report)

    return _run


def run_watch(
    before: str,
    after: str,
    interval: float = 2.0,
    colour: bool = True,
    max_iterations: Optional[int] = None,
) -> None:
    """Start watching *before* and *after* for schema changes."""
    before_path = Path(before)
    after_path = Path(after)

    if not before_path.exists():
        print(f"[watch] Path not found: {before_path}", file=sys.stderr)
        sys.exit(1)
    if not after_path.exists():
        print(f"[watch] Path not found: {after_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[watch] Watching for changes (interval={interval}s) …  Ctrl-C to stop.")
    callback = _build_callback(before_path, after_path, colour=colour)
    try:
        watch(before_path, after_path, callback, interval=interval, max_iterations=max_iterations)
    except KeyboardInterrupt:
        print("\n[watch] Stopped.")
