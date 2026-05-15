"""Assigns severity levels to schema diff changes."""

from enum import Enum
from sqldiff_report.diff_engine import SchemaDiff, TableDiff, ColumnDiff


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Severity rules for column-level changes
_COLUMN_SEVERITY_MAP = {
    "type_changed": Severity.HIGH,
    "removed": Severity.HIGH,
    "added": Severity.LOW,
    "nullable_changed": Severity.MEDIUM,
    "default_changed": Severity.LOW,
}


def column_diff_severity(col_diff: ColumnDiff) -> Severity:
    """Return the severity for a single column diff."""
    if col_diff.old_column is None:
        return _COLUMN_SEVERITY_MAP["added"]
    if col_diff.new_column is None:
        return _COLUMN_SEVERITY_MAP["removed"]
    if col_diff.old_column.col_type != col_diff.new_column.col_type:
        return _COLUMN_SEVERITY_MAP["type_changed"]
    if col_diff.old_column.nullable != col_diff.new_column.nullable:
        return _COLUMN_SEVERITY_MAP["nullable_changed"]
    return _COLUMN_SEVERITY_MAP["default_changed"]


def table_diff_severity(table_diff: TableDiff) -> Severity:
    """Return the highest severity among all changes in a table diff."""
    if table_diff.added or table_diff.removed:
        return Severity.HIGH
    levels = [column_diff_severity(c) for c in table_diff.column_diffs]
    if not levels:
        return Severity.LOW
    order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH]
    return max(levels, key=lambda s: order.index(s))


def schema_diff_severity(diff: SchemaDiff) -> Severity:
    """Return the highest severity across the entire schema diff."""
    if not diff.table_diffs:
        return Severity.LOW
    order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH]
    return max(
        (table_diff_severity(t) for t in diff.table_diffs),
        key=lambda s: order.index(s),
    )
