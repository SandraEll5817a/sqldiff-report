"""Attach human-readable annotations to diff entries based on risk heuristics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqldiff_report.diff_engine import ColumnDiff, TableDiff, SchemaDiff
from sqldiff_report.severity import Severity, column_diff_severity, table_diff_severity


@dataclass
class Annotation:
    """A single advisory note attached to a diff entry."""

    target: str          # e.g. "users.email" or "orders"
    severity: Severity
    message: str


_DESTRUCTIVE_TYPES = {"drop", "truncate", "delete"}


def _annotate_column(table_name: str, diff: ColumnDiff) -> List[Annotation]:
    annotations: List[Annotation] = []
    sev = column_diff_severity(diff)
    target = f"{table_name}.{diff.column_name}"

    if diff.old_definition is None:
        annotations.append(Annotation(target, Severity.LOW, "New column added; verify default value handling."))
    elif diff.new_definition is None:
        annotations.append(Annotation(target, Severity.HIGH, "Column removed; ensure no application code references it."))
    else:
        old, new = diff.old_definition, diff.new_definition
        if old.col_type != new.col_type:
            annotations.append(
                Annotation(target, Severity.HIGH,
                           f"Type changed from '{old.col_type}' to '{new.col_type}'; data migration may be required.")
            )
        if old.nullable and not new.nullable:
            annotations.append(
                Annotation(target, Severity.HIGH,
                           "Column became NOT NULL; backfill existing rows before applying migration.")
            )
        if not old.nullable and new.nullable:
            annotations.append(
                Annotation(target, Severity.LOW, "Column relaxed to nullable; generally safe.")
            )
    return annotations


def _annotate_table(diff: TableDiff) -> List[Annotation]:
    annotations: List[Annotation] = []
    if diff.added:
        annotations.append(Annotation(diff.table_name, Severity.LOW, "New table; remember to grant appropriate permissions."))
    elif diff.removed:
        annotations.append(Annotation(diff.table_name, Severity.HIGH, "Table removed; confirm all foreign-key references are dropped first."))
    else:
        for col_diff in diff.column_diffs:
            annotations.extend(_annotate_column(diff.table_name, col_diff))
    return annotations


def annotate_diff(schema_diff: SchemaDiff) -> List[Annotation]:
    """Return all annotations for a full schema diff."""
    result: List[Annotation] = []
    for table_diff in schema_diff.table_diffs:
        result.extend(_annotate_table(table_diff))
    return result
