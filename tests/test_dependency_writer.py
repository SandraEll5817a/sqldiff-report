"""Tests for dependency_writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqldiff_report.dependency_graph import build_dependency_graph
from sqldiff_report.dependency_writer import DependencyWriteOptions, write_dependency_report
from sqldiff_report.diff_engine import SchemaDiff, TableDiff
from sqldiff_report.schema_parser import ColumnDefinition


def _col(name: str) -> ColumnDefinition:
    return ColumnDefinition(name=name, col_type="integer", nullable=True)


def _simple_diff() -> SchemaDiff:
    orders = TableDiff(
        table_name="orders",
        status="added",
        added_columns=[_col("id"), _col("user_id")],
        removed_columns=[],
        modified_columns=[],
    )
    users = TableDiff(
        table_name="users",
        status="added",
        added_columns=[_col("id")],
        removed_columns=[],
        modified_columns=[],
    )
    return SchemaDiff(added_tables=[orders, users], removed_tables=[], modified_tables=[])


@pytest.fixture()
def graph():
    return build_dependency_graph(_simple_diff())


def test_write_text_to_stdout(graph, capsys):
    write_dependency_report(graph, DependencyWriteOptions(fmt="text", colour=False))
    out = capsys.readouterr().out
    assert "-->" in out


def test_write_json_to_stdout(graph, capsys):
    write_dependency_report(graph, DependencyWriteOptions(fmt="json", colour=False))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "orders" in data


def test_write_text_to_file(graph, tmp_path):
    dest = tmp_path / "deps.txt"
    write_dependency_report(
        graph, DependencyWriteOptions(fmt="text", colour=False, output_path=dest)
    )
    content = dest.read_text()
    assert "-->" in content


def test_write_json_to_file(graph, tmp_path):
    dest = tmp_path / "deps.json"
    write_dependency_report(
        graph, DependencyWriteOptions(fmt="json", output_path=dest)
    )
    data = json.loads(dest.read_text())
    assert "users" in data


def test_empty_graph_text_contains_placeholder(capsys):
    from sqldiff_report.dependency_graph import DependencyGraph
    graph = DependencyGraph()
    write_dependency_report(graph, DependencyWriteOptions(fmt="text", colour=False))
    out = capsys.readouterr().out
    assert "no inter-table dependencies" in out
