"""Computes the diff between two SchemaSnapshot instances."""

from dataclasses import dataclass, field
from typing import Dict, List

from sqldiff_report.schema_parser import ColumnDefinition, SchemaSnapshot, TableDefinition


@dataclass
class ColumnDiff:
    column_name: str
    change_type: str  # 'added', 'removed', 'modified'
    old_column: ColumnDefinition = None
    new_column: ColumnDefinition = None


@dataclass
class TableDiff:
    table_name: str
    change_type: str  # 'added', 'removed', 'modified'
    column_diffs: List[ColumnDiff] = field(default_factory=list)


@dataclass
class SchemaDiff:
    table_diffs: List[TableDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.table_diffs)


def _diff_columns(
    table_name: str,
    old_table: TableDefinition,
    new_table: TableDefinition,
) -> TableDiff:
    """Produce a TableDiff for two versions of the same table."""
    table_diff = TableDiff(table_name=table_name, change_type="modified")

    old_cols = old_table.columns
    new_cols = new_table.columns

    for col_name in set(old_cols) | set(new_cols):
        if col_name not in old_cols:
            table_diff.column_diffs.append(
                ColumnDiff(
                    column_name=col_name,
                    change_type="added",
                    new_column=new_cols[col_name],
                )
            )
        elif col_name not in new_cols:
            table_diff.column_diffs.append(
                ColumnDiff(
                    column_name=col_name,
                    change_type="removed",
                    old_column=old_cols[col_name],
                )
            )
        elif old_cols[col_name] != new_cols[col_name]:
            table_diff.column_diffs.append(
                ColumnDiff(
                    column_name=col_name,
                    change_type="modified",
                    old_column=old_cols[col_name],
                    new_column=new_cols[col_name],
                )
            )

    return table_diff


def compute_diff(old: SchemaSnapshot, new: SchemaSnapshot) -> SchemaDiff:
    """Compute the full diff between two schema snapshots."""
    schema_diff = SchemaDiff()

    for table_name in set(old.tables) | set(new.tables):
        if table_name not in old.tables:
            schema_diff.table_diffs.append(
                TableDiff(table_name=table_name, change_type="added")
            )
        elif table_name not in new.tables:
            schema_diff.table_diffs.append(
                TableDiff(table_name=table_name, change_type="removed")
            )
        else:
            table_diff = _diff_columns(table_name, old.tables[table_name], new.tables[table_name])
            if table_diff.column_diffs:
                schema_diff.table_diffs.append(table_diff)

    schema_diff.table_diffs.sort(key=lambda t: t.table_name)
    return schema_diff
