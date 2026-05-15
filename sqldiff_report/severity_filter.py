"""Filter a SchemaDiff to include only changes at or above a minimum severity."""

from dataclasses import replace
from sqldiff_report.diff_engine import SchemaDiff, TableDiff
from sqldiff_report.severity import Severity, column_diff_severity, table_diff_severity


def _severity_order(s: Severity) -> int:
    return [Severity.LOW, Severity.MEDIUM, Severity.HIGH].index(s)


def filter_by_severity(diff: SchemaDiff, min_severity: Severity) -> SchemaDiff:
    """Return a new SchemaDiff containing only changes at or above *min_severity*."""
    min_order = _severity_order(min_severity)
    filtered: list[TableDiff] = []

    for td in diff.table_diffs:
        # Always keep whole-table adds/removes if they meet the threshold
        if td.added or td.removed:
            if _severity_order(table_diff_severity(td)) >= min_order:
                filtered.append(td)
            continue

        # For modified tables, filter individual column diffs
        kept_cols = [
            c
            for c in td.column_diffs
            if _severity_order(column_diff_severity(c)) >= min_order
        ]
        if kept_cols:
            filtered.append(
                TableDiff(
                    table_name=td.table_name,
                    added=td.added,
                    removed=td.removed,
                    column_diffs=kept_cols,
                )
            )

    return SchemaDiff(table_diffs=filtered)
