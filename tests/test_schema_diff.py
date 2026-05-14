"""Tests for schema parsing, diff computation, and report formatting."""

import pytest

from sqldiff_report.diff_engine import compute_diff
from sqldiff_report.report_formatter import format_report
from sqldiff_report.schema_parser import parse_schema

OLD_SCHEMA = """
CREATE TABLE users (
    id INT NOT NULL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id INT NOT NULL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    body TEXT
);
"""

NEW_SCHEMA = """
CREATE TABLE users (
    id INT NOT NULL PRIMARY KEY,
    username VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP
);

CREATE TABLE comments (
    id INT NOT NULL PRIMARY KEY,
    post_id INT NOT NULL,
    body TEXT
);
"""


def test_parse_schema_tables():
    snapshot = parse_schema(OLD_SCHEMA)
    assert "users" in snapshot.tables
    assert "posts" in snapshot.tables


def test_parse_schema_columns():
    snapshot = parse_schema(OLD_SCHEMA)
    users = snapshot.tables["users"]
    assert "id" in users.columns
    assert "username" in users.columns
    assert users.columns["id"].primary_key is True
    assert users.columns["username"].nullable is False
    assert users.columns["email"].nullable is True


def test_compute_diff_added_table():
    old = parse_schema(OLD_SCHEMA)
    new = parse_schema(NEW_SCHEMA)
    diff = compute_diff(old, new)
    added = [t for t in diff.table_diffs if t.change_type == "added"]
    assert any(t.table_name == "comments" for t in added)


def test_compute_diff_removed_table():
    old = parse_schema(OLD_SCHEMA)
    new = parse_schema(NEW_SCHEMA)
    diff = compute_diff(old, new)
    removed = [t for t in diff.table_diffs if t.change_type == "removed"]
    assert any(t.table_name == "posts" for t in removed)


def test_compute_diff_modified_columns():
    old = parse_schema(OLD_SCHEMA)
    new = parse_schema(NEW_SCHEMA)
    diff = compute_diff(old, new)
    modified = [t for t in diff.table_diffs if t.table_name == "users"]
    assert len(modified) == 1
    col_names = {c.column_name for c in modified[0].column_diffs}
    assert "created_at" in col_names  # removed
    assert "updated_at" in col_names  # added


def test_no_diff_identical_schemas():
    old = parse_schema(OLD_SCHEMA)
    new = parse_schema(OLD_SCHEMA)
    diff = compute_diff(old, new)
    assert not diff.has_changes


def test_format_report_no_changes():
    old = parse_schema(OLD_SCHEMA)
    diff = compute_diff(old, old)
    report = format_report(diff)
    assert "No schema changes detected" in report


def test_format_report_contains_table_names():
    old = parse_schema(OLD_SCHEMA)
    new = parse_schema(NEW_SCHEMA)
    diff = compute_diff(old, new)
    report = format_report(diff)
    assert "comments" in report
    assert "posts" in report
    assert "users" in report
