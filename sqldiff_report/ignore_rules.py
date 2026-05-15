"""Ignore rules for filtering out tables/columns from diff reports."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List


@dataclass
class IgnoreRules:
    """Holds patterns for tables and columns to ignore during diffing."""

    tables: List[str] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)

    def should_ignore_table(self, table_name: str) -> bool:
        """Return True if the table matches any ignore pattern."""
        return any(fnmatch.fnmatch(table_name, pattern) for pattern in self.tables)

    def should_ignore_column(self, table_name: str, column_name: str) -> bool:
        """Return True if the column matches any ignore pattern.

        Patterns can be plain column names (e.g. ``updated_at``) or
        ``table.column`` qualified patterns (e.g. ``audit_log.*``).
        """
        qualified = f"{table_name}.{column_name}"
        for pattern in self.columns:
            if "." in pattern:
                if fnmatch.fnmatch(qualified, pattern):
                    return True
            else:
                if fnmatch.fnmatch(column_name, pattern):
                    return True
        return False


def rules_from_config(config_dict: dict) -> IgnoreRules:
    """Build an :class:`IgnoreRules` instance from a config mapping.

    Expected keys (both optional):
    - ``ignore_tables``: list of glob patterns
    - ``ignore_columns``: list of glob patterns
    """
    tables = config_dict.get("ignore_tables", [])
    columns = config_dict.get("ignore_columns", [])
    return IgnoreRules(tables=list(tables), columns=list(columns))
