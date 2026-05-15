"""Tests for the column rename detector."""

import pytest

from sqldiff_report.column_rename_detector import (
    RenameCandidate,
    detect_renames,
)
from sqldiff_report.diff_engine import ColumnDiff, TableDiff


def _removed(name: str, typ: str = "integer", nullable: bool = False) -> ColumnDiff:
    return ColumnDiff(
        column_name=name,
        kind="removed",
        old_type=typ,
        new_type=None,
        old_nullable=nullable,
        new_nullable=None,
    )


def _added(name: str, typ: str = "integer", nullable: bool = False) -> ColumnDiff:
    return ColumnDiff(
        column_name=name,
        kind="added",
        old_type=None,
        new_type=typ,
        old_nullable=None,
        new_nullable=nullable,
    )


def _table(col_diffs):
    return TableDiff(
        table_name="users",
        kind="modified",
        column_diffs=col_diffs,
    )


def test_detect_rename_exact_type_match():
    diff = _table([_removed("user_name", "varchar(100)"), _added("username", "varchar(100)")])
    results = detect_renames(diff)
    assert len(results) == 1
    assert results[0].old_name == "user_name"
    assert results[0].new_name == "username"
    assert results[0].confidence == 1.0


def test_detect_rename_base_type_match():
    diff = _table([_removed("qty", "integer"), _added("quantity", "int")])
    results = detect_renames(diff)
    # int / integer normalise to same base
    assert len(results) == 1


def test_detect_no_rename_when_types_differ():
    diff = _table([_removed("col_a", "integer"), _added("col_b", "text")])
    results = detect_renames(diff, threshold=0.5)
    # type score 0, nullable score 1 -> confidence 0.3 < threshold
    assert results == []


def test_detect_no_rename_when_only_removed():
    diff = _table([_removed("gone", "integer")])
    assert detect_renames(diff) == []


def test_detect_no_rename_when_only_added():
    diff = _table([_added("new_col", "text")])
    assert detect_renames(diff) == []


def test_greedy_matching_no_duplicate_use():
    # Two removed, two added — best pairs should be matched without reuse
    col_diffs = [
        _removed("a", "integer"),
        _removed("b", "integer"),
        _added("x", "integer"),
        _added("y", "integer"),
    ]
    diff = _table(col_diffs)
    results = detect_renames(diff)
    old_names = {r.old_name for r in results}
    new_names = {r.new_name for r in results}
    assert len(old_names) == len(results), "Each old name used at most once"
    assert len(new_names) == len(results), "Each new name used at most once"


def test_confidence_reflects_nullable_mismatch():
    diff = _table([
        _removed("col", "integer", nullable=False),
        _added("col2", "integer", nullable=True),
    ])
    results = detect_renames(diff)
    assert len(results) == 1
    # type matches (1.0 * 0.7) + nullable mismatch (0.0 * 0.3) = 0.7
    assert results[0].confidence == pytest.approx(0.7)
