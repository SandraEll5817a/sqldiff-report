"""Renders a SchemaDiff as a self-contained HTML report."""
from __future__ import annotations

import html
from typing import Iterable

from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff
from sqldiff_report.severity import (
    Severity,
    column_diff_severity,
    schema_diff_severity,
    table_diff_severity,
)

_SEVERITY_COLOUR: dict[Severity, str] = {
    Severity.HIGH: "#c0392b",
    Severity.MEDIUM: "#e67e22",
    Severity.LOW: "#27ae60",
    Severity.NONE: "#7f8c8d",
}

_CSS = """
body{font-family:sans-serif;margin:2rem;color:#222}
h1{border-bottom:2px solid #333;padding-bottom:.4rem}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;color:#fff;font-size:.8rem;font-weight:bold}
.table-block{margin-bottom:1.5rem;border:1px solid #ddd;border-radius:6px;overflow:hidden}
.table-header{padding:.5rem 1rem;font-weight:bold;display:flex;justify-content:space-between;align-items:center}
.table-body{padding:.5rem 1rem}
table{border-collapse:collapse;width:100%}
th,td{text-align:left;padding:4px 8px;border-bottom:1px solid #eee}
th{background:#f5f5f5}
.added{color:#27ae60} .removed{color:#c0392b} .changed{color:#e67e22}
"""


def _badge(severity: Severity) -> str:
    colour = _SEVERITY_COLOUR[severity]
    label = html.escape(severity.value.upper())
    return f'<span class="badge" style="background:{colour}">{label}</span>'


def _column_rows(diffs: Iterable[ColumnDiff]) -> str:
    rows: list[str] = []
    for cd in diffs:
        sev = column_diff_severity(cd)
        colour = _SEVERITY_COLOUR[sev]
        if cd.old_column is None:
            desc = f'<span class="added">+ added</span>'
        elif cd.new_column is None:
            desc = f'<span class="removed">- removed</span>'
        else:
            parts: list[str] = []
            if cd.old_column.col_type != cd.new_column.col_type:
                parts.append(
                    f'type: <span class="removed">{html.escape(cd.old_column.col_type)}</span>'
                    f' → <span class="added">{html.escape(cd.new_column.col_type)}</span>'
                )
            if cd.old_column.nullable != cd.new_column.nullable:
                parts.append(
                    f'nullable: <span class="removed">{cd.old_column.nullable}</span>'
                    f' → <span class="added">{cd.new_column.nullable}</span>'
                )
            desc = "; ".join(parts) or "changed"
        rows.append(
            f"<tr><td>{html.escape(cd.column_name)}</td>"
            f'<td style="color:{colour}">{desc}</td></tr>'
        )
    return "\n".join(rows)


def _table_block(td: TableDiff) -> str:
    sev = table_diff_severity(td)
    colour = _SEVERITY_COLOUR[sev]
    header_bg = colour + "22"  # light tint
    body = ""
    if td.added_columns or td.removed_columns or td.modified_columns:
        all_col_diffs = (
            [ColumnDiff(c.name, None, c) for c in td.added_columns]
            + [ColumnDiff(c.name, c, None) for c in td.removed_columns]
            + td.modified_columns
        )
        body = (
            "<table><thead><tr><th>Column</th><th>Change</th></tr></thead><tbody>"
            + _column_rows(all_col_diffs)
            + "</tbody></table>"
        )
    status = "added" if td.old_table is None else ("removed" if td.new_table is None else "modified")
    return (
        f'<div class="table-block">'
        f'<div class="table-header" style="background:{header_bg}">'
        f'<span>{html.escape(td.table_name)}</span>'
        f'<span>{_badge(sev)}&nbsp;<em>{status}</em></span></div>'
        f'<div class="table-body">{body}</div></div>'
    )


def format_html_report(diff: SchemaDiff, title: str = "Schema Diff Report") -> str:
    """Return a complete HTML document string for *diff*."""
    overall = schema_diff_severity(diff)
    table_blocks = "".join(_table_block(td) for td in diff.table_diffs)
    if not table_blocks:
        table_blocks = "<p>No schema changes detected.</p>"
    escaped_title = html.escape(title)
    return (
        f"<!DOCTYPE html><html lang='en'><head>"
        f"<meta charset='UTF-8'><title>{escaped_title}</title>"
        f"<style>{_CSS}</style></head><body>"
        f"<h1>{escaped_title} {_badge(overall)}</h1>"
        f"{table_blocks}"
        f"</body></html>"
    )
