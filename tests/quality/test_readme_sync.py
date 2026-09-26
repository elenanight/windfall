"""Tests for the README version-badge sync script."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.update_readme import (
    BADGES_END,
    BADGES_START,
    DEFAULT_SLUG,
    ROADMAP_END,
    ROADMAP_START,
    build_badges,
    project_version,
    repo_slug,
    sync_init_version,
    update_readme,
    update_roadmap,
)
from scripts.update_readme import (
    main as sync_main,
)


def _sample_readme() -> str:
    return (
        "# Windfall\n\n"
        f"{BADGES_START}\n"
        "[![version](https://img.shields.io/badge/version-0.1.0-blue)]()\n"
        f"{BADGES_END}\n"
        "\nBody text.\n"
        "\n## Roadmap\n\n"
        f"{ROADMAP_START}\n"
        "Old roadmap body.\n"
        f"{ROADMAP_END}\n"
    )


def _sample_roadmap() -> str:
    return "# Roadmap\n\nNew roadmap body.\n"


def _write_tree(tmp_path, version: str = "0.1.0") -> None:
    tmp_path.joinpath("pyproject.toml").write_text(
        f'[project]\nname = "windfall"\nversion = "{version}"\n', encoding="utf-8"
    )
    tmp_path.joinpath("README.md").write_text(_sample_readme(), encoding="utf-8")
    tmp_path.joinpath("init.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    tmp_path.joinpath("roadmap.md").write_text(_sample_roadmap(), encoding="utf-8")


class TestReadmeBadges:
    def test_build_badges_embeds_version_and_slug(self) -> None:
        block = build_badges("elenanight/windfall", "0.2.0")
        assert "version-0.2.0" in block
        assert "github/last-commit/elenanight/windfall" in block
        assert block.startswith(BADGES_START)
        assert block.endswith(BADGES_END)

    def test_repo_slug_accepts_github_remotes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import subprocess

        for url, expected in [
            ("https://github.com/elenanight/windfall.git", "elenanight/windfall"),
            ("https://github.com/elenanight/windfall", "elenanight/windfall"),
            ("git@github.com:elenanight/windfall.git", "elenanight/windfall"),
        ]:
            monkeypatch.setattr(
                subprocess,
                "run",
                lambda *a, _url=url, **k: SimpleNamespace(stdout=_url),
            )
            assert repo_slug() == expected

    def test_repo_slug_rejects_non_github_remotes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import subprocess

        cases = [
            "https://github.com.evil.com/elenanight/windfall.git",
            "https://gitlab.com/elenanight/windfall.git",
            "https://github.com/onlyowner",
            "not a url at all",
        ]
        for url in cases:
            monkeypatch.setattr(
                subprocess, "run", lambda *a, _url=url, **k: SimpleNamespace(stdout=_url)
            )
            assert repo_slug() == DEFAULT_SLUG


class TestSyncUpdate:
    def test_replaces_version_badge(self, tmp_path) -> None:
        _write_tree(tmp_path)
        readme = tmp_path / "README.md"
        changed = update_readme("0.2.0", "elenanight/windfall", readme)
        assert changed is True
        text = readme.read_text(encoding="utf-8")
        assert "version-0.2.0" in text
        assert "version-0.1.0" not in text
        assert "Body text." in text

    def test_is_idempotent(self, tmp_path) -> None:
        _write_tree(tmp_path)
        readme = tmp_path / "README.md"
        update_readme("0.1.0", "elenanight/windfall", readme)
        assert update_readme("0.1.0", "elenanight/windfall", readme) is False

    def test_requires_markers(self, tmp_path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("# Windfall\n", encoding="utf-8")
        with pytest.raises(ValueError):
            update_readme("0.1.0", "elenanight/windfall", readme)


class TestSyncRoadmap:
    def test_embeds_wiki_roadmap_body(self, tmp_path) -> None:
        _write_tree(tmp_path)
        readme = tmp_path / "README.md"
        roadmap = tmp_path / "roadmap.md"
        assert update_roadmap(readme, roadmap) is True
        text = readme.read_text(encoding="utf-8")
        assert "New roadmap body." in text
        assert "Old roadmap body." not in text
        assert "Body text." in text

    def test_is_idempotent(self, tmp_path) -> None:
        _write_tree(tmp_path)
        readme = tmp_path / "README.md"
        roadmap = tmp_path / "roadmap.md"
        update_roadmap(readme, roadmap)
        assert update_roadmap(readme, roadmap) is False

    def test_requires_markers(self, tmp_path) -> None:
        readme = tmp_path / "README.md"
        roadmap = tmp_path / "roadmap.md"
        readme.write_text("# Windfall\n", encoding="utf-8")
        roadmap.write_text("# Roadmap\n\nBody.\n", encoding="utf-8")
        with pytest.raises(ValueError):
            update_roadmap(readme, roadmap)


class TestSyncVersion:
    def test_sync_init_updates_version(self, tmp_path) -> None:
        _write_tree(tmp_path)
        init = tmp_path / "init.py"
        assert sync_init_version("0.3.0", init) is True
        assert sync_init_version("0.3.0", init) is False
        assert '__version__ = "0.3.0"' in init.read_text(encoding="utf-8")

    def test_project_version_reads_source_of_truth(self, tmp_path) -> None:
        _write_tree(tmp_path, version="0.4.0")
        assert project_version(tmp_path / "pyproject.toml") == "0.4.0"

    def test_check_flag_reports_staleness(self, tmp_path, monkeypatch) -> None:
        _write_tree(tmp_path, version="0.5.0")
        monkeypatch.setattr("scripts.update_readme.PYPROJECT", tmp_path / "pyproject.toml")
        monkeypatch.setattr("scripts.update_readme.README", tmp_path / "README.md")
        monkeypatch.setattr("scripts.update_readme.INIT", tmp_path / "init.py")
        monkeypatch.setattr("scripts.update_readme.ROADMAP", tmp_path / "roadmap.md")
        assert sync_main(["--check"]) == 1
        assert sync_main(["--check"]) == 0