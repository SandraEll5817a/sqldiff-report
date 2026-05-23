"""Schema linter: checks a SchemaSnapshot for common design issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqldiff_report.schema_parser import SchemaSnapshot
from sqldiff_report.severity import Severity


@dataclass
class LintIssue:
    table: str
    column: str | None
    message: str
    severity: Severity


@dataclass
class LintReport:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.HIGH)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.MEDIUM)


def _check_table(table_name: str, table, issues: List[LintIssue]) -> None:
    col_names = [c.name.lower() for c in table.columns]

    # Warn if no obvious primary key column present
    pk_hints = {"id", "pk", f"{table_name.lower()}_id"}
    if not any(name in pk_hints for name in col_names):
        issues.append(
            LintIssue(
                table=table_name,
                column=None,
                message="No obvious primary key column detected (expected 'id' or '<table>_id')",
                severity=Severity.MEDIUM,
            )
        )

    for col in table.columns:
        # Flag columns with no type
        if not col.col_type or col.col_type.strip() == "":
            issues.append(
                LintIssue(
                    table=table_name,
                    column=col.name,
                    message="Column has no type definition",
                    severity=Severity.HIGH,
                )
            )

        # Warn about overly generic TEXT/BLOB without length hint
        if col.col_type and col.col_type.lower() in ("text", "blob", "clob"):
            issues.append(
                LintIssue(
                    table=table_name,
                    column=col.name,
                    message=f"Column uses unbounded type '{col.col_type}'; consider VARCHAR(n) or adding a comment",
                    severity=Severity.LOW,
                )
            )


def lint_snapshot(snapshot: SchemaSnapshot) -> LintReport:
    """Run all lint checks against *snapshot* and return a :class:`LintReport`."""
    issues: List[LintIssue] = []
    for table_name, table in snapshot.tables.items():
        _check_table(table_name, table, issues)
    return LintReport(issues=issues)
