"""Tests for drift_detector and drift_formatter."""

from __future__ import annotations

import pytest

from sqldiff_report.diff_engine import SchemaDiff, TableDiff, ColumnDiff
from sqldiff_report.baseline_manager import BaselineEntry
from sqldiff_report.severity import Severity
from sqldiff_report.drift_detector import detect_drift, DriftReport, DriftItem
from sqldiff_report.drift_formatter import format_drift_text, format_drift_dict


def _make_baseline(table_names: list) -> BaselineEntry:
    return BaselineEntry(
        diff={
            "added_tables": table_names,
            "removed_tables": [],
            "modified_tables": [],
        },
        tags={"label": "v1"},
        created_at="2024-01-01T00:00:00",
    )


def _added_table(name: str) -> TableDiff:
    return TableDiff(name=name, added_columns=[], removed_columns=[], modified_columns=[])


def _modified_table(name: str) -> TableDiff:
    col = ColumnDiff(name="id", old_type="int", new_type="bigint", old_nullable=False, new_nullable=False)
    return TableDiff(name=name, added_columns=[], removed_columns=[], modified_columns=[col])


def test_no_drift_when_all_tables_in_baseline():
    baseline = _make_baseline(["users"])
    diff = SchemaDiff(added_tables=[_added_table("users")], removed_tables=[], modified_tables=[])
    report = detect_drift(diff, baseline)
    assert not report.has_drift
    assert report.items == []


def test_drift_detected_for_new_table_not_in_baseline():
    baseline = _make_baseline(["users"])
    diff = SchemaDiff(
        added_tables=[_added_table("orders")],
        removed_tables=[],
        modified_tables=[],
    )
    report = detect_drift(diff, baseline)
    assert report.has_drift
    assert len(report.items) == 1
    assert report.items[0].table_name == "orders"


def test_drift_severity_is_populated():
    baseline = _make_baseline([])
    diff = SchemaDiff(
        added_tables=[],
        removed_tables=[],
        modified_tables=[_modified_table("users")],
    )
    report = detect_drift(diff, baseline)
    assert report.has_drift
    assert report.items[0].severity in list(Severity)


def test_max_severity_returns_highest():
    report = DriftReport(
        items=[
            DriftItem("a", "desc", Severity.LOW),
            DriftItem("b", "desc", Severity.HIGH),
        ]
    )
    assert report.max_severity == Severity.HIGH


def test_max_severity_empty_report_returns_low():
    report = DriftReport(items=[])
    assert report.max_severity == Severity.LOW


def test_baseline_label_propagated():
    baseline = _make_baseline([])
    diff = SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[])
    report = detect_drift(diff, baseline)
    assert report.baseline_label == "v1"


def test_format_drift_text_no_drift():
    report = DriftReport(items=[], baseline_label="v1")
    text = format_drift_text(report, colour=False)
    assert "No drift detected" in text
    assert "v1" in text


def test_format_drift_text_with_drift():
    report = DriftReport(
        items=[DriftItem("orders", "1 column(s) added", Severity.MEDIUM)],
        baseline_label=None,
    )
    text = format_drift_text(report, colour=False)
    assert "orders" in text
    assert "1 column(s) added" in text
    assert "MEDIUM" in text


def test_format_drift_text_no_colour_has_no_ansi():
    report = DriftReport(
        items=[DriftItem("tbl", "removed", Severity.HIGH)],
    )
    text = format_drift_text(report, colour=False)
    assert "\033[" not in text


def test_format_drift_dict_structure():
    report = DriftReport(
        items=[DriftItem("users", "1 column(s) removed", Severity.HIGH)],
        baseline_label="v2",
    )
    d = format_drift_dict(report)
    assert d["has_drift"] is True
    assert d["baseline_label"] == "v2"
    assert len(d["drifted_tables"]) == 1
    assert d["drifted_tables"][0]["table"] == "users"
    assert d["max_severity"] == "high"


def test_format_drift_dict_no_drift():
    report = DriftReport(items=[])
    d = format_drift_dict(report)
    assert d["has_drift"] is False
    assert d["max_severity"] is None
    assert d["drifted_tables"] == []
