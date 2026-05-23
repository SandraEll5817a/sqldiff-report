"""Format VersionTag results for human-readable and dict output."""
from __future__ import annotations

from sqldiff_report.schema_version_tagger import VersionTag

_ANSI_BOLD = "\033[1m"
_ANSI_GREEN = "\033[32m"
_ANSI_YELLOW = "\033[33m"
_ANSI_RED = "\033[31m"
_ANSI_RESET = "\033[0m"


def _colour(text: str, code: str, use_colour: bool) -> str:
    if not use_colour:
        return text
    return f"{code}{text}{_ANSI_RESET}"


def format_version_text(
    current: str,
    suggested: VersionTag,
    *,
    use_colour: bool = True,
) -> str:
    """Return a human-readable version suggestion block."""
    lines: list[str] = []
    lines.append(_colour("Schema Version Suggestion", _ANSI_BOLD, use_colour))
    lines.append(f"  Current  : {current}")

    if suggested.label == current:
        version_str = _colour(suggested.label, _ANSI_GREEN, use_colour)
        lines.append(f"  Suggested: {version_str}  (no change needed)")
    else:
        bump_kind = _detect_bump_kind(current, suggested)
        colour = _ANSI_RED if bump_kind == "major" else (
            _ANSI_YELLOW if bump_kind == "minor" else _ANSI_GREEN
        )
        version_str = _colour(suggested.label, colour, use_colour)
        lines.append(f"  Suggested: {version_str}  [{bump_kind} bump]")

    if suggested.notes:
        lines.append("  Reasons:")
        for note in suggested.notes:
            lines.append(f"    - {note}")

    return "\n".join(lines)


def format_version_dict(current: str, suggested: VersionTag) -> dict:
    """Return a dict representation of the version suggestion."""
    return {
        "current": current,
        "suggested": suggested.label,
        "bump_kind": _detect_bump_kind(current, suggested),
        "notes": list(suggested.notes),
    }


def _detect_bump_kind(current: str, suggested: VersionTag) -> str:
    from sqldiff_report.schema_version_tagger import parse_version
    cur = parse_version(current)
    if cur is None or suggested.label == current:
        return "none"
    if suggested.major > cur.major:
        return "major"
    if suggested.minor > cur.minor:
        return "minor"
    if suggested.patch > cur.patch:
        return "patch"
    return "none"
