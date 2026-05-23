"""Write diff reports in Markdown or CSV format to a file or stdout."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sqldiff_report.diff_engine import SchemaDiff
from sqldiff_report.export_formats import format_csv_report, format_markdown_report


@dataclass
class ExportOptions:
    format: str = "markdown"          # "markdown" | "csv"
    output_path: Optional[Path] = None
    colour: bool = True


def write_export(diff: SchemaDiff, options: ExportOptions) -> None:
    """Render *diff* in the requested export format and write to file or stdout."""
    fmt = options.format.lower()
    if fmt == "markdown":
        content = format_markdown_report(diff, colour=options.colour)
    elif fmt == "csv":
        content = format_csv_report(diff)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'markdown' or 'csv'.")

    if options.output_path is None:
        sys.stdout.write(content)
    else:
        options.output_path.parent.mkdir(parents=True, exist_ok=True)
        options.output_path.write_text(content, encoding="utf-8")
