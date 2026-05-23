"""Tests for export_writer.py."""
from __future__ import annotations

import pytest

from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff
from sqldiff_report.export_writer import ExportOptions, write_export
from pathlib import Path


@pytest.fixture
def simple_diff() -> SchemaDiff:
    return SchemaDiff(
        added_tables=[TableDiff(table_name="new_tbl", added=True, removed=False, column_diffs=[])],
        removed_tables=[],
        modified_tables=[],
    )


@pytest.fixture
def empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[])


def test_write_markdown_to_stdout(simple_diff, capsys):
    write_export(simple_diff, ExportOptions(format="markdown", output_path=None))
    out = capsys.readouterr().out
    assert "# Schema Diff Report" in out


def test_write_csv_to_stdout(simple_diff, capsys):
    write_export(simple_diff, ExportOptions(format="csv", output_path=None))
    out = capsys.readouterr().out
    assert "table,change_type" in out


def test_write_markdown_to_file(simple_diff, tmp_path):
    out_file = tmp_path / "report.md"
    write_export(simple_diff, ExportOptions(format="markdown", output_path=out_file))
    assert out_file.exists()
    content = out_file.read_text()
    assert "# Schema Diff Report" in content


def test_write_csv_to_file(simple_diff, tmp_path):
    out_file = tmp_path / "report.csv"
    write_export(simple_diff, ExportOptions(format="csv", output_path=out_file))
    assert out_file.exists()
    content = out_file.read_text()
    assert "TABLE_ADDED" in content


def test_write_creates_parent_dirs(simple_diff, tmp_path):
    out_file = tmp_path / "nested" / "deep" / "report.md"
    write_export(simple_diff, ExportOptions(format="markdown", output_path=out_file))
    assert out_file.exists()


def test_write_unknown_format_raises(simple_diff):
    with pytest.raises(ValueError, match="Unsupported export format"):
        write_export(simple_diff, ExportOptions(format="xml", output_path=None))


def test_write_empty_diff_markdown(empty_diff, capsys):
    write_export(empty_diff, ExportOptions(format="markdown", output_path=None))
    out = capsys.readouterr().out
    assert "No schema changes" in out


def test_write_empty_diff_csv(empty_diff, capsys):
    write_export(empty_diff, ExportOptions(format="csv", output_path=None))
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) == 1  # header only
