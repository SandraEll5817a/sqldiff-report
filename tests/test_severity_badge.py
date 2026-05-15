"""Additional tests focused on ANSI colour output of severity badges."""

from sqldiff_report.severity import Severity
from sqldiff_report.severity_badge import severity_badge, badge_for_table

_RESET = "\033[0m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"


def test_high_badge_colour():
    badge = severity_badge(Severity.HIGH, colour=True)
    assert badge.startswith(_RED)
    assert badge.endswith(_RESET)
    assert "[HIGH]" in badge


def test_medium_badge_colour():
    badge = severity_badge(Severity.MEDIUM, colour=True)
    assert badge.startswith(_YELLOW)
    assert "[MEDIUM]" in badge


def test_low_badge_colour():
    badge = severity_badge(Severity.LOW, colour=True)
    assert badge.startswith(_CYAN)
    assert "[LOW]" in badge


def test_no_colour_has_no_ansi():
    for sev in Severity:
        badge = severity_badge(sev, colour=False)
        assert "\033[" not in badge


def test_badge_for_table_colour_contains_ansi():
    line = badge_for_table("payments", Severity.HIGH, colour=True)
    assert "\033[" in line
    assert "payments" in line


def test_badge_for_table_no_colour_clean():
    line = badge_for_table("payments", Severity.HIGH, colour=False)
    assert "\033[" not in line
    assert "[HIGH]" in line
    assert "payments" in line
