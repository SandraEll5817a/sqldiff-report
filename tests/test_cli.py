"""Tests for the sqldiff_report.cli module."""

import textwrap
from pathlib import Path

import pytest

from sqldiff_report.cli import run


BEFORE_SQL = textwrap.dedent("""\
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(255)
    );
""")

AFTER_SQL = textwrap.dedent("""\
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(255) NOT NULL,
        created_at TIMESTAMP
    );
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL
    );
""")

IDENTICAL_SQL = BEFORE_SQL


@pytest.fixture()
def before_file(tmp_path: Path) -> Path:
    p = tmp_path / "before.sql"
    p.write_text(BEFORE_SQL, encoding="utf-8")
    return p


@pytest.fixture()
def after_file(tmp_path: Path) -> Path:
    p = tmp_path / "after.sql"
    p.write_text(AFTER_SQL, encoding="utf-8")
    return p


@pytest.fixture()
def identical_file(tmp_path: Path) -> Path:
    p = tmp_path / "identical.sql"
    p.write_text(IDENTICAL_SQL, encoding="utf-8")
    return p


def test_run_returns_2_when_diff_found(before_file, after_file):
    exit_code = run([str(before_file), str(after_file), "--no-color"])
    assert exit_code == 2


def test_run_returns_0_when_no_diff(before_file, identical_file):
    exit_code = run([str(before_file), str(identical_file), "--no-color"])
    assert exit_code == 0


def test_run_writes_output_file(tmp_path, before_file, after_file):
    output = tmp_path / "report.txt"
    exit_code = run([str(before_file), str(after_file), "--no-color", "-o", str(output)])
    assert exit_code == 2
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "users" in content
    assert "orders" in content


def test_run_returns_1_for_missing_file(tmp_path, before_file):
    missing = tmp_path / "missing.sql"
    exit_code = run([str(before_file), str(missing)])
    assert exit_code == 1


def test_run_output_contains_diff_details(before_file, after_file, capsys):
    run([str(before_file), str(after_file), "--no-color"])
    captured = capsys.readouterr()
    assert "orders" in captured.out
    assert "created_at" in captured.out
