"""Tests for export_formats.py — Markdown and CSV renderers."""
from __future__ import annotations

import pytest

from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff
from sqldiff_report.export_formats import format_csv_report, format_markdown_report


def _col(name: str, *, added=False, removed=False,
         old_type=None, new_type=None,
         old_nullable=None, new_nullable=None) -> ColumnDiff:
    return ColumnDiff(
        column_name=name, added=added, removed=removed,
        old_type=old_type, new_type=new_type,
        old_nullable=old_nullable, new_nullable=new_nullable,
    )


def _added_table(name: str) -> TableDiff:
    return TableDiff(table_name=name, added=True, removed=False, column_diffs=[])


def _removed_table(name: str) -> TableDiff:
    return TableDiff(table_name=name, added=False, removed=True, column_diffs=[])


def _modified_table(name: str, col_diffs) -> TableDiff:
    return TableDiff(table_name=name, added=False, removed=False, column_diffs=col_diffs)


@pytest.fixture
def empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[])


@pytest.fixture
def rich_diff() -> SchemaDiff:
    return SchemaDiff(
        added_tables=[_added_table("orders")],
        removed_tables=[_removed_table("legacy")],
        modified_tables=[
            _modified_table("users", [
                _col("email", added=True, new_type="varchar(255)"),
                _col("age", removed=True, old_type="int"),
                _col("name", old_type="varchar(50)", new_type="varchar(100)"),
            ])
        ],
    )


# ── Markdown ──────────────────────────────────────────────────────────────────

def test_markdown_empty_diff_contains_no_changes(empty_diff):
    md = format_markdown_report(empty_diff)
    assert "No schema changes" in md


def test_markdown_contains_header(rich_diff):
    md = format_markdown_report(rich_diff)
    assert "# Schema Diff Report" in md


def test_markdown_added_table_present(rich_diff):
    md = format_markdown_report(rich_diff)
    assert "orders" in md
    assert "added" in md


def test_markdown_removed_table_present(rich_diff):
    md = format_markdown_report(rich_diff)
    assert "legacy" in md
    assert "removed" in md


def test_markdown_modified_table_has_column_table(rich_diff):
    md = format_markdown_report(rich_diff)
    assert "| Column |" in md
    assert "email" in md
    assert "age" in md
    assert "name" in md


def test_markdown_severity_label_present(rich_diff):
    md = format_markdown_report(rich_diff)
    assert "HIGH" in md or "MEDIUM" in md or "LOW" in md


# ── CSV ───────────────────────────────────────────────────────────────────────

def test_csv_has_header_row(rich_diff):
    csv = format_csv_report(rich_diff)
    first_line = csv.splitlines()[0]
    assert "table" in first_line
    assert "change_type" in first_line


def test_csv_added_table_row(rich_diff):
    csv = format_csv_report(rich_diff)
    assert "TABLE_ADDED" in csv
    assert "orders" in csv


def test_csv_removed_table_row(rich_diff):
    csv = format_csv_report(rich_diff)
    assert "TABLE_REMOVED" in csv
    assert "legacy" in csv


def test_csv_column_added_row(rich_diff):
    csv = format_csv_report(rich_diff)
    assert "COLUMN_ADDED" in csv
    assert "email" in csv


def test_csv_column_removed_row(rich_diff):
    csv = format_csv_report(rich_diff)
    assert "COLUMN_REMOVED" in csv
    assert "age" in csv


def test_csv_empty_diff_only_header(empty_diff):
    csv = format_csv_report(empty_diff)
    lines = [l for l in csv.splitlines() if l.strip()]
    assert len(lines) == 1  # header only
