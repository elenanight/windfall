"""Tests for the engine's event loop and headless stepping."""

from __future__ import annotations

import pytest

from windfall.anim import Tween, ease_linear
from windfall.engine import Engine
from windfall.events import ACTIVATE, QUIT, Event
from windfall.input import InputReader
from windfall.primitives import Divider
from windfall.scene import Scene
from windfall.widgets import Button, Footer, Header, Label, ListView, TextInput


class FakeLive:
    """Minimal stand-in for ``rich.live.Live`` used in run-loop tests."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args) -> bool:
        return False

    def update(self, renderable) -> None:
        pass

    def refresh(self) -> None:
        pass


class FakeTerminal:
    """No-op stand-in for ``windfall.terminal.RawTerminal`` in run-loop tests."""

    def __enter__(self):
        return self

    def __exit__(self, *args) -> bool:
        return False


def _scripted(tokens: list[str]):
    remaining = list(tokens)

    def read() -> str:
        if remaining:
            return remaining.pop(0)
        raise EOFError

    return read


def test_engine_starts_empty() -> None:
    engine = Engine()
    assert engine.frames.current is None
    assert engine.running is False


def test_use_scene_pushes_a_frame() -> None:
    engine = Engine()
    scene = Scene(name="title")
    engine.use_scene(scene)
    assert engine.frames.current is not None
    assert engine.frames.current.scene is scene


def test_step_dispatches_events_to_focused_widget() -> None:
    calls: list[str] = []
    scene = Scene(name="menu", root=Button("Go", on_activate=lambda: calls.append("go")))
    scene.root.focus(True)
    engine = Engine()
    engine.use_scene(scene)
    engine.post_event(Event(ACTIVATE))
    engine.step(0.016)
    assert calls == ["go"]


def test_step_updates_scene_timeline() -> None:
    scene = Scene(name="anim")
    tween = Tween(0.0, 10.0, 1.0, ease=ease_linear)
    scene.timeline.add(tween)
    engine = Engine()
    engine.use_scene(scene)
    engine.step(0.5)
    assert tween.value == pytest.approx(5.0)


def test_quit_event_stops_engine() -> None:
    engine = Engine()
    engine.running = True
    engine.post_event(Event(QUIT))
    engine.step(0.016)
    assert engine.running is False


def test_quit_stops_run_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("windfall.engine.Live", FakeLive)
    monkeypatch.setattr("windfall.engine.RawTerminal", FakeTerminal)
    engine = Engine(input_reader=InputReader(read_char=_scripted(["\x03"])))
    engine.use_scene(Scene(name="demo"))
    engine.run(fps=200)
    assert engine.running is False


def test_run_typing_reaches_focused_text_input(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("windfall.engine.Live", FakeLive)
    monkeypatch.setattr("windfall.engine.RawTerminal", FakeTerminal)
    field = TextInput(value="")
    field.focus(True)
    engine = Engine(input_reader=InputReader(read_char=_scripted(["z", "\x03"])))
    engine.use_scene(Scene(name="chat", root=field))
    engine.run(fps=200)
    assert field.value == "z"


def test_make_header_assembles_widget_from_primitives() -> None:
    engine = Engine()
    header = engine.make_header("hi", border="red", fg="green")
    assert isinstance(header, Header)
    assert header.size() == Header("hi").size()


def test_make_footer_assembles_widget_from_primitives() -> None:
    engine = Engine()
    footer = engine.make_footer("bye", border="red", fg="green")
    assert isinstance(footer, Footer)
    assert footer.size() == Footer("bye").size()


def test_make_widget_builds_each_kind() -> None:
    engine = Engine()
    assert isinstance(engine.make_widget("Label"), Label)
    assert isinstance(engine.make_widget("Button"), Button)
    assert isinstance(engine.make_widget("TextInput"), TextInput)
    assert isinstance(engine.make_widget("ListView"), ListView)
    assert isinstance(engine.make_widget("Divider"), Divider)
    assert isinstance(engine.make_widget("Nope"), Label)  # unknown kinds fall back


def test_make_widget_applies_id_and_text() -> None:
    engine = Engine()
    label = engine.make_widget("Label", id="greeting", text="Hello")
    assert label.id == "greeting"
    assert label.size() == Label("Hello").size()
    button = engine.make_widget("Button", id="save", text="Go")
    assert button.id == "save"
    assert button.size() == Button("Go").size()
    field = engine.make_widget("TextInput", id="name", text="amy")
    assert field.id == "name"
    assert field.value == "amy"
    divider = engine.make_widget("Divider", id="gap", text="ignored")
    assert divider.id == "gap"
    assert engine.make_widget("Label", id="m", text="").size() == Label("New label").size()