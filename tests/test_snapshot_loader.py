"""Tests for sqldiff_report.snapshot_loader."""

import pytest

from sqldiff_report.snapshot_loader import (
    SnapshotLoadError,
    load_snapshot,
    load_snapshot_from_directory,
    load_snapshot_from_file,
)


SIMPLE_SQL = """
CREATE TABLE users (
    id INTEGER NOT NULL,
    name VARCHAR(100)
);
"""

EXTRA_SQL = """
CREATE TABLE orders (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL
);
"""


@pytest.fixture()
def sql_file(tmp_path):
    f = tmp_path / "schema.sql"
    f.write_text(SIMPLE_SQL, encoding="utf-8")
    return f


@pytest.fixture()
def sql_directory(tmp_path):
    (tmp_path / "01_users.sql").write_text(SIMPLE_SQL, encoding="utf-8")
    (tmp_path / "02_orders.sql").write_text(EXTRA_SQL, encoding="utf-8")
    return tmp_path


def test_load_from_file_returns_snapshot(sql_file):
    snapshot = load_snapshot_from_file(sql_file)
    assert "users" in snapshot.tables


def test_load_from_file_missing_raises(tmp_path):
    with pytest.raises(SnapshotLoadError, match="not found"):
        load_snapshot_from_file(tmp_path / "missing.sql")


def test_load_from_file_not_a_file_raises(tmp_path):
    with pytest.raises(SnapshotLoadError, match="not a file"):
        load_snapshot_from_file(tmp_path)


def test_load_from_directory_merges_tables(sql_directory):
    snapshot = load_snapshot_from_directory(sql_directory)
    assert "users" in snapshot.tables
    assert "orders" in snapshot.tables


def test_load_from_directory_sorted_order(sql_directory):
    """Tables from both files should be present regardless of glob order."""
    snapshot = load_snapshot_from_directory(sql_directory)
    assert set(snapshot.tables.keys()) == {"users", "orders"}


def test_load_from_directory_missing_raises(tmp_path):
    with pytest.raises(SnapshotLoadError, match="not found"):
        load_snapshot_from_directory(tmp_path / "nonexistent")


def test_load_from_directory_no_sql_files_raises(tmp_path):
    (tmp_path / "readme.txt").write_text("hello")
    with pytest.raises(SnapshotLoadError, match="No .sql files"):
        load_snapshot_from_directory(tmp_path)


def test_load_auto_detects_file(sql_file):
    snapshot = load_snapshot(sql_file)
    assert "users" in snapshot.tables


def test_load_auto_detects_directory(sql_directory):
    snapshot = load_snapshot(sql_directory)
    assert "users" in snapshot.tables
    assert "orders" in snapshot.tables
