"""Tests for sqldiff_report.diff_stats_exporter."""

from __future__ import annotations

import csv
import io
import json

import pytest

from sqldiff_report.diff_engine import (
    ColumnDiff,
    SchemaDiff,
    TableDiff,
)
from sqldiff_report.schema_parser import ColumnDefinition
from sqldiff_report.diff_stats_exporter import (
    export_stats,
    export_stats_csv,
    export_stats_json,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[])


def _col(name: str, col_type: str = "integer", nullable: bool = True) -> ColumnDefinition:
    return ColumnDefinition(name=name, col_type=col_type, nullable=nullable)


@pytest.fixture()
def simple_diff() -> SchemaDiff:
    added_col = ColumnDiff(column_name="email", before=None, after=_col("email", "text"))
    removed_col = ColumnDiff(column_name="phone", before=_col("phone", "varchar(20)"), after=None)
    modified_col = ColumnDiff(
        column_name="age",
        before=_col("age", "integer"),
        after=_col("age", "bigint"),
    )
    table = TableDiff(
        table_name="users",
        added=False,
        removed=False,
        column_diffs=[added_col, removed_col, modified_col],
    )
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[table])


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------


def test_export_json_is_valid_json(simple_diff: SchemaDiff) -> None:
    result = export_stats_json(simple_diff)
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


def test_export_json_contains_expected_keys(simple_diff: SchemaDiff) -> None:
    parsed = json.loads(export_stats_json(simple_diff))
    for key in ("overall_severity", "total_changes", "tables_modified", "columns_added"):
        assert key in parsed


def test_export_json_empty_diff_zero_changes(empty_diff: SchemaDiff) -> None:
    parsed = json.loads(export_stats_json(empty_diff))
    assert parsed["total_changes"] == 0


def test_export_json_column_counts_correct(simple_diff: SchemaDiff) -> None:
    parsed = json.loads(export_stats_json(simple_diff))
    assert parsed["columns_added"] == 1
    assert parsed["columns_removed"] == 1
    assert parsed["columns_modified"] == 1


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


def test_export_csv_has_header_and_row(simple_diff: SchemaDiff) -> None:
    result = export_stats_csv(simple_diff)
    lines = result.strip().splitlines()
    assert len(lines) == 2


def test_export_csv_header_contains_key(simple_diff: SchemaDiff) -> None:
    result = export_stats_csv(simple_diff)
    header = result.splitlines()[0]
    assert "total_changes" in header


def test_export_csv_values_parseable(simple_diff: SchemaDiff) -> None:
    result = export_stats_csv(simple_diff)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 1
    assert int(rows[0]["columns_added"]) == 1


def test_export_tsv_uses_tab_delimiter(simple_diff: SchemaDiff) -> None:
    result = export_stats(simple_diff, fmt="tsv")
    assert "\t" in result


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def test_export_stats_unknown_format_raises(empty_diff: SchemaDiff) -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        export_stats(empty_diff, fmt="xml")  # type: ignore[arg-type]


def test_export_stats_json_dispatch(empty_diff: SchemaDiff) -> None:
    result = export_stats(empty_diff, fmt="json")
    assert json.loads(result)["total_changes"] == 0
