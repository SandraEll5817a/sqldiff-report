"""Tests for sqldiff_report.watch_mode."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from sqldiff_report.watch_mode import _file_fingerprint, _fingerprints, watch


# ---------------------------------------------------------------------------
# _file_fingerprint
# ---------------------------------------------------------------------------

def test_fingerprint_file_stable(tmp_path: Path) -> None:
    f = tmp_path / "schema.sql"
    f.write_text("CREATE TABLE t (id INT);")
    assert _file_fingerprint(f) == _file_fingerprint(f)


def test_fingerprint_file_changes_on_write(tmp_path: Path) -> None:
    f = tmp_path / "schema.sql"
    f.write_text("CREATE TABLE t (id INT);")
    fp1 = _file_fingerprint(f)
    f.write_text("CREATE TABLE t (id BIGINT);")
    fp2 = _file_fingerprint(f)
    assert fp1 != fp2


def test_fingerprint_directory(tmp_path: Path) -> None:
    (tmp_path / "a.sql").write_text("CREATE TABLE a (x INT);")
    fp1 = _file_fingerprint(tmp_path)
    (tmp_path / "b.sql").write_text("CREATE TABLE b (y TEXT);")
    fp2 = _file_fingerprint(tmp_path)
    assert fp1 != fp2


def test_fingerprint_empty_dir(tmp_path: Path) -> None:
    # Should not raise; returns a consistent hash for empty dir
    fp = _file_fingerprint(tmp_path)
    assert isinstance(fp, str) and len(fp) > 0


# ---------------------------------------------------------------------------
# watch
# ---------------------------------------------------------------------------

def test_watch_calls_callback_on_startup(tmp_path: Path) -> None:
    before = tmp_path / "before.sql"
    after = tmp_path / "after.sql"
    before.write_text("CREATE TABLE t (id INT);")
    after.write_text("CREATE TABLE t (id INT);")

    calls: list[int] = []
    watch(before, after, callback=lambda: calls.append(1), interval=0.01, max_iterations=0)
    assert calls == [1]


def test_watch_detects_change(tmp_path: Path) -> None:
    before = tmp_path / "before.sql"
    after = tmp_path / "after.sql"
    before.write_text("CREATE TABLE t (id INT);")
    after.write_text("CREATE TABLE t (id INT);")

    calls: list[int] = []

    def _cb() -> None:
        calls.append(1)
        # Mutate *after* on first real poll to trigger a second callback
        if len(calls) == 1:
            after.write_text("CREATE TABLE t (id BIGINT);")

    watch(before, after, callback=_cb, interval=0.05, max_iterations=2)
    assert len(calls) >= 2
