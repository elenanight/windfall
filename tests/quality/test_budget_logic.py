"""Unit tests for the method- and function-budget analyzers."""

from __future__ import annotations

from pathlib import Path

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


def _long_function(name: str, lines: int) -> str:
    """A module-level function of exactly ``lines`` lines."""
    body = "".join(f"    x{i} = {i}\n" for i in range(lines - 2))
    return f"def {name}():\n{body}    return 0\n"


class TestLengthBudgetLogic:
    def test_short_function_passes(self, tmp_path: Path) -> None:
        path = tmp_path / "small.py"
        path.write_text(_long_function("tiny", 10), encoding="utf-8")
        budget.run_length_checks([("small.py", path)], allowlist={})

    def test_over_long_function_fails_when_not_ratcheted(self, tmp_path: Path) -> None:
        path = tmp_path / "big.py"
        path.write_text(_long_function("huge", budget.MAX_FUNCTION_LINES + 1), encoding="utf-8")
        with pytest.raises(AssertionError, match="LENGTH-ERROR"):
            budget.run_length_checks([("big.py", path)], allowlist={})

    def test_ratcheted_function_may_shrink(self, tmp_path: Path) -> None:
        path = tmp_path / "ratchet.py"
        path.write_text(_long_function("was_long", 40), encoding="utf-8")
        budget.run_length_checks(
            [("ratchet.py", path)], allowlist={"ratchet.py": {"was_long": 200}}
        )

    def test_ratcheted_function_may_not_grow(self, tmp_path: Path) -> None:
        path = tmp_path / "ratchet.py"
        path.write_text(_long_function("grew", 80), encoding="utf-8")
        with pytest.raises(AssertionError, match="grew to 80 lines"):
            budget.run_length_checks(
                [("ratchet.py", path)], allowlist={"ratchet.py": {"grew": 60}}
            )

    def test_nested_functions_are_counted_too(self, tmp_path: Path) -> None:
        path = tmp_path / "nested.py"
        inner = "\n".join(f"        y{i} = {i}" for i in range(budget.MAX_FUNCTION_LINES + 5))
        path.write_text(f"def outer():\n    def also_long():\n{inner}\n        return 1\n", encoding="utf-8")
        with pytest.raises(AssertionError, match="also_long"):
            budget.run_length_checks([("nested.py", path)], allowlist={})

    def test_shipped_allowlist_matches_the_real_offenders(self) -> None:
        """The ratchet keys must be the paths the package scan actually uses."""
        offenders = {
            rel: name
            for rel, names in budget.OVER_LENGTH_ALLOWLIST.items()
            for name in names
        }
        assert offenders, "ratchet is empty; it should pin the two known offenders"
        for rel in offenders:
            assert (Path(__file__).resolve().parent.parent.parent / rel).is_file(), rel