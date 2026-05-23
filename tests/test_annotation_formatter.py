"""Tests for annotation_formatter and annotation_writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqldiff_report.annotation_engine import Annotation
from sqldiff_report.annotation_formatter import format_annotations_text, format_annotations_dict
from sqldiff_report.annotation_writer import AnnotationWriteOptions, write_annotations
from sqldiff_report.severity import Severity


@pytest.fixture()
def sample_annotations():
    return [
        Annotation("users.email", Severity.HIGH, "Column removed."),
        Annotation("orders", Severity.LOW, "New table added."),
    ]


def test_text_empty_returns_placeholder():
    assert format_annotations_text([]) == "No annotations."


def test_text_contains_target(sample_annotations):
    text = format_annotations_text(sample_annotations, colour=False)
    assert "users.email" in text
    assert "orders" in text


def test_text_contains_message(sample_annotations):
    text = format_annotations_text(sample_annotations, colour=False)
    assert "Column removed." in text
    assert "New table added." in text


def test_text_contains_severity_label(sample_annotations):
    text = format_annotations_text(sample_annotations, colour=False)
    assert "[HIGH]" in text
    assert "[LOW]" in text


def test_text_colour_contains_ansi(sample_annotations):
    text = format_annotations_text(sample_annotations, colour=True)
    assert "\033[" in text


def test_text_no_colour_has_no_ansi(sample_annotations):
    text = format_annotations_text(sample_annotations, colour=False)
    assert "\033[" not in text


def test_dict_format(sample_annotations):
    result = format_annotations_dict(sample_annotations)
    assert len(result) == 2
    assert result[0]["target"] == "users.email"
    assert result[0]["severity"] == "HIGH"
    assert result[1]["severity"] == "LOW"


def test_write_text_to_stdout(capsys, sample_annotations):
    opts = AnnotationWriteOptions(fmt="text", colour=False)
    write_annotations(sample_annotations, opts)
    out = capsys.readouterr().out
    assert "users.email" in out


def test_write_json_to_stdout(capsys, sample_annotations):
    opts = AnnotationWriteOptions(fmt="json", colour=False)
    write_annotations(sample_annotations, opts)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["severity"] == "HIGH"


def test_write_text_to_file(tmp_path, sample_annotations):
    out_file = tmp_path / "annotations.txt"
    opts = AnnotationWriteOptions(fmt="text", output_path=out_file)
    write_annotations(sample_annotations, opts)
    content = out_file.read_text()
    assert "users.email" in content
    assert "\033[" not in content  # no ANSI when writing to file


def test_write_json_to_file(tmp_path, sample_annotations):
    out_file = tmp_path / "annotations.json"
    opts = AnnotationWriteOptions(fmt="json", output_path=out_file)
    write_annotations(sample_annotations, opts)
    data = json.loads(out_file.read_text())
    assert len(data) == 2
