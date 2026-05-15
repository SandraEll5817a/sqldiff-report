"""Output writer module for sqldiff-report.

Handles writing formatted reports to various destinations:
stdout, file, or structured JSON output.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, TextIO

from sqldiff_report.diff_engine import SchemaDiff
from sqldiff_report.report_formatter import format_report


@dataclass
class WriteOptions:
    output_path: Optional[Path] = None
    output_format: str = "text"  # "text" or "json"
    no_color: bool = False


def _diff_to_dict(diff: SchemaDiff) -> dict:
    """Convert a SchemaDiff to a JSON-serialisable dictionary."""
    return {
        "added_tables": [
            {"name": t.name, "columns": [{"name": c.name, "type": c.col_type, "nullable": c.nullable, "default": c.default} for c in t.columns]}
            for t in diff.added_tables
        ],
        "removed_tables": [
            {"name": t.name}
            for t in diff.removed_tables
        ],
        "modified_tables": [
            {
                "name": td.name,
                "added_columns": [{"name": c.name, "type": c.col_type, "nullable": c.nullable, "default": c.default} for c in td.added_columns],
                "removed_columns": [{"name": c.name, "type": c.col_type, "nullable": c.nullable, "default": c.default} for c in td.removed_columns],
                "modified_columns": [
                    {"name": cd.name, "before": {"type": cd.before.col_type, "nullable": cd.before.nullable, "default": cd.before.default}, "after": {"type": cd.after.col_type, "nullable": cd.after.nullable, "default": cd.after.default}}
                    for cd in td.modified_columns
                ],
            }
            for td in diff.modified_tables
        ],
    }


def write_report(diff: SchemaDiff, options: WriteOptions) -> None:
    """Write the diff report according to the provided options."""
    if options.output_format == "json":
        content = json.dumps(_diff_to_dict(diff), indent=2)
    else:
        content = format_report(diff)

    if options.output_path is not None:
        options.output_path.write_text(content, encoding="utf-8")
    else:
        print(content)
