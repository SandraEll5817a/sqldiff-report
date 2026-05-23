"""Tests for impact_analyzer and impact_formatter."""

from __future__ import annotations

import pytest

from sqldiff_report.schema_parser import ColumnDefinition
from sqldiff_report.diff_engine import ColumnDiff, TableDiff, SchemaDiff
from sqldiff_report.severity import Severity
from sqldiff_report.impact_analyzer import analyze_impact, ImpactReport
from sqldiff_report.impact_formatter import format_impact_text, format_impact_dict


def _col(name: str, col_type: str = "integer", nullable: bool = True) -> ColumnDefinition:
    return ColumnDefinition(col_name=name, col_type=col_type, nullable=nullable)


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(table_diffs=[])


def _added_table() -> TableDiff:
    return TableDiff(table_name="orders", added=True, removed=False, column_diffs=[])


def _removed_table() -> TableDiff:
    return TableDiff(table_name="legacy", added=False, removed=True, column_diffs=[])


def _modified_table() -> TableDiff:
    col_added = ColumnDiff(column_name="email", old_definition=None, new_definition=_col("email", "varchar"))
    col_removed = ColumnDiff(column_name="phone", old_definition=_col("phone", "varchar"), new_definition=None)
    col_type = ColumnDiff(column_name="age", old_definition=_col("age", "integer"), new_definition=_col("age", "bigint"))
    col_null = ColumnDiff(
        column_name="name",
        old_definition=_col("name", "varchar", nullable=True),
        new_definition=_col("name", "varchar", nullable=False),
    )
    return TableDiff(table_name="users", added=False, removed=False,
                     column_diffs=[col_added, col_removed, col_type, col_null])


def test_empty_diff_produces_empty_report():
    report = analyze_impact(_empty_diff())
    assert isinstance(report, ImpactReport)
    assert report.items == []
    assert not report.has_breaking_changes


def test_added_table_produces_low_severity_item():
    diff = SchemaDiff(table_diffs=[_added_table()])
    report = analyze_impact(diff)
    assert len(report.items) == 1
    assert report.items[0].severity == Severity.LOW
    assert report.items[0].change_type == "table_added"


def test_removed_table_produces_high_severity_item():
    diff = SchemaDiff(table_diffs=[_removed_table()])
    report = analyze_impact(diff)
    assert len(report.items) == 1
    assert report.items[0].severity == Severity.HIGH
    assert report.has_breaking_changes


def test_modified_table_produces_one_item_per_column_diff():
    diff = SchemaDiff(table_diffs=[_modified_table()])
    report = analyze_impact(diff)
    assert len(report.items) == 4


def test_removed_column_is_high_severity():
    diff = SchemaDiff(table_diffs=[_modified_table()])
    report = analyze_impact(diff)
    removed = [i for i in report.items if i.change_type == "column" and i.column == "phone"]
    assert removed and removed[0].severity == Severity.HIGH


def test_added_column_is_low_severity():
    diff = SchemaDiff(table_diffs=[_modified_table()])
    report = analyze_impact(diff)
    added = [i for i in report.items if i.change_type == "column" and i.column == "email"]
    assert added and added[0].severity == Severity.LOW


def test_counts_are_correct():
    diff = SchemaDiff(table_diffs=[_added_table(), _removed_table()])
    report = analyze_impact(diff)
    assert report.high_count == 1
    assert report.low_count == 1
    assert report.medium_count == 0


def test_format_text_no_items_returns_placeholder():
    report = ImpactReport(items=[])
    text = format_impact_text(report, colour=False)
    assert "No impact" in text


def test_format_text_contains_table_name():
    diff = SchemaDiff(table_diffs=[_added_table()])
    report = analyze_impact(diff)
    text = format_impact_text(report, colour=False)
    assert "orders" in text


def test_format_text_breaking_warning_when_high():
    diff = SchemaDiff(table_diffs=[_removed_table()])
    report = analyze_impact(diff)
    text = format_impact_text(report, colour=False)
    assert "Breaking" in text or "HIGH" in text


def test_format_text_no_colour_has_no_ansi():
    diff = SchemaDiff(table_diffs=[_removed_table()])
    report = analyze_impact(diff)
    text = format_impact_text(report, colour=False)
    assert "\033[" not in text


def test_format_dict_structure():
    diff = SchemaDiff(table_diffs=[_added_table(), _removed_table()])
    report = analyze_impact(diff)
    d = format_impact_dict(report)
    assert "has_breaking_changes" in d
    assert "summary" in d
    assert "items" in d
    assert d["summary"]["high"] == 1
    assert d["summary"]["low"] == 1


def test_format_dict_item_keys():
    diff = SchemaDiff(table_diffs=[_added_table()])
    report = analyze_impact(diff)
    d = format_impact_dict(report)
    item = d["items"][0]
    for key in ("table", "column", "change_type", "severity", "description", "recommendation"):
        assert key in item
