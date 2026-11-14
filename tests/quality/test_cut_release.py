"""Tests for the windfall release-cut helper script."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from scripts import cut_release as cr

#: Real-history fixture: every 0.2 patch from 0.2.0 through 0.2.6.
HISTORY_TO_0_2_6 = [f"0.2.{patch}" for patch in range(7)]


def _write_tree(tmp_path: Path, version: str = "0.2.6") -> None:
    tmp_path.joinpath("VERSION").write_text(f"{version}\n", encoding="utf-8")
    tmp_path.joinpath("README.md").write_text(
        f"# Windfall\n\n[![version](https://img.shields.io/badge/version-{version}-blue)]()\n",
        encoding="utf-8",
    )
    tmp_path.joinpath("CHANGELOG.md").write_text(
        f"# Changelog\n\n## [{version}] - 2026-09-22\n\n### Added\n\n- A windfall feature.\n",
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


def _point(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the script at a temp tree, restoring the real paths afterwards."""
    for name, path in {
        "VERSION": tmp_path / "VERSION",
        "INIT": tmp_path / "windfall" / "__init__.py",
        "README": tmp_path / "README.md",
        "CHANGELOG": tmp_path / "CHANGELOG.md",
    }.items():
        monkeypatch.setattr(cr, name, path)


class TestWindowHistory:
    """The window derives from real release history, never a ladder (VWS-150)."""

    def test_minor_bump_window_includes_two_digit_patches(self) -> None:
        history = [f"0.2.{patch}" for patch in range(11)]  # 0.2.0 .. 0.2.10
        assert cr.window_versions("0.3.0", history) == ["0.3.0", "0.2.10", "0.2.9"]
        assert cr.eol_version("0.3.0", history) == "0.2.8"

    def test_long_patch_line_window_uses_newest_releases(self) -> None:
        history = [f"0.3.{patch}" for patch in range(26)]  # 0.3.0 .. 0.3.25
        assert cr.window_versions("0.4.0", history) == ["0.4.0", "0.3.25", "0.3.24"]
        assert cr.eol_version("0.4.0", history) == "0.3.23"

    def test_mid_line_window(self) -> None:
        assert cr.window_versions("0.2.7", HISTORY_TO_0_2_6) == ["0.2.7", "0.2.6", "0.2.5"]
        assert cr.eol_version("0.2.7", HISTORY_TO_0_2_6) == "0.2.4"

    def test_no_eol_until_history_outgrows_the_window(self) -> None:
        assert cr.window_versions("0.1.1", ["0.1.0"]) == ["0.1.1", "0.1.0"]
        assert cr.eol_version("0.1.1", ["0.1.0"]) is None


class TestSupportWindow:
    def test_support_rows_three_slot_window(self) -> None:
        assert cr.support_rows("0.2.7", HISTORY_TO_0_2_6) == [
            ("0.2.7", "✅"),
            ("0.2.6", "✅"),
            ("0.2.5", "✅"),
            ("<= 0.2.4", "❌"),
        ]

    def test_support_rows_minor_bump_window(self) -> None:
        history = [f"0.2.{patch}" for patch in range(11)]  # 0.2.0 .. 0.2.10
        assert cr.support_rows("0.3.0", history) == [
            ("0.3.0", "✅"),
            ("0.2.10", "✅"),
            ("0.2.9", "✅"),
            ("<= 0.2.8", "❌"),
        ]

    def test_support_rows_omit_eol_row_when_nothing_is_eol(self) -> None:
        assert cr.support_rows("0.1.1", ["0.1.0"]) == [("0.1.1", "✅"), ("0.1.0", "✅")]

    def test_slid_eol_is_window_tail(self) -> None:
        assert cr.slid_eol("0.2.7", HISTORY_TO_0_2_6) == "<= 0.2.4"
        assert cr.slid_eol("0.1.1", ["0.1.0"]) is None

    def test_build_support_block_contains_window_and_eol(self) -> None:
        block = cr.build_support_block("0.2.7", HISTORY_TO_0_2_6)
        assert "| 0.2.7" in block
        assert "| 0.2.6" in block
        assert "<= 0.2.4" in block


class TestSecurityBlock:
    def test_slide_support_block_rewrites_marked_window(self, tmp_path) -> None:
        _write_tree(tmp_path)
        text = tmp_path.joinpath("SECURITY.md").read_text(encoding="utf-8")
        slid = cr.slide_support_block(text, "0.2.7", HISTORY_TO_0_2_6)
        assert "| 0.2.7" in slid
        assert "| 0.2.6" in slid
        assert "<= 0.2.4" in slid

    def test_slide_support_block_requires_markers(self, tmp_path) -> None:
        _write_tree(tmp_path)
        text = tmp_path.joinpath("SECURITY.md").read_text(encoding="utf-8")
        with pytest.raises(ValueError):
            cr.slide_support_block(text.replace(cr.SUPPORT_START, ""), "0.2.7")


class TestVerify:
    def test_verify_clean_after_dry_run_tree(self, tmp_path, monkeypatch) -> None:
        _write_tree(tmp_path)
        _point(tmp_path, monkeypatch)
        ok, problems = cr.verify("0.2.6")
        assert ok, problems

    def test_verify_detects_init_mismatch(self, tmp_path, monkeypatch) -> None:
        _write_tree(tmp_path)
        _point(tmp_path, monkeypatch)
        tmp_path.joinpath("windfall", "__init__.py").write_text(
            '__version__ = "0.2.5"\n', encoding="utf-8"
        )
        ok, problems = cr.verify("0.2.6")
        assert not ok
        assert any("__init__.py" in problem for problem in problems)

    def test_verify_never_writes_the_changelog(self, tmp_path, monkeypatch) -> None:
        """--check is a read-only gate: a cuttable pending cut must not write."""
        _write_tree(tmp_path, version="0.2.7")
        _point(tmp_path, monkeypatch)
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- A windfall feature.\n",
            encoding="utf-8",
        )
        before = changelog.read_bytes()
        ok, problems = cr.verify("0.2.7")
        # The Unreleased body would promote cleanly, so this is cuttable…
        assert ok, problems
        # …but verifying it must leave the file byte-identical.
        assert changelog.read_bytes() == before

    def test_verify_reports_unpromotable_changelog(self, tmp_path, monkeypatch) -> None:
        _write_tree(tmp_path, version="0.2.7")
        _point(tmp_path, monkeypatch)
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("# Changelog\n\n## [0.2.6] - 2026-09-01\n\nOld.\n", encoding="utf-8")
        ok, problems = cr.verify("0.2.7")
        assert not ok
        assert any("CHANGELOG" in problem for problem in problems)


class TestChangelogPromotion:
    def test_promotion_uses_todays_date_not_a_stale_literal(self, tmp_path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- A windfall feature.\n",
            encoding="utf-8",
        )
        promoted = cr._promoted_changelog("0.2.7", changelog)
        assert promoted is not None
        # time.strftime keeps this independent of the implementation under test.
        assert f"## [0.2.7] - {time.strftime('%Y-%m-%d')}" in promoted
        assert "2026-09-22" not in promoted
        assert "## [Unreleased]" not in promoted

    def test_promotion_returns_none_with_nothing_to_promote(self, tmp_path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("# Changelog\n\n## [0.2.6] - 2026-09-01\n\nOld.\n", encoding="utf-8")
        assert cr._promoted_changelog("0.2.7", changelog) is None

    def test_promotion_leaves_the_file_untouched(self, tmp_path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- A windfall feature.\n",
            encoding="utf-8",
        )
        before = changelog.read_bytes()
        cr._promoted_changelog("0.2.7", changelog)
        assert changelog.read_bytes() == before

    def test_promotion_moves_the_body_without_duplicating_it(self, tmp_path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- A windfall feature.\n\n"
            "### Fixed\n\n- A windfall fix.\n\n## [0.2.6] - 2026-09-01\n\nOld.\n",
            encoding="utf-8",
        )
        promoted = cr._promoted_changelog("0.2.7", changelog)
        assert promoted is not None
        # A move, not a copy: every line of the body appears exactly once,
        # under its own subsection headings, ahead of the older sections.
        assert promoted.count("- A windfall feature.") == 1
        assert promoted.count("- A windfall fix.") == 1
        assert "### Fixed" in promoted
        assert promoted.index("## [0.2.7]") < promoted.index("## [0.2.6]")

    def test_promotion_returns_none_for_an_empty_unreleased_body(self, tmp_path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [Unreleased]\n\n## [0.2.6] - 2026-09-01\n\nOld.\n",
            encoding="utf-8",
        )
        assert cr._promoted_changelog("0.2.7", changelog) is None


class TestGate:
    def test_gate_passes_when_nothing_pending(self, tmp_path, monkeypatch) -> None:
        _write_tree(tmp_path)
        _point(tmp_path, monkeypatch)
        monkeypatch.setattr(cr, "last_released_tag", lambda: "0.2.6")
        assert cr.main(["--check"]) == 0

    def test_gate_fails_when_pending_but_not_cuttable(self, tmp_path, monkeypatch) -> None:
        _write_tree(tmp_path, version="0.2.7")
        _point(tmp_path, monkeypatch)
        tmp_path.joinpath("CHANGELOG.md").write_text(
            "# Changelog\n\n## [0.2.6] - 2026-09-01\n\nOld.\n", encoding="utf-8"
        )
        monkeypatch.setattr(cr, "last_released_tag", lambda: "0.2.6")
        assert cr.main(["--check"]) == 1


class TestApplyCut:
    """``--apply`` must reach the release body for a pending, unpromoted cut.

    ``verify()`` is read-only, so ``apply_cut`` owns the promotion. Without it
    the publish job of release.yml died on a missing ``## [version]`` section
    right after verify() reported the release as cuttable.
    """

    def _pending_tree(self, tmp_path: Path) -> Path:
        _write_tree(tmp_path, version="0.2.7")
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- A windfall feature.\n",
            encoding="utf-8",
        )
        return changelog

    def test_apply_cut_promotes_before_reading_the_release_body(
        self, tmp_path, monkeypatch
    ) -> None:
        changelog = self._pending_tree(tmp_path)
        _point(tmp_path, monkeypatch)
        monkeypatch.setattr(cr, "SECURITY", tmp_path / "SECURITY.md")
        # Both already exist, so apply_cut stops short of tagging or publishing
        # and no subprocess is spawned.
        monkeypatch.setattr(cr, "ensure_gh", lambda: True)
        monkeypatch.setattr(cr, "tag_exists", lambda version: True)
        monkeypatch.setattr(cr, "release_exists", lambda version: True)
        cr.apply_cut("0.2.7")
        assert f"## [0.2.7] - {time.strftime('%Y-%m-%d')}" in changelog.read_text(encoding="utf-8")

    def test_dry_run_stays_side_effect_free(self, tmp_path, monkeypatch) -> None:
        changelog = self._pending_tree(tmp_path)
        _point(tmp_path, monkeypatch)
        monkeypatch.setattr(cr, "SECURITY", tmp_path / "SECURITY.md")
        before = changelog.read_bytes()
        cr.apply_cut("0.2.7", dry_run=True)
        assert changelog.read_bytes() == before
