"""Formats an ImpactReport for human-readable or dict output."""

from __future__ import annotations

from typing import Dict, Any, List

from sqldiff_report.impact_analyzer import ImpactReport, ImpactItem
from sqldiff_report.severity import Severity

_ANSI = {
    Severity.HIGH: "\033[31m",
    Severity.MEDIUM: "\033[33m",
    Severity.LOW: "\033[36m",
}
_RESET = "\033[0m"


def _severity_label(sev: Severity, colour: bool) -> str:
    label = f"[{sev.value.upper()}]"
    if colour and sev in _ANSI:
        return f"{_ANSI[sev]}{label}{_RESET}"
    return label


def _item_lines(item: ImpactItem, colour: bool) -> List[str]:
    badge = _severity_label(item.severity, colour)
    lines = [
        f"  {badge} {item.description}",
        f"    → {item.recommendation}",
    ]
    return lines


def format_impact_text(report: ImpactReport, *, colour: bool = True) -> str:
    """Return a plain-text impact report."""
    if not report.items:
        return "No impact items detected."

    sections: List[str] = []
    sections.append(
        f"Impact Analysis  "
        f"(HIGH: {report.high_count}, "
        f"MEDIUM: {report.medium_count}, "
        f"LOW: {report.low_count})"
    )
    sections.append("-" * 60)

    current_table = None
    for item in report.items:
        if item.table != current_table:
            current_table = item.table
            sections.append(f"\nTable: {item.table}")
        sections.extend(_item_lines(item, colour))

    if report.has_breaking_changes:
        warning = "⚠  Breaking changes detected — review HIGH severity items before migrating."
        if colour:
            warning = f"{_ANSI[Severity.HIGH]}{warning}{_RESET}"
        sections.append(f"\n{warning}")

    return "\n".join(sections)


def format_impact_dict(report: ImpactReport) -> Dict[str, Any]:
    """Return a serialisable dict representation of the impact report."""
    return {
        "has_breaking_changes": report.has_breaking_changes,
        "summary": {
            "high": report.high_count,
            "medium": report.medium_count,
            "low": report.low_count,
        },
        "items": [
            {
                "table": i.table,
                "column": i.column,
                "change_type": i.change_type,
                "severity": i.severity.value,
                "description": i.description,
                "recommendation": i.recommendation,
            }
            for i in report.items
        ],
    }
