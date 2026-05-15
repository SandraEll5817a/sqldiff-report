"""Format a DiffStats summary into human-readable text or a dict."""
from typing import Dict, Any

from sqldiff_report.summary_stats import DiffStats
from sqldiff_report.severity import Severity

_SEVERITY_COLOURS: Dict[str, str] = {
    Severity.HIGH: "\033[31m",
    Severity.MEDIUM: "\033[33m",
    Severity.LOW: "\033[32m",
}
_RESET = "\033[0m"


def _colour(text: str, severity: str, use_colour: bool) -> str:
    if not use_colour:
        return text
    code = _SEVERITY_COLOURS.get(severity, "")
    return f"{code}{text}{_RESET}"


def format_summary_text(stats: DiffStats, use_colour: bool = True) -> str:
    """Return a compact plain-text summary block."""
    sev_label = _colour(stats.overall_severity.upper(), stats.overall_severity, use_colour)
    lines = [
        "=== Schema Diff Summary ===",
        f"Overall severity : {sev_label}",
        f"Total changes    : {stats.total_changes}",
        "",
        "Tables:",
        f"  Added    : {stats.tables_added}",
        f"  Removed  : {stats.tables_removed}",
        f"  Modified : {stats.tables_modified}",
        "",
        "Columns:",
        f"  Added    : {stats.columns_added}",
        f"  Removed  : {stats.columns_removed}",
        f"  Modified : {stats.columns_modified}",
        "",
        "Severity breakdown:",
    ]
    for sev in (Severity.HIGH, Severity.MEDIUM, Severity.LOW):
        count = stats.severity_counts.get(sev, 0)
        label = _colour(sev.upper(), sev, use_colour)
        lines.append(f"  {label:<30}: {count}")
    return "\n".join(lines)


def format_summary_dict(stats: DiffStats) -> Dict[str, Any]:
    """Return a JSON-serialisable dict of the summary."""
    return {
        "overall_severity": stats.overall_severity,
        "total_changes": stats.total_changes,
        "tables": {
            "added": stats.tables_added,
            "removed": stats.tables_removed,
            "modified": stats.tables_modified,
        },
        "columns": {
            "added": stats.columns_added,
            "removed": stats.columns_removed,
            "modified": stats.columns_modified,
        },
        "severity_counts": stats.severity_counts,
    }
