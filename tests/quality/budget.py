"""Method- and function-budget analyzers used by the test suite.

Rule of ten, methods: every class in ``windfall/`` and ``windfall_cli/`` may
define at most ``MAX_METHODS`` methods, excluding ``__init__``. Crossing the
limit is an ERROR (test failure); reaching 9-10 methods emits a UserWarning so
the class and its methods are called out before the limit is hit.

Rule of ten, functions: no single function may run past
``MAX_FUNCTION_LINES`` lines. Two functions already exceed it, so they are
ratcheted in ``OVER_LENGTH_ALLOWLIST`` at their current length: they may shrink
but growing past the recorded number is an error until the function is
refactored and dropped from the map. This keeps the gate honest about the two
worst offenders instead of silently passing them, which is what a methods-only
check did.
"""

from __future__ import annotations

import ast
import warnings
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

MAX_METHODS = 10
WARN_FROM = 9  # a class with >= this many methods already warns
WARN_AT_LIMIT = MAX_METHODS

MAX_FUNCTION_LINES = 60

# {relative path: {function name: lines allowed}} — the ratchet.
OVER_LENGTH_ALLOWLIST = {
    "windfall_cli/menu.py": {"build_menu": 164},
    "windfall_cli/templates/app/app.py": {"build": 276},
}


@dataclass
class BudgetReport:
    """Audit result for a single class: its name, home file, and methods."""

    class_name: str
    module_path: Path
    methods: list[str]

    @property
    def count(self) -> int:
        return len(self.methods)

    def error_message(self) -> str:
        offending = self.methods[self.count - 1]
        body = ", ".join(self.methods)
        return (
            f"[BUDGET-ERROR] {self.module_path.name}::{self.class_name} has "
            f"{self.count} methods (max {MAX_METHODS} excl. __init__):\n"
            f"    {body}\n"
            f"    -> offending: {offending} ({self.count}th). "
            f"Split this class or extract logic into a helper or primitive."
        )

    def warning_message(self) -> str:
        why = "at the limit" if self.count == WARN_AT_LIMIT else "close to the limit"
        body = ", ".join(self.methods)
        return (
            f"[BUDGET-WARNING] {self.module_path.name}::{self.class_name} is "
            f"{why} ({self.count}/{MAX_METHODS} methods):\n"
            f"    {body}\n"
            f"    -> the next addition will exceed the budget. Consider extracting."
        )


def _method_names(node: ast.ClassDef) -> list[str]:
    return [
        child.name
        for child in node.body
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        and child.name != "__init__"
    ]


def reports_from_source(source: str, module_name: str = "x.py") -> list[BudgetReport]:
    """Audit an in-memory Python source string (used by unit tests)."""
    tree = ast.parse(source)
    return [
        BudgetReport(node.name, Path(module_name), _method_names(node))
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    ]


def analysis(files: Iterable[Path]) -> list[BudgetReport]:
    """Audit every Python file on disk, reporting one entry per class."""
    return [
        report
        for path in files
        for report in reports_from_source(path.read_text(encoding="utf-8"), path.name)
    ]


def run_checks(reports: list[BudgetReport], *, emit_warnings: bool = True) -> None:
    """Raise on budget violations and emit warnings for near-limit classes."""
    errors: list[str] = []
    for report in reports:
        if report.count > MAX_METHODS:
            errors.append(report.error_message())
        elif emit_warnings and report.count >= WARN_FROM:
            warnings.warn(report.warning_message(), UserWarning, stacklevel=2)
    assert not errors, "Method budget exceeded:\n\n" + "\n\n".join(errors)


@dataclass
class LengthReport:
    """Audit result for one function: where it lives and how long it is."""

    module_path: Path
    func_name: str
    lines: int

    def error_message(self) -> str:
        return (
            f"[LENGTH-ERROR] {self.module_path}::{self.func_name} is {self.lines} "
            f"lines (max {MAX_FUNCTION_LINES}).\n"
            f"    -> split it into helpers, or shrink it below the limit."
        )

    def growth_message(self, allowed: int) -> str:
        return (
            f"[LENGTH-ERROR] {self.module_path}::{self.func_name} grew to "
            f"{self.lines} lines, past its ratcheted {allowed}.\n"
            f"    -> a ratcheted function may shrink but not grow. Refactor it, "
            f"or update OVER_LENGTH_ALLOWLIST if the growth is justified."
        )


def length_reports_from_source(
    source: str, module_path: str = "x.py"
) -> list[LengthReport]:
    """Audit an in-memory source string, one report per function."""
    tree = ast.parse(source)
    return [
        LengthReport(Path(module_path), node.name, (node.end_lineno or node.lineno) - node.lineno + 1)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def run_length_checks(
    files: Iterable[tuple[str, Path]],
    *,
    allowlist: dict[str, dict[str, int]] | None = None,
) -> None:
    """Raise on over-long functions, honoring the ratchet in ``allowlist``.

    ``files`` is ``(relative path, path)`` pairs so ratchet keys stay stable
    regardless of where the suite runs from.
    """
    ratchet = OVER_LENGTH_ALLOWLIST if allowlist is None else allowlist
    errors: list[str] = []
    for rel_path, path in files:
        for report in length_reports_from_source(
            path.read_text(encoding="utf-8"), rel_path
        ):
            allowed = ratchet.get(rel_path, {}).get(report.func_name)
            if allowed is None:
                if report.lines > MAX_FUNCTION_LINES:
                    errors.append(report.error_message())
            elif report.lines > allowed:
                errors.append(report.growth_message(allowed))
    assert not errors, "Function length budget exceeded:\n\n" + "\n\n".join(errors)
