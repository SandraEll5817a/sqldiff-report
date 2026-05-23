"""Exporters for additional output formats: Markdown and CSV."""
from __future__ import annotations

from typing import List

from sqldiff_report.diff_engine import SchemaDiff, TableDiff
from sqldiff_report.severity import table_diff_severity, schema_diff_severity


def _table_diff_to_markdown(td: TableDiff) -> List[str]:
    lines: List[str] = []
    severity = table_diff_severity(td)
    if td.added:
        lines.append(f"### ➕ `{td.table_name}` — added  `[{severity.name}]`")
    elif td.removed:
        lines.append(f"### ➖ `{td.table_name}` — removed  `[{severity.name}]`")
    else:
        lines.append(f"### ✏️ `{td.table_name}` — modified  `[{severity.name}]`")
        if td.column_diffs:
            lines.append("")
            lines.append("| Column | Change | Old | New |")
            lines.append("|--------|--------|-----|-----|")
            for cd in td.column_diffs:
                old_type = cd.old_type or ""
                new_type = cd.new_type or ""
                old_null = str(cd.old_nullable) if cd.old_nullable is not None else ""
                new_null = str(cd.new_nullable) if cd.new_nullable is not None else ""
                if cd.added:
                    lines.append(f"| `{cd.column_name}` | added | | `{new_type}` |")
                elif cd.removed:
                    lines.append(f"| `{cd.column_name}` | removed | `{old_type}` | |")
                else:
                    detail = f"type: `{old_type}` → `{new_type}`" if old_type != new_type else ""
                    if old_null != new_null:
                        detail += f" nullable: {old_null} → {new_null}"
                    lines.append(f"| `{cd.column_name}` | modified | {detail} | |")
    lines.append("")
    return lines


def format_markdown_report(diff: SchemaDiff, *, colour: bool = False) -> str:
    """Return a Markdown-formatted diff report string."""
    overall = schema_diff_severity(diff)
    header = [
        "# Schema Diff Report",
        "",
        f"**Overall severity:** `{overall.name}`  ",
        f"**Tables added:** {len(diff.added_tables)}  ",
        f"**Tables removed:** {len(diff.removed_tables)}  ",
        f"**Tables modified:** {len(diff.modified_tables)}  ",
        "",
    ]
    if not diff.added_tables and not diff.removed_tables and not diff.modified_tables:
        return "\n".join(header) + "_No schema changes detected._\n"

    body: List[str] = []
    for td in diff.added_tables + diff.removed_tables + diff.modified_tables:
        body.extend(_table_diff_to_markdown(td))

    return "\n".join(header + body)


def format_csv_report(diff: SchemaDiff) -> str:
    """Return a CSV-formatted diff report string."""
    rows = ["table,change_type,column,old_type,new_type,old_nullable,new_nullable,severity"]
    for td in diff.added_tables:
        sev = table_diff_severity(td).name
        rows.append(f"{td.table_name},TABLE_ADDED,,,,,, {sev}")
    for td in diff.removed_tables:
        sev = table_diff_severity(td).name
        rows.append(f"{td.table_name},TABLE_REMOVED,,,,,,{sev}")
    for td in diff.modified_tables:
        sev = table_diff_severity(td).name
        if not td.column_diffs:
            rows.append(f"{td.table_name},TABLE_MODIFIED,,,,,,{sev}")
        for cd in td.column_diffs:
            change = "COLUMN_ADDED" if cd.added else ("COLUMN_REMOVED" if cd.removed else "COLUMN_MODIFIED")
            rows.append(
                f"{td.table_name},{change},{cd.column_name},"
                f"{cd.old_type or ''},{cd.new_type or ''},"
                f"{cd.old_nullable if cd.old_nullable is not None else ''},"
                f"{cd.new_nullable if cd.new_nullable is not None else ''},"
                f"{sev}"
            )
    return "\n".join(rows) + "\n"
