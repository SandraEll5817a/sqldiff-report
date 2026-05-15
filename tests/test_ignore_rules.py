"""Tests for ignore_rules and filtered_diff modules."""

import pytest

from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff
from sqldiff_report.filtered_diff import apply_ignore_rules
from sqldiff_report.ignore_rules import IgnoreRules, rules_from_config


# ---------------------------------------------------------------------------
# IgnoreRules unit tests
# ---------------------------------------------------------------------------

def test_should_ignore_table_exact():
    rules = IgnoreRules(tables=["audit_log"])
    assert rules.should_ignore_table("audit_log") is True
    assert rules.should_ignore_table("users") is False


def test_should_ignore_table_glob():
    rules = IgnoreRules(tables=["tmp_*"])
    assert rules.should_ignore_table("tmp_migration") is True
    assert rules.should_ignore_table("orders") is False


def test_should_ignore_column_plain():
    rules = IgnoreRules(columns=["updated_at", "created_at"])
    assert rules.should_ignore_column("users", "updated_at") is True
    assert rules.should_ignore_column("users", "email") is False


def test_should_ignore_column_qualified():
    rules = IgnoreRules(columns=["audit_log.*"])
    assert rules.should_ignore_column("audit_log", "action") is True
    assert rules.should_ignore_column("users", "action") is False


def test_rules_from_config():
    cfg = {"ignore_tables": ["tmp_*"], "ignore_columns": ["updated_at"]}
    rules = rules_from_config(cfg)
    assert rules.tables == ["tmp_*"]
    assert rules.columns == ["updated_at"]


def test_rules_from_config_defaults():
    rules = rules_from_config({})
    assert rules.tables == []
    assert rules.columns == []


# ---------------------------------------------------------------------------
# apply_ignore_rules integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def base_diff() -> SchemaDiff:
    col_diff = ColumnDiff(column_name="updated_at", before="timestamp", after="timestamptz")
    real_diff = ColumnDiff(column_name="email", before="varchar(100)", after="varchar(255)")
    return SchemaDiff(
        added_tables=["tmp_staging", "orders"],
        removed_tables=["tmp_old", "archive"],
        modified_tables=[
            TableDiff(
                table_name="users",
                added_columns=[],
                removed_columns=[],
                modified_columns=[col_diff, real_diff],
            ),
            TableDiff(
                table_name="audit_log",
                added_columns=[ColumnDiff(column_name="ip", before=None, after="inet")],
                removed_columns=[],
                modified_columns=[],
            ),
        ],
    )


def test_ignore_table_removes_from_added(base_diff):
    rules = IgnoreRules(tables=["tmp_*"])
    result = apply_ignore_rules(base_diff, rules)
    assert "tmp_staging" not in result.added_tables
    assert "orders" in result.added_tables


def test_ignore_table_removes_from_removed(base_diff):
    rules = IgnoreRules(tables=["tmp_*"])
    result = apply_ignore_rules(base_diff, rules)
    assert "tmp_old" not in result.removed_tables
    assert "archive" in result.removed_tables


def test_ignore_table_removes_modified(base_diff):
    rules = IgnoreRules(tables=["audit_log"])
    result = apply_ignore_rules(base_diff, rules)
    names = [td.table_name for td in result.modified_tables]
    assert "audit_log" not in names
    assert "users" in names


def test_ignore_column_filters_modified_columns(base_diff):
    rules = IgnoreRules(columns=["updated_at"])
    result = apply_ignore_rules(base_diff, rules)
    users_diff = next(td for td in result.modified_tables if td.table_name == "users")
    col_names = [cd.column_name for cd in users_diff.modified_columns]
    assert "updated_at" not in col_names
    assert "email" in col_names


def test_table_dropped_when_all_columns_ignored(base_diff):
    rules = IgnoreRules(columns=["updated_at", "email"])
    result = apply_ignore_rules(base_diff, rules)
    names = [td.table_name for td in result.modified_tables]
    assert "users" not in names
