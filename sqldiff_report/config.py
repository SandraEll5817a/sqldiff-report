"""Configuration loading for sqldiff-report.

Supports reading defaults from a TOML config file (~/.sqldiff_report.toml
or a path supplied via --config) so users can persist preferred output
format and cache settings without repeating CLI flags.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib  # type: ignore[no-redef]
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            tomllib = None  # type: ignore[assignment]


DEFAULT_CONFIG_PATH = Path.home() / ".sqldiff_report.toml"


@dataclass
class AppConfig:
    output_format: str = "text"  # "text" | "json"
    no_color: bool = False
    cache_enabled: bool = True
    cache_dir: Optional[Path] = None


def _parse_toml(path: Path) -> dict:
    if tomllib is None:
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load AppConfig from *config_path* (falls back to DEFAULT_CONFIG_PATH).

    Missing files are silently ignored; invalid keys are skipped.
    """
    path = config_path or DEFAULT_CONFIG_PATH
    raw: dict = {}
    if path.exists() and path.is_file():
        try:
            raw = _parse_toml(path)
        except Exception:
            pass  # malformed TOML → use defaults

    cfg = AppConfig()
    if "output_format" in raw and raw["output_format"] in ("text", "json"):
        cfg.output_format = raw["output_format"]
    if "no_color" in raw and isinstance(raw["no_color"], bool):
        cfg.no_color = raw["no_color"]
    if "cache_enabled" in raw and isinstance(raw["cache_enabled"], bool):
        cfg.cache_enabled = raw["cache_enabled"]
    if "cache_dir" in raw and isinstance(raw["cache_dir"], str):
        cfg.cache_dir = Path(raw["cache_dir"])
    return cfg
