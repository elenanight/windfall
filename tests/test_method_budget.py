"""Whole-package audit: every class must honor the rule of seven."""

from __future__ import annotations

from pathlib import Path

import budget

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ("windfall", "windfall_cli")


def package_files() -> list[Path]:
    files: list[Path] = []
    for pkg in PACKAGES:
        pkg_dir = ROOT / pkg
        if pkg_dir.is_dir():
            files.extend(sorted(pkg_dir.rglob("*.py")))
    return files


def test_every_class_stays_within_budget() -> None:
    files = package_files()
    assert files, "no package files found to audit"
    budget.run_checks(budget.analysis(files))