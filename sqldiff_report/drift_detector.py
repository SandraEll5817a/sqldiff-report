"""Detects schema drift by comparing a current snapshot against a saved baseline.

Drift is defined as any table or column change that was not present in the
baseline diff, indicating the schema has diverged unexpectedly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqldiff_report.diff_engine import SchemaDiff, TableDiff
from sqldiff_report.baseline_manager import BaselineEntry
from sqldiff_report.severity import Severity, table_diff_severity


@dataclass
class DriftItem:
    table_name: str
    description: str
    severity: Severity


@dataclass
class DriftReport:
    items: List[DriftItem] = field(default_factory=list)
    baseline_label: Optional[str] = None

    @property
    def has_drift(self) -> bool:
        return len(self.items) > 0

    @property
    def max_severity(self) -> Severity:
        if not self.items:
            return Severity.LOW
        order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH]
        return max(self.items, key=lambda i: order.index(i.severity)).severity


def _table_names_in_diff(diff: SchemaDiff) -> set:
    names: set = set()
    for t in diff.added_tables:
        names.add(t.name)
    for t in diff.removed_tables:
        names.add(t.name)
    for t in diff.modified_tables:
        names.add(t.name)
    return names


def _describe_table_diff(td: TableDiff) -> str:
    if td.added_columns or td.removed_columns or td.modified_columns:
        parts = []
        if td.added_columns:
            parts.append(f"{len(td.added_columns)} column(s) added")
        if td.removed_columns:
            parts.append(f"{len(td.removed_columns)} column(s) removed")
        if td.modified_columns:
            parts.append(f"{len(td.modified_columns)} column(s) modified")
        return "; ".join(parts)
    return "table changed"


def detect_drift(current_diff: SchemaDiff, baseline: BaselineEntry) -> DriftReport:
    """Return a DriftReport listing tables that changed since the baseline."""
    baseline_tables = set(baseline.diff.get("added_tables", []))
    baseline_tables |= set(baseline.diff.get("removed_tables", []))
    baseline_tables |= set(baseline.diff.get("modified_tables", []))

    report = DriftReport(baseline_label=baseline.tags.get("label") if baseline.tags else None)

    all_current: List[TableDiff] = (
        list(current_diff.added_tables)
        + list(current_diff.removed_tables)
        + list(current_diff.modified_tables)
    )

    for td in all_current:
        if td.name not in baseline_tables:
            sev = table_diff_severity(td)
            report.items.append(
                DriftItem(
                    table_name=td.name,
                    description=_describe_table_diff(td),
                    severity=sev,
                )
            )

    return report
