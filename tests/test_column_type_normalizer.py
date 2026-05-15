"""Tests for sqldiff_report.column_type_normalizer."""

import pytest

from sqldiff_report.column_type_normalizer import (
    extract_base_type,
    extract_precision,
    normalize_type,
    types_are_equivalent,
)


# ---------------------------------------------------------------------------
# normalize_type
# ---------------------------------------------------------------------------


def test_normalize_lowercases():
    assert normalize_type("VARCHAR") == "varchar"


def test_normalize_strips_whitespace():
    assert normalize_type("  int  ") == "int"


def test_normalize_collapses_internal_spaces():
    assert normalize_type("double  precision") == "double precision"


def test_normalize_removes_spaces_around_parens():
    assert normalize_type("VARCHAR( 255 )") == "varchar(255)"


def test_normalize_removes_spaces_around_comma():
    assert normalize_type("NUMERIC( 10 , 2 )") == "numeric(10,2)"


def test_normalize_applies_integer_alias():
    assert normalize_type("integer") == "int"


def test_normalize_applies_bool_alias():
    assert normalize_type("BOOL") == "boolean"


def test_normalize_applies_character_varying_alias():
    assert normalize_type("character varying(100)") == "varchar(100)"


def test_normalize_applies_int8_alias():
    assert normalize_type("int8") == "bigint"


def test_normalize_empty_string():
    assert normalize_type("") == ""


# ---------------------------------------------------------------------------
# types_are_equivalent
# ---------------------------------------------------------------------------


def test_equivalent_identical_types():
    assert types_are_equivalent("int", "int") is True


def test_equivalent_alias_match():
    assert types_are_equivalent("integer", "int") is True


def test_equivalent_case_insensitive():
    assert types_are_equivalent("VARCHAR(255)", "varchar(255)") is True


def test_not_equivalent_different_precision():
    assert types_are_equivalent("varchar(100)", "varchar(200)") is False


def test_not_equivalent_different_base_types():
    assert types_are_equivalent("int", "bigint") is False


# ---------------------------------------------------------------------------
# extract_base_type
# ---------------------------------------------------------------------------


def test_extract_base_type_no_precision():
    assert extract_base_type("int") == "int"


def test_extract_base_type_with_precision():
    assert extract_base_type("varchar(255)") == "varchar"


def test_extract_base_type_with_scale():
    assert extract_base_type("numeric(10,2)") == "numeric"


# ---------------------------------------------------------------------------
# extract_precision
# ---------------------------------------------------------------------------


def test_extract_precision_single():
    assert extract_precision("varchar(255)") == (255,)


def test_extract_precision_multiple():
    assert extract_precision("numeric(10,2)") == (10, 2)


def test_extract_precision_none_when_absent():
    assert extract_precision("int") is None
