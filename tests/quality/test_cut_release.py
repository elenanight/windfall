"""Tests for the windfall release-cut helper script."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import cut_release as cr


def _write_tree(tmp_path: Path, version: str = "0.2.6") -> None:
    tmp_path.joinpath("pyproject.toml").write_text(
        f'[project]\nname = "windfall"\nversion = "{version}"\n', encoding="utf-8"
    )
    tmp_path.joinpath("README.md").write_text(
        "# Windfall\n\n"
        f"[![version](https://img.shields.io/badge/version-{version}-blue)]()\n",
        encoding="utf-8",
    )
    tmp_path.joinpath("CHANGELOG.md").write_text(
        "# Changelog\n\n"
        f"## [{version}] - 2026-09-22\n\n### Added\n\n- A windfall feature.\n",
        encoding="utf-8",
    )
    tmp_path.joinpath("SECURITY.md").write_text(
        "# Security\n\n## Supported Versions\n\n"
        f"{cr.SUPPORT_START}\n"
        "Initial\n"
        "| Version  | Supported          |\n"
        "| -------- | ------------------ |\n"
        f"{cr.SUPPORT_END}\n"
        "\nTail text.\n",
        encoding="utf-8",
    )
    tmp_path.joinpath("windfall").mkdir(exist_ok=True)
    tmp_path.joinpath("windfall", "__init__.py").write_text(
        f'__version__ = "{version}"\n', encoding="utf-8"
    )


class TestPrior:
    def test_prior_slides_patch_with_minor_borrow(self) -> None:
        assert cr.prior("0.2.7", 1) == "0.2.6"
        assert cr.prior("0.2.7", 2) == "0.2.5"
        assert cr.prior("0.2.7", 3) == "0.2.4"
        assert cr.prior("0.3.0", 1) == "0.2.9"
        assert cr.prior("0.1.2", 3) == "0.0.9"


class TestSupportWindow:
    def test_support_rows_three_slot_window(self) -> None:
        assert cr.support_rows("0.2.7") == [
            ("0.2.7", "✅"),
            ("0.2.6", "✅"),
            ("0.2.5", "✅"),
            ("<= 0.2.4", "❌"),
        ]

    def test_slid_eol_is_window_tail(self) -> None:
        assert cr.slid_eol("0.2.7") == "<= 0.2.4"

    def test_build_support_block_contains_window_and_eol(self) -> None:
        block = cr.build_support_block("0.2.7")
        assert "| 0.2.7" in block
        assert "| 0.2.6" in block
        assert "<= 0.2.4" in block


class TestSecurityBlock:
    def test_slide_support_block_rewrites_marked_window(self, tmp_path) -> None:
        _write_tree(tmp_path)
        text = tmp_path.joinpath("SECURITY.md").read_text(encoding="utf-8")
        slid = cr.slide_support_block(text, "0.2.7")
        assert "| 0.2.7" in slid
        assert "| 0.2.6" in slid
        assert "<= 0.2.4" in slid

    def test_slide_support_block_requires_markers(self, tmp_path) -> None:
        _write_tree(tmp_path)
        text = tmp_path.joinpath("SECURITY.md").read_text(encoding="utf-8")
        with pytest.raises(ValueError):
            cr.slide_support_block(text.replace(cr.SUPPORT_START, ""), "0.2.7")


class TestVerify:
    def test_verify_clean_after_dry_run_tree(self, tmp_path) -> None:
        _write_tree(tmp_path)
        cr.PYPROJECT = tmp_path / "pyproject.toml"
        cr.INIT = tmp_path / "windfall" / "__init__.py"
        cr.README = tmp_path / "README.md"
        cr.CHANGELOG = tmp_path / "CHANGELOG.md"
        ok, problems = cr.verify("0.2.6")
        assert ok, problems

    def test_verify_detects_init_mismatch(self, tmp_path) -> None:
        _write_tree(tmp_path)
        cr.PYPROJECT = tmp_path / "pyproject.toml"
        cr.INIT = tmp_path / "windfall" / "__init__.py"
        cr.README = tmp_path / "README.md"
        cr.CHANGELOG = tmp_path / "CHANGELOG.md"
        cr.INIT.write_text('__version__ = "0.2.5"\n', encoding="utf-8")
        ok, problems = cr.verify("0.2.6")
        assert not ok
        assert any("__init__.py" in problem for problem in problems)


class TestGate:
    def test_gate_passes_when_nothing_pending(self, tmp_path, monkeypatch) -> None:
        _write_tree(tmp_path)
        _point(tmp_path)
        monkeypatch.setattr(cr, "last_released_tag", lambda: "0.2.6")
        assert cr.main(["--check"]) == 0

    def test_gate_fails_when_pending_but_not_cuttable(self, tmp_path, monkeypatch) -> None:
        _write_tree(tmp_path, version="0.2.7")
        _point(tmp_path)
        tmp_path.joinpath("CHANGELOG.md").write_text(
            "# Changelog\n\n## [0.2.6] - 2026-09-01\n\nOld.\n", encoding="utf-8"
        )
        monkeypatch.setattr(cr, "last_released_tag", lambda: "0.2.6")
        assert cr.main(["--check"]) == 1


def _point(tmp_path: Path) -> None:
    cr.PYPROJECT = tmp_path / "pyproject.toml"
    cr.INIT = tmp_path / "windfall" / "__init__.py"
    cr.README = tmp_path / "README.md"
    cr.CHANGELOG = tmp_path / "CHANGELOG.md"
