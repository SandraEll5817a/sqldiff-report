"""ANSI-coloured badge helpers for severity levels."""

from sqldiff_report.severity import Severity

_ANSI_RESET = "\033[0m"
_ANSI_RED = "\033[31m"
_ANSI_YELLOW = "\033[33m"
_ANSI_CYAN = "\033[36m"

_COLOUR_MAP = {
    Severity.HIGH: _ANSI_RED,
    Severity.MEDIUM: _ANSI_YELLOW,
    Severity.LOW: _ANSI_CYAN,
}

_LABEL_MAP = {
    Severity.HIGH: "[HIGH]",
    Severity.MEDIUM: "[MEDIUM]",
    Severity.LOW: "[LOW]",
}


def severity_badge(severity: Severity, *, colour: bool = True) -> str:
    """Return a printable badge string for *severity*."""
    label = _LABEL_MAP[severity]
    if not colour:
        return label
    ansi = _COLOUR_MAP[severity]
    return f"{ansi}{label}{_ANSI_RESET}"


def badge_for_table(table_name: str, severity: Severity, *, colour: bool = True) -> str:
    """Return a formatted line combining table name and severity badge."""
    badge = severity_badge(severity, colour=colour)
    return f"{badge} {table_name}"
