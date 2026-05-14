"""Formats a SchemaDiff into a human-readable text report."""

from sqldiff_report.diff_engine import ColumnDiff, SchemaDiff, TableDiff

SECTION_SEP = "=" * 60
SUB_SEP = "-" * 40


def _format_column(col) -> str:
    if col is None:
        return "N/A"
    parts = [col.col_type]
    if col.primary_key:
        parts.append("PRIMARY KEY")
    if not col.nullable:
        parts.append("NOT NULL")
    if col.default is not None:
        parts.append(f"DEFAULT {col.default}")
    return " ".join(parts)


def _format_column_diff(diff: ColumnDiff) -> str:
    if diff.change_type == "added":
        return f"  [+] {diff.column_name}: {_format_column(diff.new_column)}"
    elif diff.change_type == "removed":
        return f"  [-] {diff.column_name}: {_format_column(diff.old_column)}"
    else:
        old_str = _format_column(diff.old_column)
        new_str = _format_column(diff.new_column)
        return f"  [~] {diff.column_name}:\n      Before: {old_str}\n      After:  {new_str}"


def _format_table_diff(diff: TableDiff) -> str:
    lines = []
    if diff.change_type == "added":
        lines.append(f"[TABLE ADDED] {diff.table_name}")
    elif diff.change_type == "removed":
        lines.append(f"[TABLE REMOVED] {diff.table_name}")
    else:
        lines.append(f"[TABLE MODIFIED] {diff.table_name}")
        lines.append(SUB_SEP)
        for col_diff in sorted(diff.column_diffs, key=lambda c: c.column_name):
            lines.append(_format_column_diff(col_diff))
    return "\n".join(lines)


def format_report(diff: SchemaDiff, title: str = "Schema Diff Report") -> str:
    """Render a SchemaDiff as a human-readable string report."""
    lines = [
        SECTION_SEP,
        f"  {title}",
        SECTION_SEP,
    ]

    if not diff.has_changes:
        lines.append("No schema changes detected.")
        lines.append(SECTION_SEP)
        return "\n".join(lines)

    added = [t for t in diff.table_diffs if t.change_type == "added"]
    removed = [t for t in diff.table_diffs if t.change_type == "removed"]
    modified = [t for t in diff.table_diffs if t.change_type == "modified"]

    summary_parts = []
    if added:
        summary_parts.append(f"{len(added)} table(s) added")
    if removed:
        summary_parts.append(f"{len(removed)} table(s) removed")
    if modified:
        summary_parts.append(f"{len(modified)} table(s) modified")
    lines.append("Summary: " + ", ".join(summary_parts))
    lines.append(SECTION_SEP)

    for table_diff in diff.table_diffs:
        lines.append(_format_table_diff(table_diff))
        lines.append("")

    lines.append(SECTION_SEP)
    return "\n".join(lines)
