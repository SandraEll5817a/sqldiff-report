"""Compute summary statistics from a SchemaDiff for reporting."""
from dataclasses import dataclass, field
from typing import Dict

from sqldiff_report.diff_engine import SchemaDiff
from sqldiff_report.severity import Severity, schema_diff_severity, table_diff_severity


@dataclass
class DiffStats:
    tables_added: int = 0
    tables_removed: int = 0
    tables_modified: int = 0
    columns_added: int = 0
    columns_removed: int = 0
    columns_modified: int = 0
    severity_counts: Dict[str, int] = field(default_factory=dict)
    overall_severity: str = Severity.LOW

    @property
    def total_table_changes(self) -> int:
        return self.tables_added + self.tables_removed + self.tables_modified

    @property
    def total_column_changes(self) -> int:
        return self.columns_added + self.columns_removed + self.columns_modified

    @property
    def total_changes(self) -> int:
        return self.total_table_changes + self.total_column_changes


def compute_stats(diff: SchemaDiff) -> DiffStats:
    """Return a DiffStats summary for the given SchemaDiff."""
    stats = DiffStats()
    severity_counts: Dict[str, int] = {s: 0 for s in (Severity.LOW, Severity.MEDIUM, Severity.HIGH)}

    for table_diff in diff.added_tables:
        stats.tables_added += 1
        sev = table_diff_severity(table_diff)
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    for table_diff in diff.removed_tables:
        stats.tables_removed += 1
        sev = table_diff_severity(table_diff)
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    for table_diff in diff.modified_tables:
        stats.tables_modified += 1
        for col_diff in table_diff.column_diffs:
            if col_diff.added:
                stats.columns_added += 1
            elif col_diff.removed:
                stats.columns_removed += 1
            else:
                stats.columns_modified += 1
        sev = table_diff_severity(table_diff)
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    stats.severity_counts = severity_counts
    stats.overall_severity = schema_diff_severity(diff)
    return stats
