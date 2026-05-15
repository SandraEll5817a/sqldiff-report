"""Tests for sqldiff_report.output_writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqldiff_report.diff_engine import SchemaDiff, TableDiff, ColumnDiff
from sqldiff_report.output_writer import WriteOptions, write_report
from sqldiff_report.schema_parser import ColumnDefinition, TableDefinition


@pytest.fixture()
def empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[])


@pytest.fixture()
def simple_diff() -> SchemaDiff:
    col = ColumnDefinition(name="id", col_type="INTEGER", nullable=False, default=None)
    added_table = TableDefinition(name="users", columns=[col])
    return SchemaDiff(added_tables=[added_table], removed_tables=[], modified_tables=[])


def test_write_text_to_stdout(capsys, simple_diff):
    options = WriteOptions(output_format="text")
    write_report(simple_diff, options)
    captured = capsys.readouterr()
    assert "users" in captured.out


def test_write_json_to_stdout(capsys, simple_diff):
    options = WriteOptions(output_format="json")
    write_report(simple_diff, options)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["added_tables"][0]["name"] == "users"


def test_write_text_to_file(tmp_path, simple_diff):
    out_file = tmp_path / "report.txt"
    options = WriteOptions(output_path=out_file, output_format="text")
    write_report(simple_diff, options)
    content = out_file.read_text(encoding="utf-8")
    assert "users" in content


def test_write_json_to_file(tmp_path, simple_diff):
    out_file = tmp_path / "report.json"
    options = WriteOptions(output_path=out_file, output_format="json")
    write_report(simple_diff, options)
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["added_tables"][0]["name"] == "users"


def test_empty_diff_json_structure(capsys, empty_diff):
    options = WriteOptions(output_format="json")
    write_report(empty_diff, options)
    data = json.loads(capsys.readouterr().out)
    assert data == {"added_tables": [], "removed_tables": [], "modified_tables": []}


def test_modified_table_in_json(capsys):
    before_col = ColumnDefinition(name="age", col_type="INTEGER", nullable=True, default=None)
    after_col = ColumnDefinition(name="age", col_type="BIGINT", nullable=True, default=None)
    col_diff = ColumnDiff(name="age", before=before_col, after=after_col)
    td = TableDiff(name="users", added_columns=[], removed_columns=[], modified_columns=[col_diff])
    diff = SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[td])
    options = WriteOptions(output_format="json")
    write_report(diff, options)
    data = json.loads(capsys.readouterr().out)
    mod = data["modified_tables"][0]
    assert mod["name"] == "users"
    assert mod["modified_columns"][0]["before"]["type"] == "INTEGER"
    assert mod["modified_columns"][0]["after"]["type"] == "BIGINT"
