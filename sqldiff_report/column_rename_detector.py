"""Heuristic detection of likely column renames within a table diff."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from sqldiff_report.diff_engine import ColumnDiff, TableDiff
from sqldiff_report.column_type_normalizer import types_are_equivalent


@dataclass
class RenameCandidate:
    """A pair of removed/added columns that are likely a rename."""

    old_name: str
    new_name: str
    confidence: float  # 0.0 – 1.0


def _type_score(old: ColumnDiff, new: ColumnDiff) -> float:
    """Return 1.0 if types match, 0.5 if base types match, else 0.0."""
    if types_are_equivalent(old.old_type or "", new.new_type or ""):
        return 1.0
    old_base = (old.old_type or "").split("(")[0].strip().lower()
    new_base = (new.new_type or "").split("(")[0].strip().lower()
    return 0.5 if old_base == new_base else 0.0


def _nullable_score(old: ColumnDiff, new: ColumnDiff) -> float:
    """Return 1.0 if nullable flag matches, else 0.0."""
    return 1.0 if old.old_nullable == new.new_nullable else 0.0


def _confidence(removed: ColumnDiff, added: ColumnDiff) -> float:
    type_w = 0.7
    null_w = 0.3
    return round(
        type_w * _type_score(removed, added)
        + null_w * _nullable_score(removed, added),
        4,
    )


def detect_renames(
    table_diff: TableDiff, threshold: float = 0.5
) -> List[RenameCandidate]:
    """Return likely rename candidates from a *modified* table diff.

    Only columns that are purely added or purely removed (not type-changed)
    are considered.  Pairs are matched greedily by descending confidence.
    """
    removed = [
        cd for cd in table_diff.column_diffs if cd.kind == "removed"
    ]
    added = [
        cd for cd in table_diff.column_diffs if cd.kind == "added"
    ]

    if not removed or not added:
        return []

    # Build scored pairs
    scored: List[Tuple[float, ColumnDiff, ColumnDiff]] = []
    for r in removed:
        for a in added:
            score = _confidence(r, a)
            if score >= threshold:
                scored.append((score, r, a))

    scored.sort(key=lambda t: t[0], reverse=True)

    used_removed: set = set()
    used_added: set = set()
    candidates: List[RenameCandidate] = []

    for score, r, a in scored:
        if r.column_name in used_removed or a.column_name in used_added:
            continue
        candidates.append(
            RenameCandidate(
                old_name=r.column_name,
                new_name=a.column_name,
                confidence=score,
            )
        )
        used_removed.add(r.column_name)
        used_added.add(a.column_name)

    return candidates
