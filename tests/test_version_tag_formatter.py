"""Tests for version_tag_formatter."""
from __future__ import annotations

import json
import pytest

from sqldiff_report.schema_version_tagger import VersionTag
from sqldiff_report.version_tag_formatter import (
    format_version_text,
    format_version_dict,
    _detect_bump_kind,
)


@pytest.fixture()
def major_bump_tag() -> VersionTag:
    return VersionTag(label="2.0.0", major=2, minor=0, patch=0, notes=["Removed tables: orders"])


@pytest.fixture()
def no_change_tag() -> VersionTag:
    return VersionTag(label="1.2.3", major=1, minor=2, patch=3, notes=["No schema changes detected"])


def test_text_contains_current_version(major_bump_tag):
    out = format_version_text("1.2.3", major_bump_tag, use_colour=False)
    assert "1.2.3" in out


def test_text_contains_suggested_version(major_bump_tag):
    out = format_version_text("1.2.3", major_bump_tag, use_colour=False)
    assert "2.0.0" in out


def test_text_shows_major_bump_label(major_bump_tag):
    out = format_version_text("1.2.3", major_bump_tag, use_colour=False)
    assert "major" in out


def test_text_no_change_message(no_change_tag):
    out = format_version_text("1.2.3", no_change_tag, use_colour=False)
    assert "no change needed" in out


def test_text_includes_notes(major_bump_tag):
    out = format_version_text("1.2.3", major_bump_tag, use_colour=False)
    assert "Removed tables" in out


def test_text_colour_contains_ansi(major_bump_tag):
    out = format_version_text("1.2.3", major_bump_tag, use_colour=True)
    assert "\033[" in out


def test_text_no_colour_has_no_ansi(major_bump_tag):
    out = format_version_text("1.2.3", major_bump_tag, use_colour=False)
    assert "\033[" not in out


def test_dict_contains_expected_keys(major_bump_tag):
    d = format_version_dict("1.2.3", major_bump_tag)
    assert "current" in d
    assert "suggested" in d
    assert "bump_kind" in d
    assert "notes" in d


def test_dict_bump_kind_major(major_bump_tag):
    d = format_version_dict("1.2.3", major_bump_tag)
    assert d["bump_kind"] == "major"


def test_dict_bump_kind_none(no_change_tag):
    d = format_version_dict("1.2.3", no_change_tag)
    assert d["bump_kind"] == "none"


def test_detect_bump_kind_patch():
    tag = VersionTag(label="1.2.4", major=1, minor=2, patch=4)
    assert _detect_bump_kind("1.2.3", tag) == "patch"


def test_detect_bump_kind_minor():
    tag = VersionTag(label="1.3.0", major=1, minor=3, patch=0)
    assert _detect_bump_kind("1.2.3", tag) == "minor"
