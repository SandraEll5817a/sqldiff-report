"""Tests for annotation_engine."""

from __future__ import annotations

import pytest

from sqldiff_report.schema_parser import ColumnDefinition
from sqldiff_report.diff_engine import ColumnDiff, TableDiff, SchemaDiff
from sqldiff_report.annotation_engine import annotate_diff, Annotation
from sqldiff_report.severity import Severity


def _col(name: str, col_type: str = "varchar(255)", nullable: bool = True) -> ColumnDefinition:
    return ColumnDefinition(column_name=name, col_type=col_type, nullable=nullable)


def _added_table(name: str) -> TableDiff:
    return TableDiff(table_name=name, added=True, removed=False, column_diffs=[])


def _removed_table(name: str) -> TableDiff:
    return TableDiff(table_name=name, added=False, removed=True, column_diffs=[])


def _modified_table(name: str, col_diffs: list) -> TableDiff:
    return TableDiff(table_name=name, added=False, removed=False, column_diffs=col_diffs)


def test_empty_diff_produces_no_annotations():
    diff = SchemaDiff(table_diffs=[])
    assert annotate_diff(diff) == []


def test_added_table_produces_low_annotation():
    diff = SchemaDiff(table_diffs=[_added_table("users")])
    anns = annotate_diff(diff)
    assert len(anns) == 1
    assert anns[0].severity == Severity.LOW
    assert "permission" in anns[0].message.lower()


def test_removed_table_produces_high_annotation():
    diff = SchemaDiff(table_diffs=[_removed_table("legacy")])
    anns = annotate_diff(diff)
    assert len(anns) == 1
    assert anns[0].severity == Severity.HIGH
    assert "removed" in anns[0].message.lower()


def test_added_column_produces_low_annotation():
    col_diff = ColumnDiff(column_name="bio", old_definition=None, new_definition=_col("bio"))
    diff = SchemaDiff(table_diffs=[_modified_table("users", [col_diff])])
    anns = annotate_diff(diff)
    assert any(a.severity == Severity.LOW for a in anns)
    assert any("added" in a.message.lower() for a in anns)


def test_removed_column_produces_high_annotation():
    col_diff = ColumnDiff(column_name="old_col", old_definition=_col("old_col"), new_definition=None)
    diff = SchemaDiff(table_diffs=[_modified_table("users", [col_diff])])
    anns = annotate_diff(diff)
    assert any(a.severity == Severity.HIGH for a in anns)


def test_type_change_produces_high_annotation():
    old = _col("amount", col_type="int")
    new = _col("amount", col_type="bigint")
    col_diff = ColumnDiff(column_name="amount", old_definition=old, new_definition=new)
    diff = SchemaDiff(table_diffs=[_modified_table("orders", [col_diff])])
    anns = annotate_diff(diff)
    assert any(a.severity == Severity.HIGH and "type" in a.message.lower() for a in anns)


def test_nullable_to_not_null_is_high():
    old = _col("email", nullable=True)
    new = _col("email", nullable=False)
    col_diff = ColumnDiff(column_name="email", old_definition=old, new_definition=new)
    diff = SchemaDiff(table_diffs=[_modified_table("users", [col_diff])])
    anns = annotate_diff(diff)
    assert any(a.severity == Severity.HIGH and "nullable" in a.message.lower() for a in anns)


def test_not_null_to_nullable_is_low():
    old = _col("email", nullable=False)
    new = _col("email", nullable=True)
    col_diff = ColumnDiff(column_name="email", old_definition=old, new_definition=new)
    diff = SchemaDiff(table_diffs=[_modified_table("users", [col_diff])])
    anns = annotate_diff(diff)
    assert any(a.severity == Severity.LOW and "nullable" in a.message.lower() for a in anns)
