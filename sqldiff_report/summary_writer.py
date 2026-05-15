"""Write a summary section to stdout or prepend it to an output file."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from sqldiff_report.diff_engine import SchemaDiff
from sqldiff_report.summary_stats import compute_stats
from sqldiff_report.summary_formatter import format_summary_text, format_summary_dict


def write_summary(
    diff: SchemaDiff,
    *,
    output_format: str = "text",
    use_colour: bool = True,
    output_path: Optional[Path] = None,
) -> None:
    """Compute and emit a summary for *diff*.

    Parameters
    ----------
    diff:
        The computed SchemaDiff to summarise.
    output_format:
        ``"text"`` (default) or ``"json"``.
    use_colour:
        Emit ANSI colour codes when *output_format* is ``"text"``.
    output_path:
        If given, write to this file instead of stdout.
    """
    stats = compute_stats(diff)

    if output_format == "json":
        content = json.dumps(format_summary_dict(stats), indent=2)
    else:
        content = format_summary_text(stats, use_colour=use_colour)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            fh.write(content)
            fh.write("\n")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")
