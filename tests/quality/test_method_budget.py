"""Whole-package audit: classes and functions must honor the rule of ten."""

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


def _relative_files() -> list[tuple[str, Path]]:
    return [
        (str(path.relative_to(ROOT)), path)
        for path in _package_files()
    ]


class TestPackageBudget:
    def test_every_class_stays_within_budget(self) -> None:
        files = _package_files()
        assert files, "no package files found to audit"
        budget.run_checks(budget.analysis(files))

    def test_no_function_exceeds_the_length_budget(self) -> None:
        files = _relative_files()
        assert files, "no package files found to audit"
        budget.run_length_checks(files)