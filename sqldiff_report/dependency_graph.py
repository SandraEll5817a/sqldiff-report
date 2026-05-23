"""Builds a simple dependency graph between tables based on column naming
conventions (e.g. `user_id` implies a dependency on `users`)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from sqldiff_report.diff_engine import SchemaDiff, TableDiff


@dataclass
class TableNode:
    name: str
    depends_on: List[str] = field(default_factory=list)
    depended_on_by: List[str] = field(default_factory=list)


@dataclass
class DependencyGraph:
    nodes: Dict[str, TableNode] = field(default_factory=dict)

    def table_names(self) -> List[str]:
        return sorted(self.nodes.keys())

    def dependencies_of(self, table: str) -> List[str]:
        node = self.nodes.get(table)
        return node.depends_on if node else []

    def dependents_of(self, table: str) -> List[str]:
        node = self.nodes.get(table)
        return node.depended_on_by if node else []


def _infer_referenced_table(column_name: str, known_tables: Set[str]) -> str | None:
    """Return a table name if *column_name* looks like a FK column."""
    if not column_name.endswith("_id"):
        return None
    candidate = column_name[:-3]  # strip "_id"
    # try plural form first, then singular
    for name in (candidate + "s", candidate):
        if name in known_tables:
            return name
    return None


def _all_table_names(diff: SchemaDiff) -> Set[str]:
    names: Set[str] = set()
    for td in diff.added_tables + diff.removed_tables + diff.modified_tables:
        names.add(td.table_name)
    return names


def build_dependency_graph(diff: SchemaDiff) -> DependencyGraph:
    """Analyse column names in *diff* and build a table dependency graph."""
    all_tables = _all_table_names(diff)
    graph = DependencyGraph()

    for table_name in all_tables:
        graph.nodes[table_name] = TableNode(name=table_name)

    all_diffs: List[TableDiff] = (
        diff.added_tables + diff.removed_tables + diff.modified_tables
    )

    for td in all_diffs:
        # Collect column names from added/removed/modified columns
        col_names: Set[str] = set()
        for col in td.added_columns:
            col_names.add(col.name)
        for col in td.removed_columns:
            col_names.add(col.name)
        for cd in td.modified_columns:
            col_names.add(cd.column_name)

        for col_name in col_names:
            ref = _infer_referenced_table(col_name, all_tables)
            if ref and ref != td.table_name:
                node = graph.nodes[td.table_name]
                if ref not in node.depends_on:
                    node.depends_on.append(ref)
                ref_node = graph.nodes.get(ref)
                if ref_node and td.table_name not in ref_node.depended_on_by:
                    ref_node.depended_on_by.append(td.table_name)

    return graph
