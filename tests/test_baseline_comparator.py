"""Tests for sqldiff_report.baseline_comparator."""

import pytest

from sqldiff_report.baseline_comparator import (
    compare_against_baseline,
    format_comparison_text,
)
from sqldiff_report.baseline_manager import BaselineEntry
from sqldiff_report.diff_engine import SchemaDiff


def _make_baseline(added=(), removed=(), modified=()) -> BaselineEntry:
    return BaselineEntry(
        name="test-baseline",
        created_at="2024-01-01T00:00:00+00:00",
        diff_dict={
            "added_tables": list(added),
            "removed_tables": list(removed),
            "modified_tables": [{"table_name": m, "column_diffs": []} for m in modified],
        },
    )


def _make_diff(added=(), removed=(), modified=()) -> SchemaDiff:
    from sqldiff_report.diff_engine import TableDiff
    return SchemaDiff(
        added_tables=list(added),
        removed_tables=list(removed),
        modified_tables=[
            TableDiff(table_name=m, column_diffs=[]) for m in modified
        ],
    )


def test_no_new_tables_no_regression():
    baseline = _make_baseline(added=["users"])
    current = _make_diff(added=["users"])
    cmp = compare_against_baseline(current, baseline)
    assert not cmp.has_regressions
    assert cmp.persisting_tables == ["users"]


def test_new_table_in_current_is_regression():
    baseline = _make_baseline(added=["users"])
    current = _make_diff(added=["users", "orders"])
    cmp = compare_against_baseline(current, baseline)
    assert cmp.has_regressions
    assert "orders" in cmp.new_tables


def test_resolved_table_not_in_current():
    baseline = _make_baseline(removed=["legacy"])
    current = _make_diff()
    cmp = compare_against_baseline(current, baseline)
    assert "legacy" in cmp.resolved_tables
    assert not cmp.has_regressions


def test_persisting_modified_table():
    baseline = _make_baseline(modified=["products"])
    current = _make_diff(modified=["products"])
    cmp = compare_against_baseline(current, baseline)
    assert "products" in cmp.persisting_tables


def test_format_comparison_text_no_regression():
    baseline = _make_baseline(added=["x"])
    current = _make_diff(added=["x"])
    cmp = compare_against_baseline(current, baseline)
    text = format_comparison_text(cmp, colour=False)
    assert "No new regressions" in text


def test_format_comparison_text_shows_regression():
    baseline = _make_baseline()
    current = _make_diff(added=["new_table"])
    cmp = compare_against_baseline(current, baseline)
    text = format_comparison_text(cmp, colour=False)
    assert "new_table" in text
    assert "New changes" in text


def test_format_comparison_text_colour_contains_ansi():
    baseline = _make_baseline()
    current = _make_diff(added=["t"])
    cmp = compare_against_baseline(current, baseline)
    text = format_comparison_text(cmp, colour=True)
    assert "\033[" in text


def test_format_comparison_text_no_colour_no_ansi():
    baseline = _make_baseline()
    current = _make_diff(added=["t"])
    cmp = compare_against_baseline(current, baseline)
    text = format_comparison_text(cmp, colour=False)
    assert "\033[" not in text
