"""Formats a DependencyGraph as human-readable text or a dict."""

from __future__ import annotations

from typing import Any, Dict, List

from sqldiff_report.dependency_graph import DependencyGraph

_PLACEHOLDER = "(no inter-table dependencies detected)"


def _arrow_lines(graph: DependencyGraph) -> List[str]:
    lines: List[str] = []
    for name in graph.table_names():
        node = graph.nodes[name]
        for dep in sorted(node.depends_on):
            lines.append(f"  {name}  -->  {dep}")
    return lines


def format_dependency_text(graph: DependencyGraph, *, colour: bool = True) -> str:
    """Return a plain-text representation of the dependency graph."""
    lines = _arrow_lines(graph)
    if not lines:
        return _PLACEHOLDER

    header = "Table Dependency Graph"
    if colour:
        header = f"\033[1;36m{header}\033[0m"

    parts = [header, "-" * len("Table Dependency Graph")]
    parts.extend(lines)
    return "\n".join(parts)


def format_dependency_dict(graph: DependencyGraph) -> Dict[str, Any]:
    """Return a JSON-serialisable dict representation."""
    result: Dict[str, Any] = {}
    for name in graph.table_names():
        node = graph.nodes[name]
        result[name] = {
            "depends_on": sorted(node.depends_on),
            "depended_on_by": sorted(node.depended_on_by),
        }
    return result
