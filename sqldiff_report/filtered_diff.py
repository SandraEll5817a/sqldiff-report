"""Apply :class:`IgnoreRules` to a :class:`SchemaDiff` to produce a filtered copy."""

from __future__ import annotations

from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff
from sqldiff_report.ignore_rules import IgnoreRules


def _filter_column_diffs(
    table_name: str,
    column_diffs: list[ColumnDiff],
    rules: IgnoreRules,
) -> list[ColumnDiff]:
    return [
        cd
        for cd in column_diffs
        if not rules.should_ignore_column(table_name, cd.column_name)
    ]


def apply_ignore_rules(diff: SchemaDiff, rules: IgnoreRules) -> SchemaDiff:
    """Return a new :class:`SchemaDiff` with ignored tables/columns removed.

    Tables listed in *rules.tables* are dropped entirely.  Within surviving
    tables, columns listed in *rules.columns* are removed from every change
    bucket.  A :class:`TableDiff` that ends up with no changes at all is also
    dropped so that :py:meth:`SchemaDiff.has_changes` stays accurate.
    """
    filtered_tables: list[TableDiff] = []

    for td in diff.modified_tables:
        if rules.should_ignore_table(td.table_name):
            continue

        new_added = _filter_column_diffs(td.table_name, td.added_columns, rules)
        new_removed = _filter_column_diffs(td.table_name, td.removed_columns, rules)
        new_modified = _filter_column_diffs(td.table_name, td.modified_columns, rules)

        if not (new_added or new_removed or new_modified):
            continue

        filtered_tables.append(
            TableDiff(
                table_name=td.table_name,
                added_columns=new_added,
                removed_columns=new_removed,
                modified_columns=new_modified,
            )
        )

    added_tables = [
        t for t in diff.added_tables if not rules.should_ignore_table(t)
    ]
    removed_tables = [
        t for t in diff.removed_tables if not rules.should_ignore_table(t)
    ]

    return SchemaDiff(
        added_tables=added_tables,
        removed_tables=removed_tables,
        modified_tables=filtered_tables,
    )
