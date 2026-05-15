"""Tests for sqldiff_report.html_report_formatter."""
from __future__ import annotations

import pytest

from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff
from sqldiff_report.html_report_formatter import format_html_report
from sqldiff_report.schema_parser import ColumnDefinition, TableDefinition


def _col(name: str, col_type: str = "integer", nullable: bool = True) -> ColumnDefinition:
    return ColumnDefinition(name=name, col_type=col_type, nullable=nullable)


def _added_table_diff() -> TableDiff:
    tbl = TableDefinition(name="orders", columns=[_col("id", "integer", False)])
    return TableDiff(
        table_name="orders",
        old_table=None,
        new_table=tbl,
        added_columns=tbl.columns,
        removed_columns=[],
        modified_columns=[],
    )


def _removed_table_diff() -> TableDiff:
    tbl = TableDefinition(name="legacy", columns=[_col("code", "text")])
    return TableDiff(
        table_name="legacy",
        old_table=tbl,
        new_table=None,
        added_columns=[],
        removed_columns=tbl.columns,
        modified_columns=[],
    )


def _modified_table_diff() -> TableDiff:
    old_col = _col("price", "integer")
    new_col = _col("price", "numeric(10,2)")
    col_diff = ColumnDiff(column_name="price", old_column=old_col, new_column=new_col)
    tbl_old = TableDefinition(name="products", columns=[old_col])
    tbl_new = TableDefinition(name="products", columns=[new_col])
    return TableDiff(
        table_name="products",
        old_table=tbl_old,
        new_table=tbl_new,
        added_columns=[],
        removed_columns=[],
        modified_columns=[col_diff],
    )


@pytest.fixture()
def empty_diff() -> SchemaDiff:
    return SchemaDiff(table_diffs=[])


@pytest.fixture()
def rich_diff() -> SchemaDiff:
    return SchemaDiff(
        table_diffs=[_added_table_diff(), _removed_table_diff(), _modified_table_diff()]
    )


def test_returns_html_doctype(empty_diff: SchemaDiff) -> None:
    output = format_html_report(empty_diff)
    assert output.startswith("<!DOCTYPE html>")


def test_empty_diff_shows_no_changes_message(empty_diff: SchemaDiff) -> None:
    output = format_html_report(empty_diff)
    assert "No schema changes detected" in output


def test_custom_title_appears_in_output(empty_diff: SchemaDiff) -> None:
    output = format_html_report(empty_diff, title="My Custom Report")
    assert "My Custom Report" in output


def test_added_table_name_in_output(rich_diff: SchemaDiff) -> None:
    output = format_html_report(rich_diff)
    assert "orders" in output


def test_removed_table_name_in_output(rich_diff: SchemaDiff) -> None:
    output = format_html_report(rich_diff)
    assert "legacy" in output


def test_modified_column_type_change_shown(rich_diff: SchemaDiff) -> None:
    output = format_html_report(rich_diff)
    assert "price" in output
    assert "integer" in output
    assert "numeric" in output


def test_severity_badge_present(rich_diff: SchemaDiff) -> None:
    output = format_html_report(rich_diff)
    assert "badge" in output


def test_special_chars_escaped() -> None:
    tbl = TableDefinition(name="<script>", columns=[])
    td = TableDiff(
        table_name="<script>",
        old_table=None,
        new_table=tbl,
        added_columns=[],
        removed_columns=[],
        modified_columns=[],
    )
    output = format_html_report(SchemaDiff(table_diffs=[td]))
    assert "<script>" not in output
    assert "&lt;script&gt;" in output
