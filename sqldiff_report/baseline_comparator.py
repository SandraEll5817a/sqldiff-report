"""Compare a current SchemaDiff against a saved baseline to surface regressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Set

from sqldiff_report.baseline_manager import BaselineEntry
from sqldiff_report.diff_engine import SchemaDiff, TableDiff


@dataclass
class BaselineComparison:
    baseline_name: str
    new_tables: list[str]
    """Tables present in current diff but absent from baseline."""
    resolved_tables: list[str]
    """Tables present in baseline diff but no longer in current diff."""
    persisting_tables: list[str]
    """Tables with changes in both baseline and current diff."""

    @property
    def has_regressions(self) -> bool:
        return bool(self.new_tables)


def _changed_table_names(diff: SchemaDiff) -> Set[str]:
    names: Set[str] = set()
    names.update(diff.added_tables)
    names.update(diff.removed_tables)
    names.update(t.table_name for t in diff.modified_tables)
    return names


def _changed_table_names_from_dict(diff_dict: dict) -> Set[str]:
    names: Set[str] = set()
    names.update(diff_dict.get("added_tables", []))
    names.update(diff_dict.get("removed_tables", []))
    for t in diff_dict.get("modified_tables", []):
        names.add(t["table_name"])
    return names


def compare_against_baseline(
    current: SchemaDiff,
    baseline: BaselineEntry,
) -> BaselineComparison:
    """Diff the current schema diff against a saved baseline entry."""
    current_tables = _changed_table_names(current)
    baseline_tables = _changed_table_names_from_dict(baseline.diff_dict)

    new_tables = sorted(current_tables - baseline_tables)
    resolved_tables = sorted(baseline_tables - current_tables)
    persisting_tables = sorted(current_tables & baseline_tables)

    return BaselineComparison(
        baseline_name=baseline.name,
        new_tables=new_tables,
        resolved_tables=resolved_tables,
        persisting_tables=persisting_tables,
    )


def format_comparison_text(cmp: BaselineComparison, colour: bool = True) -> str:
    """Render a BaselineComparison as a human-readable string."""
    lines: list[str] = []
    _c = (lambda s, code: f"\033[{code}m{s}\033[0m") if colour else (lambda s, _: s)

    lines.append(f"Baseline comparison: {_c(cmp.baseline_name, '1')}")
    lines.append("")

    if cmp.new_tables:
        lines.append(_c(f"  ⚠ New changes ({len(cmp.new_tables)} table(s)):", "33"))
        for t in cmp.new_tables:
            lines.append(f"    + {t}")
    else:
        lines.append(_c("  ✓ No new regressions vs baseline.", "32"))

    if cmp.resolved_tables:
        lines.append(_c(f"  ✓ Resolved ({len(cmp.resolved_tables)} table(s)):", "32"))
        for t in cmp.resolved_tables:
            lines.append(f"    - {t}")

    if cmp.persisting_tables:
        lines.append(f"  ~ Persisting ({len(cmp.persisting_tables)} table(s)):")
        for t in cmp.persisting_tables:
            lines.append(f"    ~ {t}")

    return "\n".join(lines)
