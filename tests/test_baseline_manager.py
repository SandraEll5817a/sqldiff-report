"""Tests for sqldiff_report.baseline_manager."""

import json
import pytest
from pathlib import Path

from sqldiff_report.baseline_manager import (
    BaselineError,
    delete_baseline,
    list_baselines,
    load_baseline,
    save_baseline,
)
from sqldiff_report.diff_engine import SchemaDiff


@pytest.fixture()
def empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[])


@pytest.fixture()
def simple_diff() -> SchemaDiff:
    return SchemaDiff(
        added_tables=["users"],
        removed_tables=["legacy_log"],
        modified_tables=[],
    )


def test_save_baseline_creates_file(tmp_path, empty_diff):
    entry = save_baseline(tmp_path, "v1", empty_diff)
    assert (tmp_path / "v1.json").exists()
    assert entry.name == "v1"


def test_save_baseline_stores_diff(tmp_path, simple_diff):
    save_baseline(tmp_path, "v2", simple_diff, description="initial")
    data = json.loads((tmp_path / "v2.json").read_text())
    assert data["description"] == "initial"
    assert "users" in data["diff"]["added_tables"]


def test_save_baseline_stores_tags(tmp_path, empty_diff):
    save_baseline(tmp_path, "tagged", empty_diff, tags=["release", "hotfix"])
    data = json.loads((tmp_path / "tagged.json").read_text())
    assert "release" in data["tags"]


def test_load_baseline_returns_entry(tmp_path, simple_diff):
    save_baseline(tmp_path, "snap", simple_diff)
    entry = load_baseline(tmp_path, "snap")
    assert entry.name == "snap"
    assert "users" in entry.diff_dict["added_tables"]


def test_load_baseline_missing_raises(tmp_path):
    with pytest.raises(BaselineError, match="not found"):
        load_baseline(tmp_path, "ghost")


def test_list_baselines_returns_names(tmp_path, empty_diff):
    save_baseline(tmp_path, "alpha", empty_diff)
    save_baseline(tmp_path, "beta", empty_diff)
    names = list_baselines(tmp_path)
    assert names == ["alpha", "beta"]


def test_list_baselines_empty_dir(tmp_path):
    assert list_baselines(tmp_path) == []


def test_list_baselines_nonexistent_dir(tmp_path):
    assert list_baselines(tmp_path / "nope") == []


def test_delete_baseline_removes_file(tmp_path, empty_diff):
    save_baseline(tmp_path, "to_delete", empty_diff)
    delete_baseline(tmp_path, "to_delete")
    assert not (tmp_path / "to_delete.json").exists()


def test_delete_baseline_missing_raises(tmp_path):
    with pytest.raises(BaselineError, match="not found"):
        delete_baseline(tmp_path, "missing")
