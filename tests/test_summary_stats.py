"""Tests for summary_stats.compute_stats."""
import pytest

from sqldiff_report.diff_engine import SchemaDiff, TableDiff, ColumnDiff
from sqldiff_report.severity import Severity
from sqldiff_report.summary_stats import compute_stats


def _make_col_diff(name: str, added=False, removed=False, type_changed=False, nullable_changed=False) -> ColumnDiff:
    return ColumnDiff(
        column_name=name,
        added=added,
        removed=removed,
        old_type="int" if type_changed else None,
        new_type="text" if type_changed else None,
        old_nullable=True if nullable_changed else None,
        new_nullable=False if nullable_changed else None,
    )


def _make_added_table(name: str) -> TableDiff:
    return TableDiff(table_name=name, added=True, removed=False, column_diffs=[])


def _make_removed_table(name: str) -> TableDiff:
    return TableDiff(table_name=name, added=False, removed=True, column_diffs=[])


def _make_modified_table(name: str, col_diffs) -> TableDiff:
    return TableDiff(table_name=name, added=False, removed=False, column_diffs=col_diffs)


def test_empty_diff_gives_zero_stats():
    diff = SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[])
    stats = compute_stats(diff)
    assert stats.total_changes == 0
    assert stats.tables_added == 0
    assert stats.columns_added == 0


def test_added_table_counted():
    diff = SchemaDiff(
        added_tables=[_make_added_table("users")],
        removed_tables=[],
        modified_tables=[],
    )
    stats = compute_stats(diff)
    assert stats.tables_added == 1
    assert stats.tables_removed == 0
    assert stats.total_table_changes == 1


def test_removed_table_counted():
    diff = SchemaDiff(
        added_tables=[],
        removed_tables=[_make_removed_table("legacy")],
        modified_tables=[],
    )
    stats = compute_stats(diff)
    assert stats.tables_removed == 1


def test_column_changes_counted():
    col_diffs = [
        _make_col_diff("id", added=True),
        _make_col_diff("old_col", removed=True),
        _make_col_diff("name", type_changed=True),
    ]
    diff = SchemaDiff(
        added_tables=[],
        removed_tables=[],
        modified_tables=[_make_modified_table("orders", col_diffs)],
    )
    stats = compute_stats(diff)
    assert stats.columns_added == 1
    assert stats.columns_removed == 1
    assert stats.columns_modified == 1
    assert stats.total_column_changes == 3


def test_overall_severity_high_when_table_removed():
    diff = SchemaDiff(
        added_tables=[],
        removed_tables=[_make_removed_table("critical")],
        modified_tables=[],
    )
    stats = compute_stats(diff)
    assert stats.overall_severity == Severity.HIGH


def test_severity_counts_populated():
    diff = SchemaDiff(
        added_tables=[_make_added_table("new_tbl")],
        removed_tables=[_make_removed_table("old_tbl")],
        modified_tables=[],
    )
    stats = compute_stats(diff)
    assert Severity.HIGH in stats.severity_counts
    assert stats.severity_counts[Severity.HIGH] >= 1
