"""Manage saved diff baselines for tracking schema evolution over time."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqldiff_report.diff_engine import SchemaDiff
from sqldiff_report.output_writer import _diff_to_dict


class BaselineError(Exception):
    """Raised when a baseline operation fails."""


@dataclass
class BaselineEntry:
    name: str
    created_at: str
    diff_dict: dict
    description: str = ""
    tags: list[str] = field(default_factory=list)


def _entry_to_dict(entry: BaselineEntry) -> dict:
    return {
        "name": entry.name,
        "created_at": entry.created_at,
        "description": entry.description,
        "tags": entry.tags,
        "diff": entry.diff_dict,
    }


def _entry_from_dict(data: dict) -> BaselineEntry:
    return BaselineEntry(
        name=data["name"],
        created_at=data["created_at"],
        description=data.get("description", ""),
        tags=data.get("tags", []),
        diff_dict=data["diff"],
    )


def save_baseline(
    baseline_dir: Path,
    name: str,
    diff: SchemaDiff,
    description: str = "",
    tags: Optional[list[str]] = None,
) -> BaselineEntry:
    """Persist a SchemaDiff as a named baseline JSON file."""
    baseline_dir = Path(baseline_dir)
    baseline_dir.mkdir(parents=True, exist_ok=True)

    entry = BaselineEntry(
        name=name,
        created_at=datetime.now(timezone.utc).isoformat(),
        diff_dict=_diff_to_dict(diff),
        description=description,
        tags=tags or [],
    )

    dest = baseline_dir / f"{name}.json"
    dest.write_text(json.dumps(_entry_to_dict(entry), indent=2), encoding="utf-8")
    return entry


def load_baseline(baseline_dir: Path, name: str) -> BaselineEntry:
    """Load a named baseline from disk."""
    path = Path(baseline_dir) / f"{name}.json"
    if not path.exists():
        raise BaselineError(f"Baseline '{name}' not found in {baseline_dir}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return _entry_from_dict(data)


def list_baselines(baseline_dir: Path) -> list[str]:
    """Return sorted list of baseline names available in the directory."""
    baseline_dir = Path(baseline_dir)
    if not baseline_dir.exists():
        return []
    return sorted(p.stem for p in baseline_dir.glob("*.json"))


def delete_baseline(baseline_dir: Path, name: str) -> None:
    """Remove a baseline file from disk."""
    path = Path(baseline_dir) / f"{name}.json"
    if not path.exists():
        raise BaselineError(f"Baseline '{name}' not found in {baseline_dir}")
    path.unlink()
