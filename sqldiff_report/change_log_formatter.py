"""Formats a SchemaDiff into a chronological change-log style text report."""

from __future__ import annotations

from typing import List

from sqldiff_report.diff_engine import SchemaDiff, TableDiff, ColumnDiff
from sqldiff_report.severity import (
    Severity,
    column_diff_severity,
    table_diff_severity,
)

_SEVERITY_LABEL: dict[Severity, str] = {
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MEDIUM",
    Severity.LOW: "LOW",
}


def _severity_prefix(severity: Severity, colour: bool) -> str:
    label = _SEVERITY_LABEL[severity]
    if not colour:
        return f"[{label}]"
    colours = {
        Severity.HIGH: "\033[31m",
        Severity.MEDIUM: "\033[33m",
        Severity.LOW: "\033[32m",
    }
    reset = "\033[0m"
    return f"{colours[severity]}[{label}]{reset}"


def _column_diff_lines(table: str, diff: ColumnDiff, colour: bool) -> List[str]:
    sev = column_diff_severity(diff)
    prefix = _severity_prefix(sev, colour)
    lines: List[str] = []
    if diff.added:
        lines.append(f"  {prefix} ADD COLUMN {table}.{diff.column_name}")
    elif diff.removed:
        lines.append(f"  {prefix} DROP COLUMN {table}.{diff.column_name}")
    else:
        if diff.old_type != diff.new_type:
            lines.append(
                f"  {prefix} ALTER COLUMN {table}.{diff.column_name}"
                f" TYPE {diff.old_type!r} -> {diff.new_type!r}"
            )
        if diff.old_nullable != diff.new_nullable:
            nullable_str = "NULL" if diff.new_nullable else "NOT NULL"
            lines.append(
                f"  {prefix} ALTER COLUMN {table}.{diff.column_name}"
                f" SET {nullable_str}"
            )
    return lines


def _table_diff_lines(diff: TableDiff, colour: bool) -> List[str]:
    sev = table_diff_severity(diff)
    prefix = _severity_prefix(sev, colour)
    lines: List[str] = []
    if diff.added:
        lines.append(f"{prefix} CREATE TABLE {diff.table_name}")
    elif diff.removed:
        lines.append(f"{prefix} DROP TABLE {diff.table_name}")
    else:
        lines.append(f"{prefix} ALTER TABLE {diff.table_name}")
        for col_diff in diff.column_diffs:
            lines.extend(_column_diff_lines(diff.table_name, col_diff, colour))
    return lines


def format_change_log(diff: SchemaDiff, colour: bool = True) -> str:
    """Return a human-readable change-log string for *diff*."""
    if not diff.has_changes():
        return "-- No schema changes detected --\n"

    lines: List[str] = ["Schema Change Log", "=" * 40]
    for table_diff in diff.table_diffs:
        lines.extend(_table_diff_lines(table_diff, colour))
    lines.append("")
    return "\n".join(lines)
