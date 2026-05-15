"""Format rename candidates into human-readable text or dict form."""

from __future__ import annotations

from typing import Dict, List

from sqldiff_report.column_rename_detector import RenameCandidate

_ANSI_YELLOW = "\033[33m"
_ANSI_RESET = "\033[0m"


def _pct(confidence: float) -> str:
    return f"{confidence * 100:.0f}%"


def format_rename_text(
    table_name: str,
    candidates: List[RenameCandidate],
    colour: bool = True,
) -> str:
    """Return a text block describing rename candidates for one table."""
    if not candidates:
        return ""

    label = "Possible renames"
    if colour:
        label = f"{_ANSI_YELLOW}{label}{_ANSI_RESET}"

    lines = [f"  {label} in {table_name}:"]
    for rc in candidates:
        lines.append(
            f"    {rc.old_name!r} -> {rc.new_name!r}  "
            f"(confidence {_pct(rc.confidence)})"
        )
    return "\n".join(lines)


def format_rename_dict(
    table_name: str,
    candidates: List[RenameCandidate],
) -> Dict:
    """Return a serialisable dict for rename candidates of one table."""
    return {
        "table": table_name,
        "rename_candidates": [
            {
                "old_name": rc.old_name,
                "new_name": rc.new_name,
                "confidence": rc.confidence,
            }
            for rc in candidates
        ],
    }


def format_all_renames_text(
    rename_map: Dict[str, List[RenameCandidate]],
    colour: bool = True,
) -> str:
    """Concatenate rename blocks for all tables."""
    blocks = [
        format_rename_text(table, cands, colour=colour)
        for table, cands in rename_map.items()
        if cands
    ]
    return "\n".join(blocks)
