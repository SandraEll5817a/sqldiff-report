"""Generates SQL migration hints (ALTER TABLE statements) from a SchemaDiff."""

from typing import List
from sqldiff_report.diff_engine import SchemaDiff, TableDiff, ColumnDiff


def _column_diff_hint(table_name: str, col_diff: ColumnDiff) -> str:
    """Return a single ALTER TABLE statement for a column-level change."""
    if col_diff.added:
        col = col_diff.added
        nullable = "" if col.nullable else " NOT NULL"
        default = f" DEFAULT {col.default}" if col.default else ""
        return (
            f"ALTER TABLE {table_name}"
            f" ADD COLUMN {col.name} {col.col_type}{nullable}{default};"
        )
    if col_diff.removed:
        return f"ALTER TABLE {table_name} DROP COLUMN {col_diff.removed.name};"
    # modified
    before = col_diff.before
    after = col_diff.after
    hints: List[str] = []
    if before.col_type != after.col_type:
        hints.append(
            f"ALTER TABLE {table_name}"
            f" ALTER COLUMN {after.name} TYPE {after.col_type};"
        )
    if before.nullable != after.nullable:
        if after.nullable:
            hints.append(
                f"ALTER TABLE {table_name}"
                f" ALTER COLUMN {after.name} DROP NOT NULL;"
            )
        else:
            hints.append(
                f"ALTER TABLE {table_name}"
                f" ALTER COLUMN {after.name} SET NOT NULL;"
            )
    if before.default != after.default:
        if after.default is None:
            hints.append(
                f"ALTER TABLE {table_name}"
                f" ALTER COLUMN {after.name} DROP DEFAULT;"
            )
        else:
            hints.append(
                f"ALTER TABLE {table_name}"
                f" ALTER COLUMN {after.name} SET DEFAULT {after.default};"
            )
    return "\n".join(hints)


def _table_diff_hints(table_diff: TableDiff) -> List[str]:
    """Return migration hint lines for a single TableDiff."""
    hints: List[str] = []
    if table_diff.added:
        hints.append(f"-- Table '{table_diff.added.name}' was added (manual CREATE TABLE required).")
        return hints
    if table_diff.removed:
        hints.append(f"DROP TABLE {table_diff.removed.name};")
        return hints
    table_name = table_diff.modified_name
    for col_diff in table_diff.column_diffs:
        line = _column_diff_hint(table_name, col_diff)
        if line:
            hints.append(line)
    return hints


def generate_hints(diff: SchemaDiff) -> List[str]:
    """Return a list of SQL migration hint strings for the entire diff."""
    hints: List[str] = []
    for table_diff in diff.table_diffs:
        hints.extend(_table_diff_hints(table_diff))
    return hints


def format_hints_text(hints: List[str]) -> str:
    """Format migration hints as a plain-text block."""
    if not hints:
        return "-- No migration hints generated.\n"
    return "\n".join(hints) + "\n"
