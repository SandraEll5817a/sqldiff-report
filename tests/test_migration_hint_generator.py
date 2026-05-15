"""Tests for sqldiff_report.migration_hint_generator."""

import pytest
from sqldiff_report.schema_parser import ColumnDefinition, TableDefinition
from sqldiff_report.diff_engine import ColumnDiff, TableDiff, SchemaDiff
from sqldiff_report.migration_hint_generator import generate_hints, format_hints_text


def _col(name, col_type="integer", nullable=True, default=None):
    return ColumnDefinition(name=name, col_type=col_type, nullable=nullable, default=default)


def _table(name, cols=None):
    return TableDefinition(name=name, columns=cols or [])


def _empty_diff():
    return SchemaDiff(table_diffs=[])


# --- generate_hints ---

def test_generate_hints_empty_diff_returns_empty_list():
    assert generate_hints(_empty_diff()) == []


def test_generate_hints_added_table_returns_comment():
    td = TableDiff(added=_table("users"), removed=None, column_diffs=[], modified_name="users")
    diff = SchemaDiff(table_diffs=[td])
    hints = generate_hints(diff)
    assert len(hints) == 1
    assert "users" in hints[0]
    assert hints[0].startswith("--")


def test_generate_hints_removed_table_returns_drop():
    td = TableDiff(added=None, removed=_table("orders"), column_diffs=[], modified_name="orders")
    diff = SchemaDiff(table_diffs=[td])
    hints = generate_hints(diff)
    assert hints == ["DROP TABLE orders;"]


def test_generate_hints_added_column():
    col = _col("email", col_type="varchar(255)", nullable=False)
    cd = ColumnDiff(added=col, removed=None, before=None, after=None)
    td = TableDiff(added=None, removed=None, column_diffs=[cd], modified_name="users")
    diff = SchemaDiff(table_diffs=[td])
    hints = generate_hints(diff)
    assert len(hints) == 1
    assert "ADD COLUMN email varchar(255) NOT NULL" in hints[0]
    assert hints[0].startswith("ALTER TABLE users")


def test_generate_hints_added_column_with_default():
    col = _col("score", col_type="integer", nullable=True, default="0")
    cd = ColumnDiff(added=col, removed=None, before=None, after=None)
    td = TableDiff(added=None, removed=None, column_diffs=[cd], modified_name="scores")
    diff = SchemaDiff(table_diffs=[td])
    hints = generate_hints(diff)
    assert "DEFAULT 0" in hints[0]


def test_generate_hints_removed_column():
    col = _col("legacy")
    cd = ColumnDiff(added=None, removed=col, before=None, after=None)
    td = TableDiff(added=None, removed=None, column_diffs=[cd], modified_name="users")
    diff = SchemaDiff(table_diffs=[td])
    hints = generate_hints(diff)
    assert hints == ["ALTER TABLE users DROP COLUMN legacy;"]


def test_generate_hints_type_change():
    before = _col("age", col_type="smallint")
    after = _col("age", col_type="integer")
    cd = ColumnDiff(added=None, removed=None, before=before, after=after)
    td = TableDiff(added=None, removed=None, column_diffs=[cd], modified_name="people")
    diff = SchemaDiff(table_diffs=[td])
    hints = generate_hints(diff)
    assert any("TYPE integer" in h for h in hints)


def test_generate_hints_nullable_change_to_not_null():
    before = _col("name", nullable=True)
    after = _col("name", nullable=False)
    cd = ColumnDiff(added=None, removed=None, before=before, after=after)
    td = TableDiff(added=None, removed=None, column_diffs=[cd], modified_name="users")
    diff = SchemaDiff(table_diffs=[td])
    hints = generate_hints(diff)
    assert any("SET NOT NULL" in h for h in hints)


def test_generate_hints_default_dropped():
    before = _col("status", default="'active'")
    after = _col("status", default=None)
    cd = ColumnDiff(added=None, removed=None, before=before, after=after)
    td = TableDiff(added=None, removed=None, column_diffs=[cd], modified_name="accounts")
    diff = SchemaDiff(table_diffs=[td])
    hints = generate_hints(diff)
    assert any("DROP DEFAULT" in h for h in hints)


# --- format_hints_text ---

def test_format_hints_text_empty_returns_placeholder():
    result = format_hints_text([])
    assert "No migration hints" in result


def test_format_hints_text_joins_with_newlines():
    hints = ["DROP TABLE a;", "ALTER TABLE b DROP COLUMN c;"]
    result = format_hints_text(hints)
    assert "DROP TABLE a;" in result
    assert "ALTER TABLE b DROP COLUMN c;" in result
    assert result.endswith("\n")
