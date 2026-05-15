"""Simple file-based cache for parsed SchemaSnapshots.

Caches the JSON-serialised form of a snapshot keyed by the SHA-256
hash of the source SQL so that repeated runs over the same files are
fast.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

from sqldiff_report.schema_parser import ColumnDefinition, SchemaSnapshot, TableDefinition

_CACHE_DIR = Path.home() / ".cache" / "sqldiff_report"


def _hash_sql(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _snapshot_to_dict(snapshot: SchemaSnapshot) -> dict:
    return {
        table_name: {
            "name": tdef.name,
            "columns": [
                {"name": col.name, "col_type": col.col_type, "nullable": col.nullable}
                for col in tdef.columns
            ],
        }
        for table_name, tdef in snapshot.tables.items()
    }


def _snapshot_from_dict(data: dict) -> SchemaSnapshot:
    tables = {}
    for table_name, tdata in data.items():
        columns = [
            ColumnDefinition(
                name=c["name"], col_type=c["col_type"], nullable=c["nullable"]
            )
            for c in tdata["columns"]
        ]
        tables[table_name] = TableDefinition(name=tdata["name"], columns=columns)
    return SchemaSnapshot(tables=tables)


def get_cached(sql: str, cache_dir: Path = _CACHE_DIR) -> Optional[SchemaSnapshot]:
    """Return a cached snapshot for *sql*, or ``None`` if not cached."""
    key = _hash_sql(sql)
    cache_file = cache_dir / f"{key}.json"
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        return _snapshot_from_dict(data)
    except (OSError, KeyError, json.JSONDecodeError):
        return None


def put_cache(sql: str, snapshot: SchemaSnapshot, cache_dir: Path = _CACHE_DIR) -> None:
    """Persist *snapshot* to the cache keyed by the hash of *sql*."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = _hash_sql(sql)
    cache_file = cache_dir / f"{key}.json"
    try:
        cache_file.write_text(
            json.dumps(_snapshot_to_dict(snapshot), indent=2), encoding="utf-8"
        )
    except OSError:
        pass  # Cache write failures are non-fatal.


def clear_cache(cache_dir: Path = _CACHE_DIR) -> int:
    """Delete all cached snapshots. Returns the number of files removed."""
    if not cache_dir.exists():
        return 0
    removed = 0
    for f in cache_dir.glob("*.json"):
        try:
            f.unlink()
            removed += 1
        except OSError:
            pass
    return removed
