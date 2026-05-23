"""Writes a dependency graph report to stdout or a file."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sqldiff_report.dependency_graph import DependencyGraph
from sqldiff_report.dependency_formatter import (
    format_dependency_dict,
    format_dependency_text,
)


@dataclass
class DependencyWriteOptions:
    fmt: str = "text"          # "text" | "json"
    colour: bool = True
    output_path: Optional[Path] = None


def write_dependency_report(
    graph: DependencyGraph,
    options: DependencyWriteOptions,
) -> None:
    """Serialise *graph* according to *options* and write to the destination."""
    if options.fmt == "json":
        content = json.dumps(format_dependency_dict(graph), indent=2)
    else:
        content = format_dependency_text(graph, colour=options.colour)

    if options.output_path is None:
        print(content)
    else:
        options.output_path.write_text(content, encoding="utf-8")
