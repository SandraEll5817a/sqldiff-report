"""Format annotation lists for text and dict output."""

from __future__ import annotations

from typing import List, Dict, Any

from sqldiff_report.annotation_engine import Annotation
from sqldiff_report.severity import Severity

_ANSI = {
    Severity.HIGH: "\033[31m",
    Severity.MEDIUM: "\033[33m",
    Severity.LOW: "\033[32m",
}
_RESET = "\033[0m"


def _label(severity: Severity, colour: bool) -> str:
    name = severity.name
    if colour:
        return f"{_ANSI[severity]}[{name}]{_RESET}"
    return f"[{name}]"


def format_annotations_text(annotations: List[Annotation], *, colour: bool = True) -> str:
    """Render annotations as a plain-text block."""
    if not annotations:
        return "No annotations."
    lines = ["Annotations:", ""]
    for ann in annotations:
        label = _label(ann.severity, colour)
        lines.append(f"  {label} {ann.target}")
        lines.append(f"      {ann.message}")
    return "\n".join(lines)


def format_annotations_dict(annotations: List[Annotation]) -> List[Dict[str, Any]]:
    """Serialise annotations to a list of plain dicts."""
    return [
        {
            "target": ann.target,
            "severity": ann.severity.name,
            "message": ann.message,
        }
        for ann in annotations
    ]
