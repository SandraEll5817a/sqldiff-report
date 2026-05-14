"""Parses SQL schema snapshots into structured Python objects."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ColumnDefinition:
    name: str
    col_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ColumnDefinition):
            return False
        return (
            self.name == other.name
            and self.col_type == other.col_type
            and self.nullable == other.nullable
            and self.default == other.default
            and self.primary_key == other.primary_key
        )


@dataclass
class TableDefinition:
    name: str
    columns: Dict[str, ColumnDefinition] = field(default_factory=dict)


@dataclass
class SchemaSnapshot:
    tables: Dict[str, TableDefinition] = field(default_factory=dict)


CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?\s*\(([^;]+)\)",
    re.IGNORECASE | re.DOTALL,
)
COLUMN_RE = re.compile(
    r"^\s*[`\"]?(\w+)[`\"]?\s+(\w+(?:\([^)]+\))?)\s*(.*?)\s*$",
    re.IGNORECASE,
)


def _parse_column(line: str) -> Optional[ColumnDefinition]:
    """Parse a single column definition line."""
    line = line.strip().rstrip(",")
    skip_keywords = ("PRIMARY KEY", "UNIQUE", "INDEX", "KEY", "CONSTRAINT", "CHECK", "FOREIGN")
    if any(line.upper().startswith(kw) for kw in skip_keywords):
        return None

    match = COLUMN_RE.match(line)
    if not match:
        return None

    name, col_type, rest = match.group(1), match.group(2), match.group(3).upper()
    nullable = "NOT NULL" not in rest
    primary_key = "PRIMARY KEY" in rest

    default_match = re.search(r"DEFAULT\s+(\S+)", rest, re.IGNORECASE)
    default = default_match.group(1) if default_match else None

    return ColumnDefinition(
        name=name,
        col_type=col_type,
        nullable=nullable,
        default=default,
        primary_key=primary_key,
    )


def parse_schema(sql: str) -> SchemaSnapshot:
    """Parse a SQL schema string into a SchemaSnapshot."""
    snapshot = SchemaSnapshot()
    for match in CREATE_TABLE_RE.finditer(sql):
        table_name = match.group(1)
        columns_block = match.group(2)
        table = TableDefinition(name=table_name)
        for line in columns_block.splitlines():
            col = _parse_column(line)
            if col:
                table.columns[col.name] = col
        snapshot.tables[table_name] = table
    return snapshot
