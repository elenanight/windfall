"""Whole-package audit: every class must honor the rule of ten."""

from __future__ import annotations

from pathlib import Path

from tests.quality import budget

ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGES = ("windfall", "windfall_cli")


def _package_files() -> list[Path]:
    files: list[Path] = []
    for pkg in PACKAGES:
        pkg_dir = ROOT / pkg
        if pkg_dir.is_dir():
            files.extend(sorted(pkg_dir.rglob("*.py")))
    return files


class TestPackageBudget:
    def test_every_class_stays_within_budget(self) -> None:
        files = _package_files()
        assert files, "no package files found to audit"
        budget.run_checks(budget.analysis(files))