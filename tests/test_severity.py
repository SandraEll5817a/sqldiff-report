"""Tests for severity classification and filtering."""

import pytest
from sqldiff_report.schema_parser import ColumnDefinition
from sqldiff_report.diff_engine import ColumnDiff, TableDiff, SchemaDiff
from sqldiff_report.severity import (
    Severity,
    column_diff_severity,
    table_diff_severity,
    schema_diff_severity,
)
from sqldiff_report.severity_filter import filter_by_severity
from sqldiff_report.severity_badge import severity_badge, badge_for_table


_COL_A = ColumnDefinition(name="id", col_type="INT", nullable=False, default=None)
_COL_B = ColumnDefinition(name="id", col_type="BIGINT", nullable=False, default=None)
_COL_C = ColumnDefinition(name="id", col_type="INT", nullable=True, default=None)


def test_column_diff_severity_added():
    diff = ColumnDiff(column_name="x", old_column=None, new_column=_COL_A)
    assert column_diff_severity(diff) == Severity.LOW


def test_column_diff_severity_removed():
    diff = ColumnDiff(column_name="x", old_column=_COL_A, new_column=None)
    assert column_diff_severity(diff) == Severity.HIGH


def test_column_diff_severity_type_changed():
    diff = ColumnDiff(column_name="id", old_column=_COL_A, new_column=_COL_B)
    assert column_diff_severity(diff) == Severity.HIGH


def test_column_diff_severity_nullable_changed():
    diff = ColumnDiff(column_name="id", old_column=_COL_A, new_column=_COL_C)
    assert column_diff_severity(diff) == Severity.MEDIUM


def test_table_diff_severity_added_table():
    td = TableDiff(table_name="users", added=True, removed=False, column_diffs=[])
    assert table_diff_severity(td) == Severity.HIGH


def test_table_diff_severity_uses_highest_column():
    col_low = ColumnDiff(column_name="x", old_column=None, new_column=_COL_A)
    col_high = ColumnDiff(column_name="y", old_column=_COL_A, new_column=None)
    td = TableDiff(table_name="t", added=False, removed=False, column_diffs=[col_low, col_high])
    assert table_diff_severity(td) == Severity.HIGH


def test_schema_diff_severity_empty():
    assert schema_diff_severity(SchemaDiff(table_diffs=[])) == Severity.LOW


def test_filter_by_severity_removes_low():
    col_low = ColumnDiff(column_name="x", old_column=None, new_column=_COL_A)
    col_high = ColumnDiff(column_name="y", old_column=_COL_A, new_column=None)
    td = TableDiff(table_name="t", added=False, removed=False, column_diffs=[col_low, col_high])
    result = filter_by_severity(SchemaDiff(table_diffs=[td]), Severity.HIGH)
    assert len(result.table_diffs) == 1
    assert len(result.table_diffs[0].column_diffs) == 1
    assert result.table_diffs[0].column_diffs[0].column_name == "y"


def test_filter_by_severity_keeps_added_table():
    td = TableDiff(table_name="new_tbl", added=True, removed=False, column_diffs=[])
    result = filter_by_severity(SchemaDiff(table_diffs=[td]), Severity.HIGH)
    assert len(result.table_diffs) == 1


def test_severity_badge_no_colour():
    assert severity_badge(Severity.HIGH, colour=False) == "[HIGH]"
    assert severity_badge(Severity.MEDIUM, colour=False) == "[MEDIUM]"
    assert severity_badge(Severity.LOW, colour=False) == "[LOW]"


def test_badge_for_table_contains_name():
    line = badge_for_table("orders", Severity.MEDIUM, colour=False)
    assert "orders" in line
    assert "[MEDIUM]" in line
