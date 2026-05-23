"""Tests for dependency_graph and dependency_formatter."""

from __future__ import annotations

import pytest

from sqldiff_report.dependency_graph import (
    DependencyGraph,
    build_dependency_graph,
    _infer_referenced_table,
)
from sqldiff_report.dependency_formatter import (
    format_dependency_text,
    format_dependency_dict,
)
from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff
from sqldiff_report.schema_parser import ColumnDefinition


def _col(name: str, col_type: str = "integer") -> ColumnDefinition:
    return ColumnDefinition(name=name, col_type=col_type, nullable=True)


def _added_table(name: str, *col_names: str) -> TableDiff:
    return TableDiff(
        table_name=name,
        status="added",
        added_columns=[_col(c) for c in col_names],
        removed_columns=[],
        modified_columns=[],
    )


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[])


# ---------------------------------------------------------------------------
# _infer_referenced_table
# ---------------------------------------------------------------------------

def test_infer_fk_column_plural():
    assert _infer_referenced_table("user_id", {"users"}) == "users"


def test_infer_fk_column_singular():
    assert _infer_referenced_table("order_id", {"order"}) == "order"


def test_infer_non_fk_column_returns_none():
    assert _infer_referenced_table("created_at", {"orders"}) is None


def test_infer_unknown_table_returns_none():
    assert _infer_referenced_table("user_id", {"products"}) is None


# ---------------------------------------------------------------------------
# build_dependency_graph
# ---------------------------------------------------------------------------

def test_empty_diff_produces_empty_graph():
    graph = build_dependency_graph(_empty_diff())
    assert graph.table_names() == []


def test_added_table_with_fk_column_creates_dependency():
    diff = SchemaDiff(
        added_tables=[
            _added_table("orders", "id", "user_id"),
            _added_table("users", "id"),
        ],
        removed_tables=[],
        modified_tables=[],
    )
    graph = build_dependency_graph(diff)
    assert "users" in graph.dependencies_of("orders")
    assert "orders" in graph.dependents_of("users")


def test_no_fk_columns_no_dependencies():
    diff = SchemaDiff(
        added_tables=[_added_table("products", "id", "name")],
        removed_tables=[],
        modified_tables=[],
    )
    graph = build_dependency_graph(diff)
    assert graph.dependencies_of("products") == []


def test_table_does_not_depend_on_itself():
    diff = SchemaDiff(
        added_tables=[_added_table("users", "id", "user_id")],
        removed_tables=[],
        modified_tables=[],
    )
    graph = build_dependency_graph(diff)
    assert "users" not in graph.dependencies_of("users")


# ---------------------------------------------------------------------------
# format_dependency_text
# ---------------------------------------------------------------------------

def test_text_placeholder_when_no_dependencies():
    graph = DependencyGraph()
    result = format_dependency_text(graph, colour=False)
    assert "no inter-table dependencies" in result


def test_text_contains_arrow():
    diff = SchemaDiff(
        added_tables=[
            _added_table("orders", "user_id"),
            _added_table("users", "id"),
        ],
        removed_tables=[],
        modified_tables=[],
    )
    graph = build_dependency_graph(diff)
    result = format_dependency_text(graph, colour=False)
    assert "orders" in result
    assert "-->" in result


def test_no_colour_has_no_ansi():
    diff = SchemaDiff(
        added_tables=[_added_table("orders", "user_id"), _added_table("users", "id")],
        removed_tables=[],
        modified_tables=[],
    )
    graph = build_dependency_graph(diff)
    result = format_dependency_text(graph, colour=False)
    assert "\033[" not in result


# ---------------------------------------------------------------------------
# format_dependency_dict
# ---------------------------------------------------------------------------

def test_dict_contains_all_tables():
    diff = SchemaDiff(
        added_tables=[_added_table("orders", "user_id"), _added_table("users", "id")],
        removed_tables=[],
        modified_tables=[],
    )
    graph = build_dependency_graph(diff)
    d = format_dependency_dict(graph)
    assert "orders" in d
    assert "users" in d


def test_dict_depends_on_key_is_list():
    diff = SchemaDiff(
        added_tables=[_added_table("orders", "user_id"), _added_table("users", "id")],
        removed_tables=[],
        modified_tables=[],
    )
    graph = build_dependency_graph(diff)
    d = format_dependency_dict(graph)
    assert isinstance(d["orders"]["depends_on"], list)
    assert "users" in d["orders"]["depends_on"]
