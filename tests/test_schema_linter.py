"""Tests for sqldiff_report.schema_linter."""

from __future__ import annotations

import pytest

from sqldiff_report.schema_parser import ColumnDefinition, TableDefinition, SchemaSnapshot
from sqldiff_report.schema_linter import lint_snapshot, LintReport
from sqldiff_report.severity import Severity


def _make_col(name: str, col_type: str = "VARCHAR(255)", nullable: bool = True) -> ColumnDefinition:
    return ColumnDefinition(name=name, col_type=col_type, nullable=nullable)


def _make_snapshot(*tables: TableDefinition) -> SchemaSnapshot:
    return SchemaSnapshot(tables={t.name: t for t in tables})


# ---------------------------------------------------------------------------
# LintReport helpers
# ---------------------------------------------------------------------------

def test_empty_snapshot_has_no_issues():
    report = lint_snapshot(_make_snapshot())
    assert not report.has_issues
    assert report.error_count == 0
    assert report.warning_count == 0


def test_well_formed_table_no_issues():
    table = TableDefinition(name="users", columns=[_make_col("id", "INTEGER"), _make_col("email")])
    report = lint_snapshot(_make_snapshot(table))
    assert not report.has_issues


# ---------------------------------------------------------------------------
# Primary-key detection
# ---------------------------------------------------------------------------

def test_missing_pk_column_raises_medium():
    table = TableDefinition(name="logs", columns=[_make_col("message")])
    report = lint_snapshot(_make_snapshot(table))
    pk_issues = [i for i in report.issues if "primary key" in i.message.lower()]
    assert pk_issues, "Expected a primary-key warning"
    assert pk_issues[0].severity == Severity.MEDIUM
    assert pk_issues[0].column is None


def test_table_id_column_satisfies_pk_check():
    table = TableDefinition(name="orders", columns=[_make_col("orders_id", "BIGINT")])
    report = lint_snapshot(_make_snapshot(table))
    pk_issues = [i for i in report.issues if "primary key" in i.message.lower()]
    assert not pk_issues


# ---------------------------------------------------------------------------
# Missing type
# ---------------------------------------------------------------------------

def test_column_with_no_type_is_high_severity():
    col = ColumnDefinition(name="mystery", col_type="", nullable=True)
    table = TableDefinition(name="things", columns=[_make_col("id"), col])
    report = lint_snapshot(_make_snapshot(table))
    type_issues = [i for i in report.issues if "no type" in i.message.lower()]
    assert type_issues
    assert type_issues[0].severity == Severity.HIGH
    assert type_issues[0].column == "mystery"


# ---------------------------------------------------------------------------
# Unbounded type warning
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("col_type", ["text", "TEXT", "blob", "BLOB", "clob"])
def test_unbounded_type_raises_low_severity(col_type):
    table = TableDefinition(name="docs", columns=[_make_col("id"), _make_col("body", col_type)])
    report = lint_snapshot(_make_snapshot(table))
    type_issues = [i for i in report.issues if "unbounded" in i.message.lower()]
    assert type_issues
    assert type_issues[0].severity == Severity.LOW


def test_varchar_does_not_trigger_unbounded_warning():
    table = TableDefinition(name="items", columns=[_make_col("id"), _make_col("label", "VARCHAR(200)")])
    report = lint_snapshot(_make_snapshot(table))
    type_issues = [i for i in report.issues if "unbounded" in i.message.lower()]
    assert not type_issues


# ---------------------------------------------------------------------------
# Counts
# ---------------------------------------------------------------------------

def test_error_count_and_warning_count():
    col_no_type = ColumnDefinition(name="x", col_type="", nullable=True)
    # 'nopk' table: no pk (MEDIUM) + no-type col (HIGH)
    table = TableDefinition(name="nopk", columns=[col_no_type])
    report = lint_snapshot(_make_snapshot(table))
    assert report.error_count >= 1
    assert report.warning_count >= 1
