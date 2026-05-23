"""Export diff statistics in various machine-readable formats."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from typing import Literal

from sqldiff_report.summary_stats import DiffStats, compute_stats
from sqldiff_report.diff_engine import SchemaDiff
from sqldiff_report.severity import schema_diff_severity

OutputFormat = Literal["json", "csv", "tsv"]


def _stats_to_dict(diff: SchemaDiff) -> dict:
    """Build a flat dict of stats suitable for serialisation."""
    stats: DiffStats = compute_stats(diff)
    severity = schema_diff_severity(diff)
    return {
        "overall_severity": severity.value,
        "tables_added": len(diff.added_tables),
        "tables_removed": len(diff.removed_tables),
        "tables_modified": len(diff.modified_tables),
        "total_table_changes": stats.total_table_changes,
        "columns_added": stats.columns_added,
        "columns_removed": stats.columns_removed,
        "columns_modified": stats.columns_modified,
        "total_column_changes": stats.total_column_changes,
        "total_changes": stats.total_changes,
    }


def export_stats_json(diff: SchemaDiff, *, indent: int = 2) -> str:
    """Return diff statistics serialised as a JSON string."""
    return json.dumps(_stats_to_dict(diff), indent=indent)


def export_stats_csv(diff: SchemaDiff, *, delimiter: str = ",") -> str:
    """Return diff statistics serialised as a CSV (or TSV) string."""
    data = _stats_to_dict(diff)
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=list(data.keys()),
        delimiter=delimiter,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerow(data)
    return buf.getvalue()


def export_stats(diff: SchemaDiff, fmt: OutputFormat = "json") -> str:
    """Dispatch to the appropriate exporter based on *fmt*."""
    if fmt == "json":
        return export_stats_json(diff)
    if fmt == "tsv":
        return export_stats_csv(diff, delimiter="\t")
    if fmt == "csv":
        return export_stats_csv(diff)
    raise ValueError(f"Unsupported stats export format: {fmt!r}")
