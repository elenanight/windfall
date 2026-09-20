"""Method-budget analyzer used by the test suite.

Rule of ten: every class in ``windfall/`` and ``windfall_cli/`` may define at
most ``MAX_METHODS`` methods, excluding ``__init__``. Crossing the limit is an
ERROR (test failure); reaching 9-10 methods emits a UserWarning so the class
and its methods are called out before the limit is hit.
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
