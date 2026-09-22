"""Unit tests for the method-budget analyzer and its diagnostics."""

from __future__ import annotations

import pytest

from tests.quality import budget


class TestBudgetLogic:
    def test_method_names_exclude_init(self) -> None:
        source = "class Foo:\n    def __init__(self): pass\n    def a(self): pass\n"
        report = budget.reports_from_source(source)[0]
        assert report.methods == ["a"]

    def test_error_when_over_limit(self) -> None:
        source = "class Foo:\n" + "".join(f"    def m{i}(self): pass\n" for i in range(1, 12))
        report = budget.reports_from_source(source)[0]
        assert report.count == 11
        message = report.error_message()
        assert message.startswith("[BUDGET-ERROR]")
        assert "Foo" in message
        assert "m11 (11th)" in message
        assert "max 10" in message

    def test_warning_when_at_limit(self) -> None:
        source = "class Foo:\n" + "".join(f"    def m{i}(self): pass\n" for i in range(1, 11))
        report = budget.reports_from_source(source)[0]
        assert report.count == 10
        message = report.warning_message()
        assert message.startswith("[BUDGET-WARNING]")
        assert "Foo" in message
        assert "at the limit (10/10 methods)" in message

    def test_warning_when_close_to_limit(self) -> None:
        source = "class Foo:\n" + "".join(f"    def m{i}(self): pass\n" for i in range(1, 10))
        report = budget.reports_from_source(source)[0]
        assert report.count == 9
        message = report.warning_message()
        assert message.startswith("[BUDGET-WARNING]")
        assert "Foo" in message
        assert "close to the limit (9/10 methods)" in message

    def test_run_checks_fails_on_violation(self) -> None:
        source = "class Foo:\n" + "".join(f"    def m{i}(self): pass\n" for i in range(1, 12))
        report = budget.reports_from_source(source)[0]
        with pytest.raises(AssertionError, match="BUDGET-ERROR"):
            budget.run_checks([report], emit_warnings=False)

    def test_run_checks_warns_without_failing(self) -> None:
        source = "class Foo:\n" + "".join(f"    def m{i}(self): pass\n" for i in range(1, 10))
        report = budget.reports_from_source(source)[0]
        with pytest.warns(UserWarning, match="BUDGET-WARNING"):
            budget.run_checks([report])

    def test_clean_class_passes_silently(self) -> None:
        report = budget.reports_from_source("class Foo:\n    def a(self): pass\n")[0]
        budget.run_checks([report], emit_warnings=True)
        budget.run_checks([report], emit_warnings=False)