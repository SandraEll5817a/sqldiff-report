"""Tests for rollback_hint_generator and rollback_writer."""
from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest

from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff
from sqldiff_report.rollback_hint_generator import (
    format_rollback_hints_text,
    generate_rollback_hints,
)
from sqldiff_report.rollback_writer import RollbackWriteOptions, write_rollback_hints


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _col(name: str, *, added=False, removed=False,
         old_type=None, new_type=None,
         old_nullable=None, new_nullable=None) -> ColumnDiff:
    return ColumnDiff(
        column_name=name,
        added=added,
        removed=removed,
        old_type=old_type,
        new_type=new_type,
        old_nullable=old_nullable,
        new_nullable=new_nullable,
    )


def _added_table(name: str) -> TableDiff:
    return TableDiff(table_name=name, added=True, removed=False, column_diffs=[])


def _removed_table(name: str) -> TableDiff:
    cols = [_col("id", removed=True, old_type="integer", old_nullable=False)]
    return TableDiff(table_name=name, added=False, removed=True, column_diffs=cols)


def _modified_table(name: str) -> TableDiff:
    cols = [
        _col("email", added=True, old_type=None, new_type="varchar(255)"),
        _col("age", old_type="int", new_type="bigint"),
        _col("active", old_nullable=False, new_nullable=True),
    ]
    return TableDiff(table_name=name, added=False, removed=False, column_diffs=cols)


@pytest.fixture
def empty_diff() -> SchemaDiff:
    return SchemaDiff(table_diffs=[])


@pytest.fixture
def rich_diff() -> SchemaDiff:
    return SchemaDiff(table_diffs=[
        _added_table("orders"),
        _removed_table("legacy_log"),
        _modified_table("users"),
    ])


# ---------------------------------------------------------------------------
# generate_rollback_hints
# ---------------------------------------------------------------------------

def test_empty_diff_returns_no_hints(empty_diff):
    assert generate_rollback_hints(empty_diff) == []


def test_added_table_hint_is_drop(rich_diff):
    hints = generate_rollback_hints(rich_diff)
    orders_hints = [h for h in hints if h.table == "orders"]
    assert len(orders_hints) == 1
    assert "DROP TABLE" in orders_hints[0].sql
    assert "orders" in orders_hints[0].sql


def test_removed_table_hint_is_create(rich_diff):
    hints = generate_rollback_hints(rich_diff)
    legacy_hints = [h for h in hints if h.table == "legacy_log"]
    assert len(legacy_hints) == 1
    assert "CREATE TABLE" in legacy_hints[0].sql


def test_added_column_hint_is_drop_column(rich_diff):
    hints = generate_rollback_hints(rich_diff)
    email_hints = [h for h in hints if "email" in h.sql]
    assert any("DROP COLUMN" in h.sql for h in email_hints)


def test_type_change_hint_contains_old_type(rich_diff):
    hints = generate_rollback_hints(rich_diff)
    age_hints = [h for h in hints if "age" in h.sql]
    assert any("int" in h.sql for h in age_hints)


def test_nullable_change_hint_drop_not_null(rich_diff):
    hints = generate_rollback_hints(rich_diff)
    active_hints = [h for h in hints if "active" in h.sql]
    assert any("SET NOT NULL" in h.sql for h in active_hints)


# ---------------------------------------------------------------------------
# format_rollback_hints_text
# ---------------------------------------------------------------------------

def test_format_empty_returns_placeholder():
    text = format_rollback_hints_text([])
    assert "unchanged" in text.lower() or "no rollback" in text.lower()


def test_format_text_contains_table_name(rich_diff):
    hints = generate_rollback_hints(rich_diff)
    text = format_rollback_hints_text(hints, colour=False)
    assert "users" in text
    assert "orders" in text


def test_format_text_contains_sql(rich_diff):
    hints = generate_rollback_hints(rich_diff)
    text = format_rollback_hints_text(hints, colour=False)
    assert "DROP TABLE" in text or "CREATE TABLE" in text


# ---------------------------------------------------------------------------
# write_rollback_hints
# ---------------------------------------------------------------------------

def test_write_json_to_file(tmp_path, rich_diff):
    out = tmp_path / "rollback.json"
    opts = RollbackWriteOptions(fmt="json", output_path=out, colour=False)
    write_rollback_hints(rich_diff, opts)
    data = json.loads(out.read_text())
    assert "rollback_hints" in data
    assert len(data["rollback_hints"]) > 0


def test_write_text_to_file(tmp_path, rich_diff):
    out = tmp_path / "rollback.txt"
    opts = RollbackWriteOptions(fmt="text", output_path=out, colour=False)
    write_rollback_hints(rich_diff, opts)
    content = out.read_text()
    assert "Rollback Hints" in content


def test_write_json_stdout_no_error(capsys, rich_diff):
    opts = RollbackWriteOptions(fmt="json", colour=False)
    write_rollback_hints(rich_diff, opts)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data["rollback_hints"], list)


def test_write_empty_diff_text(capsys, empty_diff):
    opts = RollbackWriteOptions(fmt="text", colour=False)
    write_rollback_hints(empty_diff, opts)
    captured = capsys.readouterr()
    assert "unchanged" in captured.out.lower() or "no rollback" in captured.out.lower()
