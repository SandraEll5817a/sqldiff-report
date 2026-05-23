"""Tests for schema_version_tagger."""
from __future__ import annotations

import pytest

from sqldiff_report.schema_version_tagger import (
    VersionTag,
    parse_version,
    suggest_next_version,
)
from sqldiff_report.diff_engine import SchemaDiff, TableDiff, ColumnDiff


# ---------------------------------------------------------------------------
# parse_version
# ---------------------------------------------------------------------------

def test_parse_version_valid():
    tag = parse_version("1.2.3")
    assert tag is not None
    assert tag.major == 1
    assert tag.minor == 2
    assert tag.patch == 3
    assert tag.label == "1.2.3"


def test_parse_version_with_suffix():
    tag = parse_version("2.0.0-beta")
    assert tag is not None
    assert tag.major == 2


def test_parse_version_invalid_returns_none():
    assert parse_version("not-a-version") is None
    assert parse_version("") is None


def test_version_tag_as_tuple():
    tag = VersionTag(label="3.1.4", major=3, minor=1, patch=4)
    assert tag.as_tuple() == (3, 1, 4)


def test_version_tag_str():
    tag = VersionTag(label="1.0.0")
    assert str(tag) == "1.0.0"


# ---------------------------------------------------------------------------
# suggest_next_version
# ---------------------------------------------------------------------------

def _empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[])


def _diff_with_removed_table() -> SchemaDiff:
    return SchemaDiff(
        added_tables=[],
        removed_tables=["orders"],
        modified_tables=[],
    )


def _diff_with_added_table() -> SchemaDiff:
    return SchemaDiff(
        added_tables=["shipments"],
        removed_tables=[],
        modified_tables=[],
    )


def _diff_with_modified_column() -> SchemaDiff:
    col_diff = ColumnDiff(
        column_name="email",
        before=None,
        after=None,
        added=True,
        removed=False,
        type_changed=False,
        nullable_changed=False,
    )
    table_diff = TableDiff(
        table_name="users",
        added=False,
        removed=False,
        column_diffs=[col_diff],
    )
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[table_diff])


def test_no_changes_keeps_version():
    result = suggest_next_version("1.2.3", _empty_diff())
    assert result.label == "1.2.3"
    assert "No schema changes" in result.notes[0]


def test_removed_table_triggers_major_bump():
    result = suggest_next_version("1.2.3", _diff_with_removed_table())
    assert result.major == 2
    assert result.minor == 0
    assert result.patch == 0
    assert result.label == "2.0.0"


def test_added_table_triggers_minor_bump():
    result = suggest_next_version("1.2.3", _diff_with_added_table())
    assert result.major == 1
    assert result.minor == 3
    assert result.patch == 0


def test_column_added_triggers_patch_bump():
    result = suggest_next_version("1.2.3", _diff_with_modified_column())
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 4


def test_invalid_current_version_defaults_to_zero():
    result = suggest_next_version("not-semver", _diff_with_removed_table())
    assert result.major == 1
    assert result.minor == 0
