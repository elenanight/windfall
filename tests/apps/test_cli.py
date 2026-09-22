"""Tests for the ``windfall`` command-line interface."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.helpers import find_all, key, move
from windfall import Compositor, Engine
from windfall.events import ACTIVATE, Event
from windfall.primitives import Connector
from windfall.scene import focusables
from windfall.widgets import (
    AddWidget,
    Button,
    EditMenu,
    FooterEditor,
    HeaderEditor,
    Hotkey,
    Label,
    ListView,
    RemoveWidget,
    TextInput,
)
from windfall_cli import cli


def _stub_run(monkeypatch: pytest.MonkeyPatch, calls: list) -> None:
    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cli, "subprocess", SimpleNamespace(run=fake_run))


@pytest.fixture
def scaffold(tmp_path: Path):
    """Scaffold ``myapp`` once per test and return its loaded module and paths."""
    import importlib.util

    base = tmp_path / "work"
    assert cli.main(["new", "myapp", "--dest", str(base)]) == 0
    app_path = base / "project" / "myapp" / "app.py"
    spec = importlib.util.spec_from_file_location("scaffolded_myapp", app_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return SimpleNamespace(
        module=module,
        home=app_path.parent,
        config=app_path.parent / ".windfallrc.json",
    )


def _unfocus_all(scene) -> None:
    for widget in focusables(scene.root):
        widget.focus(False)


def _focus_button(scene, index: int):
    buttons = [w for w in focusables(scene.root) if isinstance(w, Button)]
    _unfocus_all(scene)
    buttons[index].focus(True)
    return buttons[index]


def _open_menu(scene, row: int = 0) -> None:
    """Open the Edit menu, pick the entry at ``row``, and swap to the editor."""
    _focus_button(scene, 2)  # E -> Edit
    assert scene.handle(Event(ACTIVATE)) is True
    menus = find_all(scene.root, EditMenu)
    assert len(menus) == 1
    menu_lists = [w for w in focusables(menus[0]) if isinstance(w, ListView)]
    menu_lists[0].focus(True)
    for _ in range(row):
        menu_lists[0].handle(move("down"))
    assert scene.handle(Event(ACTIVATE)) is True


def _save(editor, scene) -> None:
    save, _ = [w for w in focusables(editor) if isinstance(w, Button)]
    _unfocus_all(scene)
    save.focus(True)
    assert scene.handle(Event(ACTIVATE)) is True


def _add_label(scene) -> None:
    _focus_button(scene, 0)  # W -> Add widget
    assert scene.handle(Event(ACTIVATE)) is True
    adders = find_all(scene.root, AddWidget)
    assert len(adders) == 1
    _save(adders[0], scene)


def _add_named_label(scene) -> None:
    _focus_button(scene, 0)  # W -> Add widget
    assert scene.handle(Event(ACTIVATE)) is True
    adders = find_all(scene.root, AddWidget)
    assert len(adders) == 1
    fields = [w for w in focusables(adders[0]) if isinstance(w, TextInput)]
    fields[0].focus(True)
    for char in "greeting":
        fields[0].handle(key(char))
    fields[0].focus(False)
    fields[1].focus(True)
    for char in "Hello!":
        fields[1].handle(key(char))
    fields[1].focus(False)
    _save(adders[0], scene)


class TestCliBasics:
    def test_missing_command_prints_help(self, capsys) -> None:
        assert cli.main([]) == 0
        assert "windfall" in capsys.readouterr().out

    def test_version_flag(self, capsys) -> None:
        with pytest.raises(SystemExit) as exc:
            cli.main(["--version"])
        assert exc.value.code == 0
        assert "windfall" in capsys.readouterr().out

    def test_help_subcommand(self, capsys) -> None:
        assert cli.main(["help"]) == 0
        assert "windfall" in capsys.readouterr().out

    def test_unknown_command_exits_two(self) -> None:
        with pytest.raises(SystemExit) as exc:
            cli.main(["frobnicate"])
        assert exc.value.code == 2


class TestNewScaffold:
    def test_scaffolds_app(self, tmp_path: Path) -> None:
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

    def test_defaults_to_current_dir(self, monkeypatch, tmp_path: Path) -> None:
        monkeypatch.chdir(tmp_path)
        assert cli.main(["new", "myapp"]) == 0
        dest = tmp_path / "project" / "myapp"
        assert (dest / "app.py").is_file()

    def test_rejects_existing_destination(self, tmp_path: Path) -> None:
        dest = tmp_path / "taken" / "project" / "app"
        dest.mkdir(parents=True)
        assert cli.main(["new", "app", "--dest", str(tmp_path / "taken")]) == 2

    def test_rejects_bad_name(self, tmp_path: Path) -> None:
        assert cli.main(["new", "9bad", "--dest", str(tmp_path / "bad")]) == 2

    def test_rejects_unknown_template(self, tmp_path: Path) -> None:
        assert cli.main(["new", "x", "--template", "nope", "--dest", str(tmp_path / "x")]) == 2

    def test_yes_flag_runs_app_without_prompt(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list = []
        _stub_run(monkeypatch, calls)
        base = tmp_path / "yes"
        assert cli.main(["new", "myapp", "--dest", str(base), "--yes"]) == 0
        assert len(calls) == 1
        (args, kwargs) = calls[0]
        assert args[0] == ["uv", "run", "python", "app.py"]
        assert kwargs["cwd"] == base / "project" / "myapp"

    def test_prompts_and_runs_on_yes(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        calls: list = []
        prompts: list = []
        _stub_run(monkeypatch, calls)
        monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
        monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "y")
        base = tmp_path / "prompt"
        assert cli.main(["new", "myapp", "--dest", str(base)]) == 0
        assert prompts == ["Run 'myapp' now? [y/N]: "]
        assert "Starting myapp ..." in capsys.readouterr().out
        assert len(calls) == 1

    def test_prompts_and_skips_on_no(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list = []
        _stub_run(monkeypatch, calls)
        monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
        monkeypatch.setattr("builtins.input", lambda _: "n")
        base = tmp_path / "skip"
        assert cli.main(["new", "myapp", "--dest", str(base)]) == 0
        assert calls == []


class TestSubcommands:
    def test_check_smoke_passes(self) -> None:
        assert cli.main(["check", "--ticks", "10"]) == 0

    def test_demo_headless_passes(self) -> None:
        assert cli.main(["demo", "--headless", "--ticks", "5"]) == 0

    def test_demo_scene_is_buildable(self) -> None:
        from windfall_cli.demo import build_scene

        scene = build_scene()
        assert scene.name == "demo"
        assert scene.size().x > 0


class TestInspect:
    def test_list_reports_scenes(self, tmp_path: Path, capsys) -> None:
        app = tmp_path / "app.py"
        app.write_text(
            "from windfall import Scene\n\n\nclass TitleScene(Scene):\n    pass\n\nclass Helper:\n    pass\n",
            encoding="utf-8",
        )
        assert cli.main(["list", str(app)]) == 0
        out = capsys.readouterr().out
        assert "TitleScene" in out
        assert "Helper" not in out

    def test_list_missing_file(self) -> None:
        assert cli.main(["list", "no_such_file.py"]) == 2

    def test_scenes_in_parses_ast(self, tmp_path: Path) -> None:
        from windfall_cli.inspect import scenes_in

        app = tmp_path / "a.py"
        app.write_text(
            "from windfall import Component, Scene\nclass A(Scene):\n    pass\nclass B(Component):\n    pass\n",
            encoding="utf-8",
        )
        assert scenes_in(app) == ["A", "B"]


class TestAliases:
    def test_create_scaffolds(self, tmp_path: Path) -> None:
        base = tmp_path / "alias"
        assert cli.main(["--create", "aliasapp", "--dest", str(base)]) == 0
        assert (base / "project" / "aliasapp" / "app.py").is_file()

    def test_create_bad_name(self, tmp_path: Path) -> None:
        assert cli.main(["--create", "9bad", "--dest", str(tmp_path / "x")]) == 2

    def test_run_executes_a_file(self, tmp_path: Path) -> None:
        app = tmp_path / "app.py"
        app.write_text("value = 42\n", encoding="utf-8")
        assert cli.main(["--run", str(app)]) == 0

    def test_run_missing_file(self) -> None:
        assert cli.main(["--run", "no_such_file.py"]) == 2

    def test_demo_headless(self) -> None:
        assert cli.main(["--demo", "--headless", "--ticks", "3"]) == 0

    def test_check(self) -> None:
        assert cli.main(["--check", "--ticks", "5"]) == 0

    def test_list(self, tmp_path: Path, capsys) -> None:
        app = tmp_path / "app.py"
        app.write_text("from windfall import Scene\nclass MyScene(Scene):\n    pass\n", encoding="utf-8")
        assert cli.main(["--list", str(app)]) == 0
        assert "MyScene" in capsys.readouterr().out

    def test_example_headless(self) -> None:
        assert cli.main(["--example", "bouncer", "--headless", "--ticks", "3"]) == 0

    def test_example_unknown(self) -> None:
        assert cli.main(["--example", "nope"]) == 2

    def test_examples_lists(self, capsys) -> None:
        assert cli.main(["--examples"]) == 0
        out = capsys.readouterr().out
        assert "menu" in out
        assert "bouncer" in out
        assert "animation" in out
        assert "snake" in out


class TestExampleCommand:
    def test_subcommand_headless(self) -> None:
        assert cli.main(["example", "snake", "--headless", "--ticks", "5"]) == 0

    def test_subcommand_unknown_choice(self) -> None:
        with pytest.raises(SystemExit) as exc:
            cli.main(["example", "nope"])
        assert exc.value.code == 2


class TestScaffoldedApp:
    def test_windfall_home_resolves(self, scaffold) -> None:
        home = scaffold.module.windfall_home()
        assert home is not None
        assert (home / "pyproject.toml").is_file()
        assert (home / "windfall" / "__init__.py").is_file()

    def test_builds_cleanly(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        assert scene.name == "myapp"
        assert find_all(scene.root, HeaderEditor) == []
        assert find_all(scene.root, FooterEditor) == []
        assert len(find_all(scene.root, Hotkey)) == 4
        shafts = find_all(scene.root, Connector)
        assert len(shafts) == 3
        assert all(shaft.state == "available" and shaft.horizontal for shaft in shafts)
        rendered = Compositor().text(scene)
        assert any("Build your app here." in line for line in rendered)

    def test_hotkeys_focus_buttons_and_quit(self, scaffold) -> None:
        engine = Engine()
        scene = scaffold.module.build(engine)
        buttons = [w for w in focusables(scene.root) if isinstance(w, Button)]
        for char, index in [("w", 0), ("r", 1), ("e", 2)]:
            _unfocus_all(scene)
            assert scene.handle(key(char)) is True
            assert buttons[index].focused is True
        engine.running = True
        assert scene.handle(key("q")) is True
        assert engine.running is False

    def test_open_header_editor_pauses_hotkeys(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _open_menu(scene, row=0)  # "Header bar"
        editors = find_all(scene.root, HeaderEditor)
        assert len(editors) == 1  # menu swaps itself for the editor
        assert find_all(scene.root, EditMenu) == []
        main = scene.root.children[0]
        assert main.children[1] is editors[0]  # resting under the menu, above the header
        assert find_all(scene.root, Hotkey) == []  # hotkey parked while editing

        fields = [w for w in focusables(editors[0]) if isinstance(w, TextInput)]
        fields[0].focus(True)
        assert scene.handle(key("e")) is True
        assert fields[0].value.endswith("e")  # typing wins over the hotkey
        assert fields[0].focused is True

    def test_save_header_writes_config(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _open_menu(scene, row=0)
        editors = find_all(scene.root, HeaderEditor)
        _save(editors[0], scene)
        assert scaffold.config.is_file()
        assert "hello from myapp!" in scaffold.config.read_text(encoding="utf-8")
        assert find_all(scene.root, HeaderEditor) == []
        assert len(find_all(scene.root, Hotkey)) == 4  # hotkeys restored after close

    def test_hide_header_persists_across_boot(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _open_menu(scene, row=0)
        editors = find_all(scene.root, HeaderEditor)
        views = [w for w in focusables(editors[0]) if isinstance(w, ListView)]
        views[2].focus(True)
        views[2].handle(move("down"))
        views[2].focus(False)
        _save(editors[0], scene)
        assert '"header_visible": false' in scaffold.config.read_text(encoding="utf-8")

        hidden = scaffold.module.build(Engine())  # later boot rebuilds from the saved spec
        assert not any("hello from myapp!" in line for line in Compositor().text(hidden))
        _open_menu(hidden, row=0)
        editors = find_all(hidden.root, HeaderEditor)
        views = [w for w in focusables(editors[0]) if isinstance(w, ListView)]
        assert views[2].selection == 1  # still "No" from the saved flag
        views[2].focus(True)
        views[2].handle(move("up"))
        views[2].focus(False)
        _save(editors[0], hidden)
        assert '"header_visible": true' in scaffold.config.read_text(encoding="utf-8")
        assert any("hello from myapp!" in line for line in Compositor().text(hidden))

    def test_edit_footer_bar_persists(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _open_menu(scene, row=1)  # "Footer bar"
        footers = find_all(scene.root, FooterEditor)
        assert len(footers) == 1  # footer editor opens in place
        _save(footers[0], scene)
        assert "built with windfall" in scaffold.config.read_text(encoding="utf-8")
        assert find_all(scene.root, FooterEditor) == []

    def test_add_label_hides_guides(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _add_label(scene)
        assert '"type": "Label"' in scaffold.config.read_text(encoding="utf-8")
        assert find_all(scene.root, AddWidget) == []
        rendered = Compositor().text(scene)
        assert any("New label" in line for line in rendered)
        assert not any("Build your app here." in line for line in rendered)

    def test_edit_widget_placement_preset(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _add_label(scene)
        _open_menu(scene, row=2)  # the placed Label
        editors = find_all(scene.root, AddWidget)
        assert len(editors) == 1  # widget editor opens preset to current values
        kinds, places, _ = [w for w in focusables(editors[0]) if isinstance(w, ListView)]
        assert kinds.selection == 0
        assert places.selection == 0  # still "left" from the drop
        places.focus(True)
        places.handle(move("down"))
        places.handle(move("down"))
        places.focus(False)
        _save(editors[0], scene)
        assert '"placement": "right"' in scaffold.config.read_text(encoding="utf-8")
        assert find_all(scene.root, AddWidget) == []
        assert any("New label" in line for line in Compositor().text(scene))

    def test_edit_widget_id_and_text(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _add_label(scene)
        _open_menu(scene, row=2)
        editors = find_all(scene.root, AddWidget)
        fields = [w for w in focusables(editors[0]) if isinstance(w, TextInput)]
        assert len(fields) == 2  # id and text fields open preset
        fields[0].focus(True)
        for char in "greeting":
            fields[0].handle(key(char))
        assert fields[0].value == "greeting"
        fields[0].focus(False)
        fields[1].focus(True)
        for char in "Hello!":
            fields[1].handle(key(char))
        fields[1].focus(False)
        _save(editors[0], scene)
        config = scaffold.config.read_text(encoding="utf-8")
        assert '"id": "greeting"' in config
        assert '"text": "Hello!"' in config
        assert find_all(scene.root, AddWidget) == []
        rendered = Compositor().text(scene)
        assert any("Hello!" in line for line in rendered)
        assert not any("New label" in line for line in rendered)

    def test_remove_widget_restores_guides(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _add_label(scene)
        _focus_button(scene, 1)  # R -> Remove widget
        assert scene.handle(Event(ACTIVATE)) is True
        removers = find_all(scene.root, RemoveWidget)
        assert len(removers) == 1  # removal list opens in place
        _save(removers[0], scene)
        assert '"type": "Label"' not in scaffold.config.read_text(encoding="utf-8")
        assert find_all(scene.root, RemoveWidget) == []
        rendered = Compositor().text(scene)
        assert not any("New label" in line for line in rendered)
        assert any("Build your app here." in line for line in rendered)

    def test_remove_palette_lists_widget_by_id(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _add_named_label(scene)
        rebuilt = scaffold.module.build(Engine())
        buttons = [w for w in focusables(rebuilt.root) if isinstance(w, Button)]
        buttons[1].focus(True)
        assert rebuilt.handle(Event(ACTIVATE)) is True
        removers = find_all(rebuilt.root, RemoveWidget)
        assert len(removers) == 1
        entries = [w for w in focusables(removers[0]) if isinstance(w, ListView)]
        assert entries[0]._items == ["greeting · left"]  # listing names the id

    def test_boot_rebuilds_saved_state(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _add_named_label(scene)

        rebuilt = scaffold.module.build(Engine())  # a later boot rebuilds from the saved spec
        rendered = Compositor().text(rebuilt)
        assert any("Hello!" in line for line in rendered)
        assert not any("New label" in line for line in rendered)
        labels = [label for label in find_all(rebuilt.root, Label) if label.id == "greeting"]
        assert len(labels) == 1
        assert labels[0].size() == Label("Hello!").size()

    def test_final_boot_restores_clean_state(self, scaffold) -> None:
        scene = scaffold.module.build(Engine())
        _add_named_label(scene)
        _open_menu(scene, row=2)
        editors = find_all(scene.root, AddWidget)
        fields = [w for w in focusables(editors[0]) if isinstance(w, TextInput)]
        fields[0].focus(True)
        for char in "greeting":
            fields[0].handle(key(char))
        fields[0].focus(False)
        fields[1].focus(True)
        for char in "Hello!":
            fields[1].handle(key(char))
        fields[1].focus(False)
        _save(editors[0], scene)
        _open_menu(scene, row=1)  # footer first
        footers = find_all(scene.root, FooterEditor)
        _save(footers[0], scene)
        _focus_button(scene, 1)  # R -> Remove widget
        assert scene.handle(Event(ACTIVATE)) is True
        removers = find_all(scene.root, RemoveWidget)
        assert len(removers) == 1
        _save(removers[0], scene)

        final = scaffold.module.build(Engine())
        assert find_all(final.root, FooterEditor) == []
        assert find_all(final.root, HeaderEditor) == []
        assert find_all(final.root, AddWidget) == []
        assert find_all(final.root, RemoveWidget) == []
        rendered = Compositor().text(final)
        assert any("built with windfall" in line for line in rendered)
        assert any("Build your app here." in line for line in rendered)
        assert not any("New label" in line for line in rendered)

    def test_back_button_stops_loop(self, scaffold) -> None:
        engine = Engine()
        scene = scaffold.module.build(engine)
        quit = next(
            widget
            for widget in focusables(scene.root)
            if isinstance(widget, Button) and widget.on_activate == engine.stop
        )
        _unfocus_all(scene)
        engine.running = True
        quit.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        assert engine.running is False  # Back stops the loop
        assert any("← Back" in line for line in Compositor().text(scene))