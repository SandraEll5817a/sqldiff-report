"""Analyzes the potential impact of schema changes on dependent objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqldiff_report.diff_engine import SchemaDiff, TableDiff, ColumnDiff
from sqldiff_report.severity import Severity, column_diff_severity, table_diff_severity


@dataclass
class ImpactItem:
    table: str
    column: Optional[str]
    change_type: str
    severity: Severity
    description: str
    recommendation: str


@dataclass
class ImpactReport:
    items: List[ImpactItem] = field(default_factory=list)

    @property
    def has_breaking_changes(self) -> bool:
        return any(i.severity == Severity.HIGH for i in self.items)

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.items if i.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for i in self.items if i.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for i in self.items if i.severity == Severity.LOW)


def _column_impact(table: str, diff: ColumnDiff) -> ImpactItem:
    sev = column_diff_severity(diff)
    if diff.old_definition is None:
        desc = f"Column '{diff.column_name}' added to '{table}'."
        rec = "Ensure application code handles the new column; verify NOT NULL defaults."
    elif diff.new_definition is None:
        desc = f"Column '{diff.column_name}' removed from '{table}'."
        rec = "Remove all references to this column in queries and ORM models."
    else:
        old_t = diff.old_definition.col_type
        new_t = diff.new_definition.col_type
        if old_t != new_t:
            desc = f"Column '{diff.column_name}' type changed from '{old_t}' to '{new_t}'."
            rec = "Audit casts and comparisons; test data migration scripts."
        else:
            old_n = diff.old_definition.nullable
            new_n = diff.new_definition.nullable
            desc = f"Column '{diff.column_name}' nullability changed ({old_n} -> {new_n})."
            rec = "Verify existing rows satisfy new constraint before applying migration."
    return ImpactItem(
        table=table,
        column=diff.column_name,
        change_type="column",
        severity=sev,
        description=desc,
        recommendation=rec,
    )


def _table_impact(diff: TableDiff) -> List[ImpactItem]:
    items: List[ImpactItem] = []
    if diff.added:
        items.append(ImpactItem(
            table=diff.table_name, column=None, change_type="table_added",
            severity=Severity.LOW,
            description=f"Table '{diff.table_name}' is new.",
            recommendation="Run CREATE TABLE migration and update ORM models.",
        ))
    elif diff.removed:
        items.append(ImpactItem(
            table=diff.table_name, column=None, change_type="table_removed",
            severity=Severity.HIGH,
            description=f"Table '{diff.table_name}' was dropped.",
            recommendation="Remove all queries and foreign-key references before dropping.",
        ))
    else:
        for col_diff in diff.column_diffs:
            items.append(_column_impact(diff.table_name, col_diff))
    return items


def analyze_impact(diff: SchemaDiff) -> ImpactReport:
    """Produce an ImpactReport from a SchemaDiff."""
    items: List[ImpactItem] = []
    for table_diff in diff.table_diffs:
        items.extend(_table_impact(table_diff))
    return ImpactReport(items=items)
