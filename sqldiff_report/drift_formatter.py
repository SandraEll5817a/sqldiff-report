"""Formats a DriftReport for human-readable and machine-readable output."""

from __future__ import annotations

from typing import Dict, Any, List

from sqldiff_report.drift_detector import DriftReport, DriftItem
from sqldiff_report.severity import Severity

_ANSI = {
    Severity.HIGH: "\033[31m",
    Severity.MEDIUM: "\033[33m",
    Severity.LOW: "\033[32m",
}
_RESET = "\033[0m"


def _severity_label(sev: Severity, colour: bool = True) -> str:
    label = sev.value.upper()
    if colour:
        return f"{_ANSI[sev]}{label}{_RESET}"
    return label


def format_drift_text(report: DriftReport, colour: bool = True) -> str:
    """Return a human-readable, optionally colourised summary of *report*.

    Args:
        report: The :class:`DriftReport` produced by the drift detector.
        colour: When ``True`` (default), ANSI colour codes are embedded in the
            output so severity labels are highlighted in a terminal.  Pass
            ``False`` when writing to a file or a non-TTY stream.

    Returns:
        A multi-line string suitable for printing to stdout.
    """
    lines: List[str] = []
    baseline_info = f" (baseline: {report.baseline_label})" if report.baseline_label else ""
    lines.append(f"=== Schema Drift Report{baseline_info} ===")

    if not report.has_drift:
        lines.append("  No drift detected — schema matches baseline.")
        return "\n".join(lines)

    lines.append(f"  Overall severity: {_severity_label(report.max_severity, colour)}")
    lines.append(f"  Drifted tables: {len(report.items)}")
    lines.append("")

    for item in sorted(report.items, key=lambda i: i.table_name):
        sev_str = _severity_label(item.severity, colour)
        lines.append(f"  [{sev_str}] {item.table_name}: {item.description}")

    return "\n".join(lines)


def format_drift_dict(report: DriftReport) -> Dict[str, Any]:
    """Serialise *report* to a plain dictionary suitable for JSON output.

    Returns:
        A dictionary with the following keys:

        * ``baseline_label`` – the label of the baseline schema, or ``None``.
        * ``has_drift`` – ``True`` when at least one drift item was detected.
        * ``max_severity`` – the highest severity value string, or ``None``.
        * ``drifted_tables`` – list of dicts, each containing ``table``,
          ``description``, and ``severity``.
    """
    return {
        "baseline_label": report.baseline_label,
        "has_drift": report.has_drift,
        "max_severity": report.max_severity.value if report.has_drift else None,
        "drifted_tables": [
            {
                "table": item.table_name,
                "description": item.description,
                "severity": item.severity.value,
            }
            for item in sorted(report.items, key=lambda i: i.table_name)
        ],
    }
