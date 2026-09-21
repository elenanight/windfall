"""Tests for the interactive project manager."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from windfall import Engine
from windfall.events import ACTIVATE, KEY, Event
from windfall.scene import focusables
from windfall.widgets import Button, ListView, TextInput
from windfall_cli import cli
from windfall_cli import menu as menu_module


def _make_project(base: Path, name: str) -> Path:
    target = base / "project" / name
    target.mkdir(parents=True)
    (target / "app.py").write_text("value = 1\n", encoding="utf-8")
    return target


def _buttons(scene) -> list[Button]:
    return [w for w in focusables(scene.root) if isinstance(w, Button)]


def _key(char: str) -> Event:
    return Event(KEY, {"key": char})


def _stub_run(monkeypatch: pytest.MonkeyPatch, calls: list) -> None:
    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(menu_module, "subprocess", SimpleNamespace(run=fake_run))


def test_find_projects_lists_sorted_app_dirs(tmp_path: Path) -> None:
    _make_project(tmp_path, "bebra")
    _make_project(tmp_path, "alpha")
    stray = tmp_path / "project" / "notes.txt"
    stray.write_text("x", encoding="utf-8")
    nodir = tmp_path / "project" / "empty"
    nodir.mkdir()
    assert [p.name for p in menu_module.find_projects(tmp_path)] == ["alpha", "bebra"]


def test_find_projects_missing_root_is_empty(tmp_path: Path) -> None:
    assert menu_module.find_projects(tmp_path / "nowhere") == []


def test_find_projects_skips_dot_dirs(tmp_path: Path) -> None:
    _make_project(tmp_path, "app")
    hidden = tmp_path / "project" / ".archive"
    hidden.mkdir(parents=True)
    assert [p.name for p in menu_module.find_projects(tmp_path)] == ["app"]


def test_open_runs_app_in_its_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list = []
    _stub_run(monkeypatch, calls)
    target = _make_project(tmp_path, "myapp")
    scene = menu_module.build_menu(Engine(), tmp_path)
    _, open_btn, _, _, _ = _buttons(scene)
    for widget in focusables(scene.root):
        widget.focus(False)
    open_btn.focus(True)
    assert scene.handle(Event(ACTIVATE)) is True
    assert len(calls) == 1
    (args, kwargs) = calls[0]
    assert args[0] == ["uv", "run", "python", "app.py"]
    assert kwargs["cwd"] == target


def test_delete_asks_confirm_and_removes(tmp_path: Path) -> None:
    target = _make_project(tmp_path, "myapp")
    _make_project(tmp_path, "other")
    scene = menu_module.build_menu(Engine(), tmp_path)
    _, _, delete, _, _ = _buttons(scene)
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


def test_delete_no_keeps_project(tmp_path: Path) -> None:
    target = _make_project(tmp_path, "myapp")
    scene = menu_module.build_menu(Engine(), tmp_path)
    _, _, delete, _, _ = _buttons(scene)
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
    assert len(_buttons(scene)) == 5  # actions restored


def test_archive_moves_to_timestamped_dir(tmp_path: Path) -> None:
    target = _make_project(tmp_path, "myapp")
    scene = menu_module.build_menu(Engine(), tmp_path)
    _, _, _, archive, _ = _buttons(scene)
    for widget in focusables(scene.root):
        widget.focus(False)
    archive.focus(True)
    assert scene.handle(Event(ACTIVATE)) is True
    assert not target.exists()
    archived = list((tmp_path / "project" / ".archive").iterdir())
    assert len(archived) == 1
    assert archived[0].name.startswith("myapp-")
    assert (archived[0] / "app.py").is_file()


def test_empty_menu_actions_are_noops(tmp_path: Path) -> None:
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


def test_menu_help_lists_subcommand(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["menu", "--help"])
    assert exc.value.code == 0
    assert "menu" in capsys.readouterr().out


def test_new_creates_project_and_refreshes(tmp_path: Path) -> None:
    scene = menu_module.build_menu(Engine(), tmp_path)
    new, _, _, _, _ = _buttons(scene)
    for widget in focusables(scene.root):
        widget.focus(False)
    new.focus(True)
    assert scene.handle(Event(ACTIVATE)) is True
    fields = [w for w in focusables(scene.root) if isinstance(w, TextInput)]
    assert len(fields) == 1  # name form opens in place
    fields[0].focus(True)
    for char in "ab":
        assert fields[0].handle(_key(char)) is True
    fields[0].focus(False)
    create, _ = [w for w in focusables(scene.root) if isinstance(w, Button)][-2:]
    create.focus(True)
    assert scene.handle(Event(ACTIVATE)) is True
    assert (tmp_path / "project" / "ab" / "app.py").is_file()
    views = [w for w in focusables(scene.root) if isinstance(w, ListView)]
    assert "ab" in views[0]._items
    assert len(_buttons(scene)) == 5  # actions restored


def test_new_invalid_name_stays_with_error(tmp_path: Path) -> None:
    from windfall import Compositor

    scene = menu_module.build_menu(Engine(), tmp_path)
    new, _, _, _, _ = _buttons(scene)
    for widget in focusables(scene.root):
        widget.focus(False)
    new.focus(True)
    assert scene.handle(Event(ACTIVATE)) is True
    fields = [w for w in focusables(scene.root) if isinstance(w, TextInput)]
    fields[0].focus(True)
    for char in "9bad":
        fields[0].handle(_key(char))
    fields[0].focus(False)
    create, _ = [w for w in focusables(scene.root) if isinstance(w, Button)][-2:]
    create.focus(True)
    assert scene.handle(Event(ACTIVATE)) is True
    assert not (tmp_path / "project" / "9bad").exists()
    assert len([w for w in focusables(scene.root) if isinstance(w, TextInput)]) == 1
    assert any("Could not create" in line for line in Compositor().text(scene))
