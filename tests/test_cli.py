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


def _find_all(node, kind: type) -> list:
    """Walk a component tree the way event delivery does (children/box/child)."""
    found = [node] if isinstance(node, kind) else []
    for attr in ("children", "_box", "_child"):
        value = getattr(node, attr, None)
        if value is None:
            continue
        for kid in value if isinstance(value, list) else [value]:
            found.extend(_find_all(kid, kind))
    return found


def test_scaffolded_app_edits_header_in_place(tmp_path: Path) -> None:
    import importlib.util

    from windfall import Compositor, Engine
    from windfall.events import ACTIVATE, KEY, Event
    from windfall.primitives import Connector
    from windfall.scene import focusables
    from windfall.widgets import (
        AddWidget,
        Button,
        FooterEditor,
        HeaderEditor,
        Hotkey,
        RemoveWidget,
        TextInput,
    )

    base = tmp_path / "work"
    assert cli.main(["new", "myapp", "--dest", str(base)]) == 0
    app_path = base / "project" / "myapp" / "app.py"
    spec = importlib.util.spec_from_file_location("scaffolded_myapp", app_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    engine = Engine()
    scene = module.build(engine)
    assert scene.name == "myapp"
    assert _find_all(scene.root, HeaderEditor) == []  # user opens the editor now

    buttons = [w for w in focusables(scene.root) if isinstance(w, Button)]
    assert scene.handle(Event(KEY, {"key": "e"})) is True
    assert buttons[0].focused is True  # E focuses Add widget, now actionable

    for widget in focusables(scene.root):
        widget.focus(False)
    _, _, edit_header, _, _ = buttons

    for widget in focusables(scene.root):
        widget.focus(False)
    assert scene.handle(Event(KEY, {"key": "a"})) is True
    assert buttons[0].focused is True  # A focuses Add widget

    engine.running = True
    assert scene.handle(Event(KEY, {"key": "q"})) is True
    assert engine.running is False  # Q quits outright
    engine.running = False

    _, _, edit_header, _, _ = buttons
    for widget in focusables(scene.root):
        widget.focus(False)
    edit_header.focus(True)
    assert scene.handle(Event(ACTIVATE)) is True
    editors = _find_all(scene.root, HeaderEditor)
    assert len(editors) == 1  # menu opens the editor in place
    main = scene.root.children[0]
    assert main.children[1] is editors[0]  # resting under the menu, above the header
    assert _find_all(scene.root, Hotkey) == []  # hotkey parked while editing

    fields = [w for w in focusables(editors[0]) if isinstance(w, TextInput)]
    fields[0].focus(True)
    assert scene.handle(Event(KEY, {"key": "e"})) is True
    assert fields[0].value.endswith("e")  # typing wins over the hotkey
    assert fields[0].focused is True

    save, _ = [w for w in focusables(editors[0]) if isinstance(w, Button)]
    for widget in focusables(scene.root):
        widget.focus(False)
    save.focus(True)
    assert scene.handle(Event(ACTIVATE)) is True
    config_path = base / "project" / "myapp" / ".windfallrc.json"
    assert config_path.is_file()
    assert "hello from myapp!" in config_path.read_text(encoding="utf-8")
    assert _find_all(scene.root, HeaderEditor) == []
    assert len(_find_all(scene.root, Hotkey)) == 3  # hotkeys restored after close

    again_engine = Engine()
    again = module.build(again_engine)
    assert _find_all(again.root, HeaderEditor) == []
    assert any("hello from myapp!" in line for line in Compositor().text(again))
    shafts = _find_all(again.root, Connector)
    assert len(shafts) == 4
    assert all(shaft.state == "available" and shaft.horizontal for shaft in shafts)

    quit = next(
        w
        for w in focusables(again.root)
        if isinstance(w, Button) and w.on_activate == again_engine.stop
    )
    for widget in focusables(again.root):
        widget.focus(False)
    again_engine.running = True
    quit.focus(True)
    assert again.handle(Event(ACTIVATE)) is True
    assert again_engine.running is False

    buttons = [w for w in focusables(again.root) if isinstance(w, Button)]
    _, _, _, edit_footer, _ = buttons
    for widget in focusables(again.root):
        widget.focus(False)
    edit_footer.focus(True)
    assert again.handle(Event(ACTIVATE)) is True
    footers = _find_all(again.root, FooterEditor)
    assert len(footers) == 1  # footer editor opens in place

    save, _ = [w for w in focusables(footers[0]) if isinstance(w, Button)]
    for widget in focusables(again.root):
        widget.focus(False)
    save.focus(True)
    assert again.handle(Event(ACTIVATE)) is True
    assert "built with windfall" in config_path.read_text(encoding="utf-8")
    assert _find_all(again.root, FooterEditor) == []

    buttons = [w for w in focusables(again.root) if isinstance(w, Button)]
    add, _, _, _, _ = buttons
    for widget in focusables(again.root):
        widget.focus(False)
    add.focus(True)
    assert again.handle(Event(ACTIVATE)) is True
    adders = _find_all(again.root, AddWidget)
    assert len(adders) == 1  # palette opens in place

    save, _ = [w for w in focusables(adders[0]) if isinstance(w, Button)]
    for widget in focusables(again.root):
        widget.focus(False)
    save.focus(True)
    assert again.handle(Event(ACTIVATE)) is True
    assert '"type": "Label"' in config_path.read_text(encoding="utf-8")
    assert _find_all(again.root, AddWidget) == []

    buttons = [w for w in focusables(again.root) if isinstance(w, Button)]
    _, remove, _, _, _ = buttons
    for widget in focusables(again.root):
        widget.focus(False)
    remove.focus(True)
    assert again.handle(Event(ACTIVATE)) is True
    removers = _find_all(again.root, RemoveWidget)
    assert len(removers) == 1  # removal list opens in place

    save, _ = [w for w in focusables(removers[0]) if isinstance(w, Button)]
    for widget in focusables(again.root):
        widget.focus(False)
    save.focus(True)
    assert again.handle(Event(ACTIVATE)) is True
    assert '"type": "Label"' not in config_path.read_text(encoding="utf-8")
    assert _find_all(again.root, RemoveWidget) == []
    assert not any("New label" in line for line in Compositor().text(again))

    final = module.build(Engine())
    assert _find_all(final.root, FooterEditor) == []
    assert _find_all(final.root, HeaderEditor) == []
    assert _find_all(final.root, AddWidget) == []
    assert _find_all(final.root, RemoveWidget) == []
    rendered = Compositor().text(final)
    assert any("built with windfall" in line for line in rendered)
    assert any("Build your app here." in line for line in rendered)
    assert not any("New label" in line for line in rendered)