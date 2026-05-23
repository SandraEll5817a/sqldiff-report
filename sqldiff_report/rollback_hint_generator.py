"""Generate rollback (undo) SQL hints for a SchemaDiff.

For each detected change the generator produces a best-effort SQL snippet
that would reverse the migration, helping reviewers understand the cost of
rolling back.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff


@dataclass
class RollbackHint:
    table: str
    description: str
    sql: str


def _column_rollback_hints(table_name: str, col_diff: ColumnDiff) -> List[RollbackHint]:
    hints: List[RollbackHint] = []
    col = col_diff.column_name

    if col_diff.added:
        hints.append(RollbackHint(
            table=table_name,
            description=f"Drop added column '{col}'",
            sql=f"ALTER TABLE {table_name} DROP COLUMN {col};",
        ))
    elif col_diff.removed:
        nullable = "" if col_diff.old_nullable else " NOT NULL"
        hints.append(RollbackHint(
            table=table_name,
            description=f"Re-add removed column '{col}'",
            sql=f"ALTER TABLE {table_name} ADD COLUMN {col} {col_diff.old_type}{nullable};",
        ))
    else:
        if col_diff.old_type and col_diff.new_type:
            hints.append(RollbackHint(
                table=table_name,
                description=f"Revert type change on '{col}' ({col_diff.new_type} -> {col_diff.old_type})",
                sql=f"ALTER TABLE {table_name} ALTER COLUMN {col} TYPE {col_diff.old_type};",
            ))
        if col_diff.old_nullable is not None and col_diff.new_nullable is not None:
            if col_diff.old_nullable:
                hints.append(RollbackHint(
                    table=table_name,
                    description=f"Revert nullable change on '{col}' (restore NULL)",
                    sql=f"ALTER TABLE {table_name} ALTER COLUMN {col} DROP NOT NULL;",
                ))
            else:
                hints.append(RollbackHint(
                    table=table_name,
                    description=f"Revert nullable change on '{col}' (restore NOT NULL)",
                    sql=f"ALTER TABLE {table_name} ALTER COLUMN {col} SET NOT NULL;",
                ))
    return hints


def _table_rollback_hints(table_diff: TableDiff) -> List[RollbackHint]:
    hints: List[RollbackHint] = []
    tname = table_diff.table_name

    if table_diff.added:
        hints.append(RollbackHint(
            table=tname,
            description=f"Drop added table '{tname}'",
            sql=f"DROP TABLE {tname};",
        ))
        return hints

    if table_diff.removed:
        col_defs = ", ".join(
            f"{c.column_name} {c.old_type}" for c in table_diff.column_diffs
        )
        hints.append(RollbackHint(
            table=tname,
            description=f"Re-create removed table '{tname}'",
            sql=f"CREATE TABLE {tname} ({col_defs});",
        ))
        return hints

    for col_diff in table_diff.column_diffs:
        hints.extend(_column_rollback_hints(tname, col_diff))

    return hints


def generate_rollback_hints(diff: SchemaDiff) -> List[RollbackHint]:
    """Return a flat list of rollback hints for every change in *diff*."""
    hints: List[RollbackHint] = []
    for table_diff in diff.table_diffs:
        hints.extend(_table_rollback_hints(table_diff))
    return hints


def format_rollback_hints_text(hints: List[RollbackHint], *, colour: bool = True) -> str:
    """Render rollback hints as a human-readable text block."""
    if not hints:
        return "No rollback hints — schema is unchanged."

    lines: List[str] = ["Rollback Hints", "=" * 40]
    current_table = None
    for hint in hints:
        if hint.table != current_table:
            current_table = hint.table
            lines.append(f"\n[{hint.table}]")
        lines.append(f"  -- {hint.description}")
        lines.append(f"  {hint.sql}")
    return "\n".join(lines)
