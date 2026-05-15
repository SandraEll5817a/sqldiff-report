"""Loads schema snapshots from SQL files or directories."""

from __future__ import annotations

import os
from pathlib import Path

from sqldiff_report.schema_parser import SchemaSnapshot, parse_schema


class SnapshotLoadError(Exception):
    """Raised when a snapshot cannot be loaded."""


def load_snapshot_from_file(path: str | Path) -> SchemaSnapshot:
    """Load a SchemaSnapshot from a single SQL file.

    Args:
        path: Path to the SQL file.

    Returns:
        Parsed SchemaSnapshot.

    Raises:
        SnapshotLoadError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.exists():
        raise SnapshotLoadError(f"File not found: {path}")
    if not path.is_file():
        raise SnapshotLoadError(f"Path is not a file: {path}")
    try:
        sql = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SnapshotLoadError(f"Cannot read file {path}: {exc}") from exc
    return parse_schema(sql)


def load_snapshot_from_directory(directory: str | Path) -> SchemaSnapshot:
    """Concatenate all *.sql files in a directory and parse as one snapshot.

    Files are sorted alphabetically to ensure deterministic ordering.

    Args:
        directory: Path to the directory containing SQL files.

    Returns:
        Merged SchemaSnapshot.

    Raises:
        SnapshotLoadError: If the directory cannot be read.
    """
    directory = Path(directory)
    if not directory.exists():
        raise SnapshotLoadError(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise SnapshotLoadError(f"Path is not a directory: {directory}")

    sql_files = sorted(directory.glob("*.sql"))
    if not sql_files:
        raise SnapshotLoadError(f"No .sql files found in directory: {directory}")

    parts: list[str] = []
    for sql_file in sql_files:
        try:
            parts.append(sql_file.read_text(encoding="utf-8"))
        except OSError as exc:
            raise SnapshotLoadError(f"Cannot read {sql_file}: {exc}") from exc

    combined_sql = "\n".join(parts)
    return parse_schema(combined_sql)


def load_snapshot(path: str | Path) -> SchemaSnapshot:
    """Auto-detect whether *path* is a file or directory and load accordingly."""
    path = Path(path)
    if path.is_dir():
        return load_snapshot_from_directory(path)
    return load_snapshot_from_file(path)
