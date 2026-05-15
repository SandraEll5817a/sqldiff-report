"""Tests for sqldiff_report.watch_cli."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from sqldiff_report.watch_cli import _build_callback, run_watch


BEFORE_SQL = "CREATE TABLE users (id INT, name VARCHAR(100));"
AFTER_SQL = "CREATE TABLE users (id BIGINT, name VARCHAR(100));"


@pytest.fixture()
def schema_files(tmp_path: Path):
    before = tmp_path / "before.sql"
    after = tmp_path / "after.sql"
    before.write_text(BEFORE_SQL)
    after.write_text(AFTER_SQL)
    return before, after


def test_build_callback_runs_without_error(schema_files, capsys) -> None:
    before, after = schema_files
    cb = _build_callback(before, after, colour=False)
    cb()
    captured = capsys.readouterr()
    assert "users" in captured.out


def test_build_callback_handles_bad_path(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing.sql"
    after = tmp_path / "after.sql"
    after.write_text(AFTER_SQL)
    cb = _build_callback(missing, after, colour=False)
    cb()  # should not raise
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_run_watch_missing_before_exits(tmp_path: Path) -> None:
    after = tmp_path / "after.sql"
    after.write_text(AFTER_SQL)
    with pytest.raises(SystemExit) as exc_info:
        run_watch(str(tmp_path / "no.sql"), str(after), interval=0.01)
    assert exc_info.value.code == 1


def test_run_watch_missing_after_exits(tmp_path: Path) -> None:
    before = tmp_path / "before.sql"
    before.write_text(BEFORE_SQL)
    with pytest.raises(SystemExit) as exc_info:
        run_watch(str(before), str(tmp_path / "no.sql"), interval=0.01)
    assert exc_info.value.code == 1


def test_run_watch_executes_iterations(schema_files, capsys) -> None:
    before, after = schema_files
    # max_iterations=0 means only the startup callback fires then exits
    run_watch(str(before), str(after), interval=0.01, colour=False, max_iterations=0)
    captured = capsys.readouterr()
    assert "users" in captured.out
