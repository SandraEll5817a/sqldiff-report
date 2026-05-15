"""Tests for sqldiff_report.change_log_formatter."""

from __future__ import annotations

import pytest

from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff
from sqldiff_report.change_log_formatter import format_change_log


def _added_table() -> TableDiff:
    return TableDiff(table_name="orders", added=True, removed=False, column_diffs=[])


def _removed_table() -> TableDiff:
    return TableDiff(table_name="legacy", added=False, removed=True, column_diffs=[])


def _modified_table() -> TableDiff:
    col_diffs = [
        ColumnDiff(
            column_name="email",
            added=True,
            removed=False,
            old_type=None,
            new_type="varchar(255)",
            old_nullable=None,
            new_nullable=True,
        ),
        ColumnDiff(
            column_name="age",
            added=False,
            removed=False,
            old_type="int",
            new_type="bigint",
            old_nullable=False,
            new_nullable=False,
        ),
    ]
    return TableDiff(
        table_name="users", added=False, removed=False, column_diffs=col_diffs
    )


def test_no_changes_returns_placeholder():
    diff = SchemaDiff(table_diffs=[])
    result = format_change_log(diff, colour=False)
    assert "No schema changes" in result


def test_added_table_appears_in_log():
    diff = SchemaDiff(table_diffs=[_added_table()])
    result = format_change_log(diff, colour=False)
    assert "CREATE TABLE orders" in result


def test_removed_table_appears_in_log():
    diff = SchemaDiff(table_diffs=[_removed_table()])
    result = format_change_log(diff, colour=False)
    assert "DROP TABLE legacy" in result


def test_modified_table_shows_alter():
    diff = SchemaDiff(table_diffs=[_modified_table()])
    result = format_change_log(diff, colour=False)
    assert "ALTER TABLE users" in result


def test_added_column_shown():
    diff = SchemaDiff(table_diffs=[_modified_table()])
    result = format_change_log(diff, colour=False)
    assert "ADD COLUMN users.email" in result


def test_type_change_shown():
    diff = SchemaDiff(table_diffs=[_modified_table()])
    result = format_change_log(diff, colour=False)
    assert "users.age" in result
    assert "'int'" in result
    assert "'bigint'" in result


def test_severity_label_present_no_colour():
    diff = SchemaDiff(table_diffs=[_removed_table()])
    result = format_change_log(diff, colour=False)
    assert "[HIGH]" in result


def test_colour_output_contains_ansi():
    diff = SchemaDiff(table_diffs=[_added_table()])
    result = format_change_log(diff, colour=True)
    assert "\033[" in result


def test_no_colour_has_no_ansi():
    diff = SchemaDiff(table_diffs=[_added_table()])
    result = format_change_log(diff, colour=False)
    assert "\033[" not in result


def test_header_present():
    diff = SchemaDiff(table_diffs=[_added_table()])
    result = format_change_log(diff, colour=False)
    assert "Schema Change Log" in result
