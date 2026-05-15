"""Normalizes SQL column type strings for consistent comparison."""

import re
from typing import Optional

# Aliases map non-canonical type names to their canonical equivalents
_TYPE_ALIASES: dict[str, str] = {
    "integer": "int",
    "int4": "int",
    "int8": "bigint",
    "int2": "smallint",
    "bool": "boolean",
    "float4": "real",
    "float8": "double precision",
    "character varying": "varchar",
    "character": "char",
}


def normalize_type(raw: str) -> str:
    """Return a canonical, lower-cased type string.

    Steps applied:
    1. Strip surrounding whitespace and lower-case.
    2. Collapse internal whitespace runs to a single space.
    3. Remove spaces around parentheses and commas so that
       ``VARCHAR( 255 )`` becomes ``varchar(255)``.
    4. Apply alias substitution (longest match first).
    """
    if not raw:
        return ""

    normalised = raw.strip().lower()
    normalised = re.sub(r"\s+", " ", normalised)
    normalised = re.sub(r"\s*\(\s*", "(", normalised)
    normalised = re.sub(r"\s*\)\s*", ")", normalised)
    normalised = re.sub(r"\s*,\s*", ",", normalised)

    # Apply aliases — try longer keys first to avoid partial replacements
    for alias, canonical in sorted(_TYPE_ALIASES.items(), key=lambda kv: -len(kv[0])):
        if normalised == alias or normalised.startswith(alias + "("):
            normalised = canonical + normalised[len(alias):]
            break

    return normalised


def types_are_equivalent(a: str, b: str) -> bool:
    """Return True when two type strings are semantically equal after normalisation."""
    return normalize_type(a) == normalize_type(b)


def extract_base_type(raw: str) -> str:
    """Return the base type without any precision / scale modifier.

    ``varchar(255)`` → ``varchar``, ``numeric(10,2)`` → ``numeric``.
    """
    normalised = normalize_type(raw)
    paren_pos = normalised.find("(")
    if paren_pos == -1:
        return normalised
    return normalised[:paren_pos]


def extract_precision(raw: str) -> Optional[tuple[int, ...]]:
    """Return a tuple of integer precision/scale values, or None if absent.

    ``varchar(255)`` → ``(255,)``, ``numeric(10,2)`` → ``(10, 2)``.
    """
    normalised = normalize_type(raw)
    match = re.search(r"\(([^)]+)\)", normalised)
    if not match:
        return None
    try:
        return tuple(int(p.strip()) for p in match.group(1).split(","))
    except ValueError:
        return None
