"""Tests for the rename report formatter."""

from sqldiff_report.column_rename_detector import RenameCandidate
from sqldiff_report.rename_report_formatter import (
    format_rename_text,
    format_rename_dict,
    format_all_renames_text,
)


def _cand(old: str, new: str, conf: float = 1.0) -> RenameCandidate:
    return RenameCandidate(old_name=old, new_name=new, confidence=conf)


def test_format_rename_text_contains_names():
    text = format_rename_text("orders", [_cand("usr_id", "user_id")], colour=False)
    assert "usr_id" in text
    assert "user_id" in text
    assert "orders" in text


def test_format_rename_text_shows_confidence_pct():
    text = format_rename_text("orders", [_cand("a", "b", 0.7)], colour=False)
    assert "70%" in text


def test_format_rename_text_empty_when_no_candidates():
    assert format_rename_text("orders", [], colour=False) == ""


def test_format_rename_text_colour_contains_ansi():
    text = format_rename_text("t", [_cand("x", "y")], colour=True)
    assert "\033[" in text


def test_format_rename_text_no_colour_has_no_ansi():
    text = format_rename_text("t", [_cand("x", "y")], colour=False)
    assert "\033[" not in text


def test_format_rename_dict_structure():
    result = format_rename_dict("users", [_cand("old", "new", 0.9)])
    assert result["table"] == "users"
    assert len(result["rename_candidates"]) == 1
    entry = result["rename_candidates"][0]
    assert entry["old_name"] == "old"
    assert entry["new_name"] == "new"
    assert entry["confidence"] == 0.9


def test_format_rename_dict_empty_candidates():
    result = format_rename_dict("t", [])
    assert result["rename_candidates"] == []


def test_format_all_renames_text_combines_tables():
    rename_map = {
        "users": [_cand("user_name", "username")],
        "orders": [_cand("qty", "quantity")],
    }
    text = format_all_renames_text(rename_map, colour=False)
    assert "users" in text
    assert "orders" in text
    assert "user_name" in text
    assert "qty" in text


def test_format_all_renames_skips_empty_tables():
    rename_map = {
        "users": [],
        "orders": [_cand("a", "b")],
    }
    text = format_all_renames_text(rename_map, colour=False)
    assert "users" not in text
    assert "orders" in text
