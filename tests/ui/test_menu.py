"""Tests for the interactive project manager."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.helpers import editor_buttons, find_all, key
from windfall import Engine
from windfall.events import ACTIVATE, KEY, Event
from windfall.scene import focusables
from windfall.widgets import Button, Hotkey, ListView, TextInput
from windfall_cli import cli
from windfall_cli import menu as menu_module


def _make_project(base: Path, name: str) -> Path:
    target = base / "project" / name
    target.mkdir(parents=True)
    (target / "app.py").write_text("value = 1\n", encoding="utf-8")
    return target


def _stub_run(monkeypatch: pytest.MonkeyPatch, calls: list) -> None:
    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(wait=lambda: 0)

    monkeypatch.setattr(menu_module, "subprocess", SimpleNamespace(Popen=fake_popen))


class TestFindProjects:
    def test_lists_sorted_app_dirs(self, tmp_path: Path) -> None:
        _make_project(tmp_path, "bebra")
        _make_project(tmp_path, "alpha")
        stray = tmp_path / "project" / "notes.txt"
        stray.write_text("x", encoding="utf-8")
        nodir = tmp_path / "project" / "empty"
        nodir.mkdir()
        assert [p.name for p in menu_module.find_projects(tmp_path)] == ["alpha", "bebra"]

    def test_missing_root_is_empty(self, tmp_path: Path) -> None:
        assert menu_module.find_projects(tmp_path / "nowhere") == []

    def test_skips_dot_dirs(self, tmp_path: Path) -> None:
        _make_project(tmp_path, "app")
        hidden = tmp_path / "project" / ".archive"
        hidden.mkdir(parents=True)
        assert [p.name for p in menu_module.find_projects(tmp_path)] == ["app"]


class TestMenuSize:
    def test_format_size_uses_clean_units(self) -> None:
        assert menu_module.format_size(0) == "0 B"
        assert menu_module.format_size(512) == "512 B"
        assert menu_module.format_size(1024) == "1 KB"
        assert menu_module.format_size(1536) == "1.5 KB"
        assert menu_module.format_size(1024 * 1024) == "1 MB"
        assert menu_module.format_size(5 * 1024**3) == "5 GB"
        assert menu_module.format_size(2 * 1024**4) == "2 TB"

    def test_dir_size_sums_nested_files(self, tmp_path: Path) -> None:
        target = _make_project(tmp_path, "myapp")
        (target / "app.py").write_bytes(b"x" * 100)
        nested = target / "sub"
        nested.mkdir()
        (nested / "data.bin").write_bytes(b"y" * 200)
        assert menu_module.dir_size(target) == 300

    def test_sidebar_shows_total_size(self, tmp_path: Path) -> None:
        from windfall import Compositor

        target = _make_project(tmp_path, "myapp")
        (target / "app.py").write_bytes(b"x" * 2048)
        scene = menu_module.build_menu(Engine(), tmp_path)
        assert any("2 KB" in line for line in Compositor().text(scene))


class TestMenuActions:
    def test_open_runs_app_in_its_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list = []
        _stub_run(monkeypatch, calls)
        target = _make_project(tmp_path, "myapp")
        scene = menu_module.build_menu(Engine(), tmp_path)
        _, open_btn, _, _, _ = editor_buttons(scene.root)
        for widget in focusables(scene.root):
            widget.focus(False)
        open_btn.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        assert len(calls) == 1
        (args, kwargs) = calls[0]
        assert args[0] == ["uv", "run", "python", "app.py"]
        assert kwargs["cwd"] == target

    def test_delete_asks_confirm_and_removes(self, tmp_path: Path) -> None:
        target = _make_project(tmp_path, "myapp")
        _make_project(tmp_path, "other")
        scene = menu_module.build_menu(Engine(), tmp_path)
        _, _, delete, _, _ = editor_buttons(scene.root)
        for widget in focusables(scene.root):
            widget.focus(False)
        delete.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        yes, _no = [w for w in focusables(scene.root) if isinstance(w, Button)][-2:]
        for widget in focusables(scene.root):
            widget.focus(False)
        yes.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        assert not target.exists()
        assert (tmp_path / "project" / "other").is_dir()
        views = [w for w in focusables(scene.root) if isinstance(w, ListView)]
        assert views[0].selection == 0

    def test_delete_no_keeps_project(self, tmp_path: Path) -> None:
        target = _make_project(tmp_path, "myapp")
        scene = menu_module.build_menu(Engine(), tmp_path)
        _, _, delete, _, _ = editor_buttons(scene.root)
        for widget in focusables(scene.root):
            widget.focus(False)
        delete.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        _, no = [w for w in focusables(scene.root) if isinstance(w, Button)][-2:]
        for widget in focusables(scene.root):
            widget.focus(False)
        no.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        assert target.is_dir()
        assert len(editor_buttons(scene.root)) == 5  # actions restored

    def test_archive_moves_to_timestamped_dir(self, tmp_path: Path) -> None:
        target = _make_project(tmp_path, "myapp")
        scene = menu_module.build_menu(Engine(), tmp_path)
        _, _, _, archive, _ = editor_buttons(scene.root)
        for widget in focusables(scene.root):
            widget.focus(False)
        archive.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        assert not target.exists()
        archived = list((tmp_path / "project" / ".archive").iterdir())
        assert len(archived) == 1
        assert archived[0].name.startswith("myapp-")
        assert (archived[0] / "app.py").is_file()

    def test_new_creates_project_and_refreshes(self, tmp_path: Path) -> None:
        scene = menu_module.build_menu(Engine(), tmp_path)
        new, _, _, _, _ = editor_buttons(scene.root)
        for widget in focusables(scene.root):
            widget.focus(False)
        new.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        fields = [w for w in focusables(scene.root) if isinstance(w, TextInput)]
        assert len(fields) == 1  # name form opens in place
        fields[0].focus(True)
        for char in "ab":
            assert fields[0].handle(key(char)) is True
        fields[0].focus(False)
        create, _ = [w for w in focusables(scene.root) if isinstance(w, Button)][-2:]
        create.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        assert (tmp_path / "project" / "ab" / "app.py").is_file()
        views = [w for w in focusables(scene.root) if isinstance(w, ListView)]
        assert "ab" in views[0]._items
        assert len(editor_buttons(scene.root)) == 5  # actions restored

    def test_new_invalid_name_stays_with_error(self, tmp_path: Path) -> None:
        from windfall import Compositor

        scene = menu_module.build_menu(Engine(), tmp_path)
        new, _, _, _, _ = editor_buttons(scene.root)
        for widget in focusables(scene.root):
            widget.focus(False)
        new.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        fields = [w for w in focusables(scene.root) if isinstance(w, TextInput)]
        fields[0].focus(True)
        for char in "9bad":
            fields[0].handle(key(char))
        fields[0].focus(False)
        create, _ = [w for w in focusables(scene.root) if isinstance(w, Button)][-2:]
        create.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        assert not (tmp_path / "project" / "9bad").exists()
        assert len([w for w in focusables(scene.root) if isinstance(w, TextInput)]) == 1
        assert any("Could not create" in line for line in Compositor().text(scene))


class TestMenuUi:
    def test_empty_menu_actions_are_noops(self, tmp_path: Path) -> None:
        scene = menu_module.build_menu(Engine(), tmp_path)

        def press(button) -> None:
            for widget in focusables(scene.root):
                widget.focus(False)
            button.focus(True)
            assert scene.handle(Event(ACTIVATE)) is True

        buttons = [w for w in focusables(scene.root) if isinstance(w, Button)]
        new, open_btn, delete, archive, quit = buttons
        press(open_btn)
        press(delete)
        press(archive)
        press(quit)
        press(new)
        assert len([w for w in focusables(scene.root) if isinstance(w, TextInput)]) == 1
        cancel = [w for w in focusables(scene.root) if isinstance(w, Button)][-1]
        press(cancel)
        assert not [w for w in focusables(scene.root) if isinstance(w, TextInput)]
        views = [w for w in focusables(scene.root) if isinstance(w, ListView)]
        assert "no projects" in views[0]._items[0]

    def test_hotkeys_focus_buttons_and_quit(self, tmp_path: Path) -> None:
        _make_project(tmp_path, "myapp")
        engine = Engine()
        scene = menu_module.build_menu(engine, tmp_path)
        assert len(find_all(scene.root, Hotkey)) == 5
        buttons = [w for w in focusables(scene.root) if isinstance(w, Button)]
        for key_, index in [("n", 0), ("o", 1), ("d", 2), ("a", 3)]:
            for widget in focusables(scene.root):
                widget.focus(False)
            assert scene.handle(Event(KEY, {"key": key_})) is True
            assert buttons[index].focused is True
        engine.running = True
        assert scene.handle(Event(KEY, {"key": "x"})) is True
        assert engine.running is False


class TestMenuCli:
    def test_help_lists_subcommand(self, capsys) -> None:
        with pytest.raises(SystemExit) as exc:
            cli.main(["menu", "--help"])
        assert exc.value.code == 0
        assert "menu" in capsys.readouterr().out


class TestMenuShutdown:
    def test_farewell_prints_shutdown_line(self, capsys) -> None:
        menu_module.farewell()
        out = capsys.readouterr().out
        assert "\033[2J" in out
        assert "Thanks for using Windfall. Goodbye!" in out