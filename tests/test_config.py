"""Tests for sqldiff_report.config."""

from __future__ import annotations

from pathlib import Path

import pytest

from sqldiff_report.config import AppConfig, load_config


def _write_toml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_config_defaults_when_no_file(tmp_path):
    cfg = load_config(tmp_path / "nonexistent.toml")
    assert cfg.output_format == "text"
    assert cfg.no_color is False
    assert cfg.cache_enabled is True
    assert cfg.cache_dir is None


def test_load_config_reads_output_format(tmp_path):
    p = tmp_path / "cfg.toml"
    _write_toml(p, 'output_format = "json"\n')
    cfg = load_config(p)
    assert cfg.output_format == "json"


def test_load_config_reads_no_color(tmp_path):
    p = tmp_path / "cfg.toml"
    _write_toml(p, "no_color = true\n")
    cfg = load_config(p)
    assert cfg.no_color is True


def test_load_config_reads_cache_dir(tmp_path):
    cache = tmp_path / "cache"
    p = tmp_path / "cfg.toml"
    _write_toml(p, f'cache_dir = "{cache}"\n')
    cfg = load_config(p)
    assert cfg.cache_dir == cache


def test_load_config_ignores_invalid_output_format(tmp_path):
    p = tmp_path / "cfg.toml"
    _write_toml(p, 'output_format = "xml"\n')
    cfg = load_config(p)
    assert cfg.output_format == "text"  # falls back to default


def test_load_config_ignores_malformed_toml(tmp_path):
    p = tmp_path / "cfg.toml"
    p.write_text("this is not valid toml ===\n", encoding="utf-8")
    cfg = load_config(p)  # should not raise
    assert isinstance(cfg, AppConfig)


def test_load_config_cache_disabled(tmp_path):
    p = tmp_path / "cfg.toml"
    _write_toml(p, "cache_enabled = false\n")
    cfg = load_config(p)
    assert cfg.cache_enabled is False
