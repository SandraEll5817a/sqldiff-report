"""Tests for summary_formatter."""
import pytest

from sqldiff_report.severity import Severity
from sqldiff_report.summary_stats import DiffStats
from sqldiff_report.summary_formatter import format_summary_text, format_summary_dict


@pytest.fixture
def sample_stats() -> DiffStats:
    return DiffStats(
        tables_added=1,
        tables_removed=2,
        tables_modified=3,
        columns_added=4,
        columns_removed=5,
        columns_modified=6,
        severity_counts={Severity.HIGH: 2, Severity.MEDIUM: 1, Severity.LOW: 3},
        overall_severity=Severity.HIGH,
    )


def test_text_contains_overall_severity(sample_stats):
    text = format_summary_text(sample_stats, use_colour=False)
    assert "HIGH" in text


def test_text_contains_table_counts(sample_stats):
    text = format_summary_text(sample_stats, use_colour=False)
    assert "Added    : 1" in text
    assert "Removed  : 2" in text
    assert "Modified : 3" in text


def test_text_contains_column_counts(sample_stats):
    text = format_summary_text(sample_stats, use_colour=False)
    assert "Added    : 4" in text
    assert "Removed  : 5" in text
    assert "Modified : 6" in text


def test_text_no_colour_has_no_ansi(sample_stats):
    text = format_summary_text(sample_stats, use_colour=False)
    assert "\033[" not in text


def test_text_with_colour_has_ansi(sample_stats):
    text = format_summary_text(sample_stats, use_colour=True)
    assert "\033[" in text


def test_dict_keys_present(sample_stats):
    d = format_summary_dict(sample_stats)
    assert "overall_severity" in d
    assert "tables" in d
    assert "columns" in d
    assert "severity_counts" in d
    assert "total_changes" in d


def test_dict_values_correct(sample_stats):
    d = format_summary_dict(sample_stats)
    assert d["overall_severity"] == Severity.HIGH
    assert d["tables"]["added"] == 1
    assert d["columns"]["removed"] == 5
    assert d["total_changes"] == sample_stats.total_changes
