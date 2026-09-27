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

    def test_archive_collision_counting_starts_at_one(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The first name clash must land on -1, not skip to -2."""
        stamp = "20260927-120000"
        monkeypatch.setattr(menu_module.time, "strftime", lambda fmt: stamp)
        target = _make_project(tmp_path, "myapp")
        archive = tmp_path / "project" / ".archive"
        archive.mkdir()
        (archive / f"myapp-{stamp}").mkdir()  # force exactly one collision

        scene = menu_module.build_menu(Engine(), tmp_path)
        _, _, _, archive_btn, _ = editor_buttons(scene.root)
        for widget in focusables(scene.root):
            widget.focus(False)
        archive_btn.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        assert not target.exists()
        assert (archive / f"myapp-{stamp}-1" / "app.py").is_file()

    def test_archive_skips_every_taken_suffix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        stamp = "20260927-120000"
        monkeypatch.setattr(menu_module.time, "strftime", lambda fmt: stamp)
        _make_project(tmp_path, "myapp")
        archive = tmp_path / "project" / ".archive"
        archive.mkdir()
        for suffix in ("", "-1", "-2"):
            (archive / f"myapp-{stamp}{suffix}").mkdir()

        scene = menu_module.build_menu(Engine(), tmp_path)
        _, _, _, archive_btn, _ = editor_buttons(scene.root)
        for widget in focusables(scene.root):
            widget.focus(False)
        archive_btn.focus(True)
        assert scene.handle(Event(ACTIVATE)) is True
        assert (archive / f"myapp-{stamp}-3" / "app.py").is_file()

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


class TestStdinHandoff:
    """The fd handoff never ran under test before this class existed.

    ``_detach_stdin`` opens with ``if not os.isatty(0): return None``, and
    stdin is not a terminal under pytest, so every "open the project" test
    bailed on that first line and the whole ``dup``/``dup2``/``tcflush``
    dance went unexercised. These drive it with a fake ``os`` swapped into
    the module namespace, so no real file descriptor is ever touched.
    """

    @staticmethod
    def _fake_os(
        monkeypatch: pytest.MonkeyPatch,
        calls: list,
        *,
        isatty: bool = True,
        fail: str = "",
    ) -> None:
        def op(name: str, result):
            def inner(*args):
                calls.append((name, *args))
                if fail == name:
                    raise OSError(f"{name} failed")
                return result

            return inner

        monkeypatch.setattr(
            menu_module,
            "os",
            SimpleNamespace(
                isatty=op("isatty", isatty),
                dup=op("dup", 7),
                open=op("open", 9),
                dup2=op("dup2", None),
                close=op("close", None),
                devnull="/dev/null",
                O_RDONLY=0,
            ),
        )

    @staticmethod
    def _engine(calls: list) -> Engine:
        reader = SimpleNamespace(
            close=lambda: calls.append(("input.close",)),
            open=lambda: calls.append(("input.open",)),
        )
        return Engine(input_reader=reader)

    def test_detach_redirects_stdin_to_devnull(self, monkeypatch) -> None:
        calls: list = []
        self._fake_os(monkeypatch, calls)
        saved = menu_module._detach_stdin(self._engine(calls))
        assert saved == 7
        assert calls == [
            ("isatty", 0),
            ("dup", 0),
            ("open", "/dev/null", 0),
            ("dup2", 9, 0),
            ("close", 9),
            ("input.close",),
        ]

    def test_detach_skips_when_stdin_is_not_a_terminal(self, monkeypatch) -> None:
        calls: list = []
        self._fake_os(monkeypatch, calls, isatty=False)
        assert menu_module._detach_stdin(self._engine(calls)) is None
        assert [name for name, *_ in calls] == ["isatty"]

    def test_detach_gives_up_if_dup_fails(self, monkeypatch) -> None:
        calls: list = []
        self._fake_os(monkeypatch, calls, fail="dup")
        assert menu_module._detach_stdin(self._engine(calls)) is None
        assert ("close", 7) not in calls

    def test_detach_closes_the_dup_if_devnull_open_fails(self, monkeypatch) -> None:
        calls: list = []
        self._fake_os(monkeypatch, calls, fail="open")
        assert menu_module._detach_stdin(self._engine(calls)) is None
        assert ("close", 7) in calls
        assert ("dup2", 9, 0) not in calls

    def test_restore_puts_the_dup_back_and_flushes(self, monkeypatch) -> None:
        calls: list = []
        self._fake_os(monkeypatch, calls)
        monkeypatch.setattr(
            menu_module,
            "termios",
            SimpleNamespace(tcflush=lambda *a: calls.append(("tcflush", *a)), TCIFLUSH=2),
        )
        menu_module._restore_stdin(self._engine(calls), 7)
        assert calls == [
            ("dup2", 7, 0),
            ("close", 7),
            ("tcflush", 0, 2),
            ("input.open",),
        ]

    def test_restore_is_a_noop_without_a_saved_dup(self, monkeypatch) -> None:
        calls: list = []
        self._fake_os(monkeypatch, calls)
        menu_module._restore_stdin(self._engine(calls), None)
        assert calls == []

    def test_restore_survives_a_termios_failure(self, monkeypatch) -> None:
        """The dup is already back on fd 0, so a flush error must not escape."""
        calls: list = []
        self._fake_os(monkeypatch, calls)

        def boom(*args):
            raise OSError("tcflush failed")

        monkeypatch.setattr(
            menu_module, "termios", SimpleNamespace(tcflush=boom, TCIFLUSH=2)
        )
        menu_module._restore_stdin(self._engine(calls), 7)
        assert calls[-1] == ("input.open",)


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