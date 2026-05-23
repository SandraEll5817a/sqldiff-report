"""Formats column lineage data for human-readable and dict output."""
from __future__ import annotations

from typing import Dict, List

from sqldiff_report.column_lineage_tracker import LineageEntry, TableLineage

_EVENT_SYMBOL = {
    "added": "+",
    "removed": "-",
    "renamed": "~",
    "modified": "*",
    "unchanged": " ",
}


def _entry_line(entry: LineageEntry, colour: bool = True) -> str:
    symbol = _EVENT_SYMBOL.get(entry.event, "?")
    ansi = {
        "+": "\033[32m",
        "-": "\033[31m",
        "~": "\033[33m",
        "*": "\033[36m",
        " ": "",
    }
    reset = "\033[0m"

    if entry.event == "renamed" and entry.origin_column:
        pct = f"{entry.confidence * 100:.0f}%" if entry.confidence is not None else "?"
        detail = f"{entry.origin_column} -> {entry.column} ({pct} confidence)"
    elif entry.event in ("added", "removed"):
        detail = entry.column
    else:
        detail = entry.column

    if colour:
        code = ansi.get(symbol, "")
        return f"  {code}{symbol} {detail}{reset}"
    return f"  {symbol} {detail}"


def format_lineage_text(
    lineage: Dict[str, TableLineage],
    colour: bool = True,
) -> str:
    if not lineage:
        return "No column lineage changes detected."

    lines: List[str] = []
    for table_name, tl in sorted(lineage.items()):
        lines.append(f"Table: {table_name}")
        if not tl.entries:
            lines.append("  (no column changes)")
        else:
            for entry in sorted(tl.entries, key=lambda e: e.column):
                lines.append(_entry_line(entry, colour=colour))
        lines.append("")

    return "\n".join(lines).rstrip()


def format_lineage_dict(
    lineage: Dict[str, TableLineage],
) -> List[dict]:
    result = []
    for table_name, tl in sorted(lineage.items()):
        entries = []
        for e in sorted(tl.entries, key=lambda x: x.column):
            entry_dict: dict = {
                "column": e.column,
                "event": e.event,
                "origin_column": e.origin_column,
            }
            if e.confidence is not None:
                entry_dict["confidence"] = round(e.confidence, 4)
            entries.append(entry_dict)
        result.append({"table": table_name, "columns": entries})
    return result
