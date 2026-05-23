"""Tracks column lineage across schema snapshots.

Builds a lineage map that records where each column came from,
combining rename detection with add/remove events to give a
complete picture of how columns evolved between two snapshots.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqldiff_report.diff_engine import SchemaDiff, TableDiff
from sqldiff_report.column_rename_detector import RenameCandidate, detect_renames


@dataclass
class LineageEntry:
    table: str
    column: str
    origin_column: Optional[str]  # None when column is brand-new
    event: str  # 'added', 'removed', 'renamed', 'modified', 'unchanged'
    confidence: Optional[float] = None  # only set for 'renamed'


@dataclass
class TableLineage:
    table: str
    entries: List[LineageEntry] = field(default_factory=list)


def _lineage_for_table(table_diff: TableDiff) -> TableLineage:
    lineage = TableLineage(table=table_diff.table_name)

    if table_diff.added:
        for col in table_diff.columns_added:
            lineage.entries.append(
                LineageEntry(table_diff.table_name, col.name, None, "added")
            )
        return lineage

    if table_diff.removed:
        for col in table_diff.columns_removed:
            lineage.entries.append(
                LineageEntry(table_diff.table_name, col.name, None, "removed")
            )
        return lineage

    renames: List[RenameCandidate] = detect_renames(table_diff)
    renamed_removed = {r.removed_column for r in renames}
    renamed_added = {r.added_column for r in renames}

    for r in renames:
        lineage.entries.append(
            LineageEntry(
                table_diff.table_name,
                r.added_column,
                r.removed_column,
                "renamed",
                confidence=r.confidence,
            )
        )

    for col in table_diff.columns_added:
        if col.name not in renamed_added:
            lineage.entries.append(
                LineageEntry(table_diff.table_name, col.name, None, "added")
            )

    for col in table_diff.columns_removed:
        if col.name not in renamed_removed:
            lineage.entries.append(
                LineageEntry(table_diff.table_name, col.name, None, "removed")
            )

    for col_diff in table_diff.column_diffs:
        lineage.entries.append(
            LineageEntry(
                table_diff.table_name,
                col_diff.column_name,
                col_diff.column_name,
                "modified",
            )
        )

    return lineage


def build_lineage(diff: SchemaDiff) -> Dict[str, TableLineage]:
    """Return a mapping of table_name -> TableLineage for every changed table."""
    result: Dict[str, TableLineage] = {}
    for table_diff in diff.table_diffs:
        tl = _lineage_for_table(table_diff)
        result[tl.table] = tl
    return result
