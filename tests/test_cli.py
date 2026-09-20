"""Tests for the ``windfall`` command-line interface."""

from __future__ import annotations

from pathlib import Path

import pytest

from windfall_cli import cli


def test_missing_command_prints_help(capsys) -> None:
    assert cli.main([]) == 0
    assert "windfall" in capsys.readouterr().out


def test_version_flag(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert "windfall" in capsys.readouterr().out


def test_new_scaffolds_app(tmp_path: Path) -> None:
    base = tmp_path / "work"
    assert cli.main(["new", "myapp", "--dest", str(base)]) == 0
    dest = base / "project" / "myapp"
    assert (dest / "app.py").is_file()
    assert (dest / "README.md").is_file()
    rendered = (dest / "app.py").read_text(encoding="utf-8")
    assert "myapp" in rendered
    assert "@@package@@" not in rendered
    assert "@@title@@" not in rendered
    project_toml = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert "@@uv_sources@@" not in project_toml
    assert "windfall" in project_toml
    assert "[tool.uv.sources]" in project_toml
    assert "editable = true" in project_toml


def test_new_defaults_to_current_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    assert cli.main(["new", "myapp"]) == 0
    dest = tmp_path / "project" / "myapp"
    assert (dest / "app.py").is_file()


def test_new_rejects_existing_destination(tmp_path: Path) -> None:
    dest = tmp_path / "taken" / "project" / "app"
    dest.mkdir(parents=True)
    assert cli.main(["new", "app", "--dest", str(tmp_path / "taken")]) == 2


def test_new_rejects_bad_name(tmp_path: Path) -> None:
    assert cli.main(["new", "9bad", "--dest", str(tmp_path / "bad")]) == 2


def test_new_rejects_unknown_template(tmp_path: Path) -> None:
    assert cli.main(["new", "x", "--template", "nope", "--dest", str(tmp_path / "x")]) == 2


def test_check_smoke_passes() -> None:
    assert cli.main(["check", "--ticks", "10"]) == 0


def test_demo_headless_passes() -> None:
    assert cli.main(["demo", "--headless", "--ticks", "5"]) == 0


def test_list_reports_scenes(tmp_path: Path, capsys) -> None:
    app = tmp_path / "app.py"
    app.write_text(
        "from windfall import Scene\n\n\nclass TitleScene(Scene):\n    pass\n\nclass Helper:\n    pass\n",
        encoding="utf-8",
    )
    assert cli.main(["list", str(app)]) == 0
    out = capsys.readouterr().out
    assert "TitleScene" in out
    assert "Helper" not in out


def test_list_missing_file() -> None:
    assert cli.main(["list", "no_such_file.py"]) == 2


def test_unknown_command_exits_two() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["frobnicate"])
    assert exc.value.code == 2


def test_demo_scene_is_buildable() -> None:
    from windfall_cli.demo import build_scene

    scene = build_scene()
    assert scene.name == "demo"
    assert scene.size().x > 0


def test_scenes_in_parses_ast(tmp_path: Path) -> None:
    from windfall_cli.inspect import scenes_in

    app = tmp_path / "a.py"
    app.write_text(
        "from windfall import Component, Scene\nclass A(Scene):\n    pass\nclass B(Component):\n    pass\n",
        encoding="utf-8",
    )
    assert scenes_in(app) == ["A", "B"]


def test_alias_create_scaffolds(tmp_path: Path) -> None:
    base = tmp_path / "alias"
    assert cli.main(["--create", "aliasapp", "--dest", str(base)]) == 0
    assert (base / "project" / "aliasapp" / "app.py").is_file()


def test_alias_create_bad_name(tmp_path: Path) -> None:
    assert cli.main(["--create", "9bad", "--dest", str(tmp_path / "x")]) == 2


def test_alias_run_executes_a_file(tmp_path: Path) -> None:
    app = tmp_path / "app.py"
    app.write_text("value = 42\n", encoding="utf-8")
    assert cli.main(["--run", str(app)]) == 0


def test_alias_run_missing_file() -> None:
    assert cli.main(["--run", "no_such_file.py"]) == 2


def test_alias_demo_headless() -> None:
    assert cli.main(["--demo", "--headless", "--ticks", "3"]) == 0


def test_alias_check() -> None:
    assert cli.main(["--check", "--ticks", "5"]) == 0


def test_alias_list(tmp_path: Path, capsys) -> None:
    app = tmp_path / "app.py"
    app.write_text("from windfall import Scene\nclass MyScene(Scene):\n    pass\n", encoding="utf-8")
    assert cli.main(["--list", str(app)]) == 0
    assert "MyScene" in capsys.readouterr().out


def test_example_subcommand_headless() -> None:
    assert cli.main(["example", "snake", "--headless", "--ticks", "5"]) == 0


def test_alias_example_headless() -> None:
    assert cli.main(["--example", "bouncer", "--headless", "--ticks", "3"]) == 0


def test_alias_example_unknown() -> None:
    assert cli.main(["--example", "nope"]) == 2


def test_example_subcommand_unknown_choice() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["example", "nope"])
    assert exc.value.code == 2


def test_alias_examples_lists(capsys) -> None:
    assert cli.main(["--examples"]) == 0
    out = capsys.readouterr().out
    assert "menu" in out
    assert "bouncer" in out
    assert "snake" in out


def test_help_subcommand(capsys) -> None:
    assert cli.main(["help"]) == 0
    assert "windfall" in capsys.readouterr().out