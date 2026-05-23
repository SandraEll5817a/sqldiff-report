"""Attach semantic version tags to schema snapshots and diffs."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from sqldiff_report.diff_engine import SchemaDiff
from sqldiff_report.summary_stats import compute_stats

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[._-].+)?$")


@dataclass
class VersionTag:
    label: str
    major: int = 0
    minor: int = 0
    patch: int = 0
    notes: list[str] = field(default_factory=list)

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def __str__(self) -> str:
        return self.label


def parse_version(raw: str) -> Optional[VersionTag]:
    """Parse a semver-like string into a VersionTag, or return None."""
    m = _SEMVER_RE.match(raw.strip())
    if not m:
        return None
    return VersionTag(
        label=raw.strip(),
        major=int(m.group(1)),
        minor=int(m.group(2)),
        patch=int(m.group(3)),
    )


def suggest_next_version(current: str, diff: SchemaDiff) -> VersionTag:
    """Suggest the next semantic version based on the nature of the diff."""
    tag = parse_version(current)
    if tag is None:
        tag = VersionTag(label="0.0.0", major=0, minor=0, patch=0)

    stats = compute_stats(diff)
    notes: list[str] = []

    if diff.removed_tables:
        # Breaking: removed tables → major bump
        next_tag = VersionTag(
            label=f"{tag.major + 1}.0.0",
            major=tag.major + 1,
            minor=0,
            patch=0,
            notes=[f"Removed tables: {', '.join(diff.removed_tables)}"],
        )
        return next_tag

    if diff.added_tables or stats.columns_removed > 0:
        # Potentially breaking column removals → minor bump
        if diff.added_tables:
            notes.append(f"Added tables: {', '.join(diff.added_tables)}")
        if stats.columns_removed:
            notes.append(f"{stats.columns_removed} column(s) removed")
        return VersionTag(
            label=f"{tag.major}.{tag.minor + 1}.0",
            major=tag.major,
            minor=tag.minor + 1,
            patch=0,
            notes=notes,
        )

    if stats.total_changes > 0:
        notes.append(f"{stats.total_changes} change(s) (columns added/modified)")
        return VersionTag(
            label=f"{tag.major}.{tag.minor}.{tag.patch + 1}",
            major=tag.major,
            minor=tag.minor,
            patch=tag.patch + 1,
            notes=notes,
        )

    # No changes
    return VersionTag(
        label=tag.label,
        major=tag.major,
        minor=tag.minor,
        patch=tag.patch,
        notes=["No schema changes detected"],
    )
