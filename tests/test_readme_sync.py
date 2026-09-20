"""Tests for the README version-badge sync script."""

from __future__ import annotations

import pytest

from scripts.update_readme import (
    BADGES_END,
    BADGES_START,
    build_badges,
    project_version,
    sync_init_version,
    update_readme,
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
    )


def _write_tree(tmp_path, version: str = "0.1.0") -> None:
    tmp_path.joinpath("pyproject.toml").write_text(
        f'[project]\nname = "windfall"\nversion = "{version}"\n', encoding="utf-8"
    )
    tmp_path.joinpath("README.md").write_text(_sample_readme(), encoding="utf-8")
    tmp_path.joinpath("init.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")


def test_build_badges_embeds_version_and_slug() -> None:
    block = build_badges("elenanight/windfall", "0.2.0")
    assert "version-0.2.0" in block
    assert "github/last-commit/elenanight/windfall" in block
    assert block.startswith(BADGES_START)
    assert block.endswith(BADGES_END)


def test_update_readme_replaces_version_badge(tmp_path) -> None:
    _write_tree(tmp_path)
    readme = tmp_path / "README.md"
    changed = update_readme("0.2.0", "elenanight/windfall", readme)
    assert changed is True
    text = readme.read_text(encoding="utf-8")
    assert "version-0.2.0" in text
    assert "version-0.1.0" not in text
    assert "Body text." in text


def test_update_readme_is_idempotent(tmp_path) -> None:
    _write_tree(tmp_path)
    readme = tmp_path / "README.md"
    update_readme("0.1.0", "elenanight/windfall", readme)
    assert update_readme("0.1.0", "elenanight/windfall", readme) is False


def test_update_readme_requires_markers(tmp_path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Windfall\n", encoding="utf-8")
    with pytest.raises(ValueError):
        update_readme("0.1.0", "elenanight/windfall", readme)


def test_sync_init_updates_version(tmp_path) -> None:
    _write_tree(tmp_path)
    init = tmp_path / "init.py"
    assert sync_init_version("0.3.0", init) is True
    assert sync_init_version("0.3.0", init) is False
    assert '__version__ = "0.3.0"' in init.read_text(encoding="utf-8")


def test_project_version_reads_source_of_truth(tmp_path) -> None:
    _write_tree(tmp_path, version="0.4.0")
    assert project_version(tmp_path / "pyproject.toml") == "0.4.0"


def test_check_flag_reports_staleness(tmp_path, monkeypatch) -> None:
    _write_tree(tmp_path, version="0.5.0")
    monkeypatch.setattr("scripts.update_readme.PYPROJECT", tmp_path / "pyproject.toml")
    monkeypatch.setattr("scripts.update_readme.README", tmp_path / "README.md")
    monkeypatch.setattr("scripts.update_readme.INIT", tmp_path / "init.py")
    assert sync_main(["--check"]) == 1
    assert sync_main(["--check"]) == 0