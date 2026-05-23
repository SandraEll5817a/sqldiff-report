"""Write rollback hints to stdout or a file in text or JSON format."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from sqldiff_report.diff_engine import SchemaDiff
from sqldiff_report.rollback_hint_generator import (
    RollbackHint,
    format_rollback_hints_text,
    generate_rollback_hints,
)


@dataclass
class RollbackWriteOptions:
    fmt: str = "text"          # "text" | "json"
    output_path: Optional[Path] = None
    colour: bool = True


def _hints_to_dict(hints: List[RollbackHint]) -> dict:
    return {
        "rollback_hints": [
            {"table": h.table, "description": h.description, "sql": h.sql}
            for h in hints
        ]
    }


def write_rollback_hints(diff: SchemaDiff, options: RollbackWriteOptions) -> None:
    """Generate and write rollback hints according to *options*."""
    hints = generate_rollback_hints(diff)

    if options.fmt == "json":
        content = json.dumps(_hints_to_dict(hints), indent=2)
    else:
        content = format_rollback_hints_text(hints, colour=options.colour)

    if options.output_path:
        options.output_path.write_text(content, encoding="utf-8")
    else:
        print(content)
