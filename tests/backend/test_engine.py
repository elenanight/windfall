"""Tests for the engine's event loop and headless stepping."""

from __future__ import annotations

import pytest

from windfall.anim import Tween, ease_linear
from windfall.component import Component
from windfall.engine import Engine
from windfall.events import ACTIVATE, QUIT, RESIZE, Event
from windfall.geom import Vec2
from windfall.input import InputReader
from windfall.primitives import Divider
from windfall.scene import Scene
from windfall.widgets import Button, Footer, Header, Label, ListView, TextInput


class _Recorder(Component):
    """A leaf that records every event the scene routes to it."""

    def __init__(self, seen: list[Event]) -> None:
        super().__init__()
        self._seen = seen

    def size(self) -> Vec2:
        return Vec2(1, 1)

    def draw(self, canvas, rect) -> None:
        pass

    def handle(self, event: Event) -> bool:
        self._seen.append(event)
        return False


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


class TestEngine:
    def test_starts_empty(self) -> None:
        engine = Engine()
        assert engine.frames.current is None
        assert engine.running is False

    def test_use_scene_pushes_a_frame(self) -> None:
        engine = Engine()
        scene = Scene(name="title")
        engine.use_scene(scene)
        assert engine.frames.current is not None
        assert engine.frames.current.scene is scene

    def test_step_dispatches_events_to_focused_widget(self) -> None:
        calls: list[str] = []
        scene = Scene(name="menu", root=Button("Go", on_activate=lambda: calls.append("go")))
        scene.root.focus(True)
        engine = Engine()
        engine.use_scene(scene)
        engine.post_event(Event(ACTIVATE))
        engine.step(0.016)
        assert calls == ["go"]

    def test_step_updates_scene_timeline(self) -> None:
        scene = Scene(name="anim")
        tween = Tween(0.0, 10.0, 1.0, ease=ease_linear)
        scene.timeline.add(tween)
        engine = Engine()
        engine.use_scene(scene)
        engine.step(0.5)
        assert tween.value == pytest.approx(5.0)

    def test_quit_event_stops_engine(self) -> None:
        engine = Engine()
        engine.running = True
        engine.post_event(Event(QUIT))
        engine.step(0.016)
        assert engine.running is False


class TestRunLoop:
    def test_quit_stops_run_loop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("windfall.engine.Live", FakeLive)
        monkeypatch.setattr("windfall.engine.RawTerminal", FakeTerminal)
        engine = Engine(input_reader=InputReader(read_char=_scripted(["\x03"])))
        engine.use_scene(Scene(name="demo"))
        engine.run(fps=200)
        assert engine.running is False

    def test_run_typing_reaches_focused_text_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("windfall.engine.Live", FakeLive)
        monkeypatch.setattr("windfall.engine.RawTerminal", FakeTerminal)
        field = TextInput(value="")
        field.focus(True)
        engine = Engine(input_reader=InputReader(read_char=_scripted(["z", "\x03"])))
        engine.use_scene(Scene(name="chat", root=field))
        engine.run(fps=200)
        assert field.value == "z"

    def test_run_restores_the_previous_winch_handler(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("windfall.engine.Live", FakeLive)
        monkeypatch.setattr("windfall.engine.RawTerminal", FakeTerminal)
        installed: list = []
        monkeypatch.setattr("windfall.engine.signal.signal", lambda sig, handler: installed.append(handler))

        def host_handler(_signum, _frame) -> None:
            pass

        monkeypatch.setattr(
            "windfall.engine.signal.getsignal", lambda _sig: host_handler
        )
        engine = Engine(input_reader=InputReader(read_char=_scripted(["\x03"])))
        engine.use_scene(Scene(name="demo"))
        engine.run(fps=200)
        # Ours went in, and the host's handler went back out.
        assert len(installed) == 2
        assert installed[0] is not host_handler
        assert installed[1] is host_handler

    def test_pending_resize_exists_before_run(self) -> None:
        """The SIGWINCH callback may fire before run() re-initialises the slot."""
        assert Engine()._pending_resize is None


class TestResizeEvent:
    """A terminal resize must reach the scene as a RESIZE event.

    RESIZE was exported in the event vocabulary but never produced, so a
    scene had no way to observe a resize except by polling size().
    """

    def test_resize_is_announced_to_the_scene(self) -> None:
        seen: list[Event] = []
        engine = Engine()
        engine.use_scene(Scene(name="demo", root=_Recorder(seen)))
        engine._pending_resize = (100, 40)
        engine.step(0.016)
        assert [event.kind for event in seen] == [RESIZE]
        assert seen[0].data == {"width": 100, "height": 40}

    def test_resize_updates_the_compositor(self) -> None:
        engine = Engine()
        engine._pending_resize = (100, 40)
        engine.step(0.016)
        assert engine.compositor.size() == Vec2(100, 40)

    def test_resize_is_applied_once_and_cleared(self) -> None:
        seen: list[Event] = []
        engine = Engine()
        engine.use_scene(Scene(name="demo", root=_Recorder(seen)))
        engine._pending_resize = (100, 40)
        engine.step(0.016)
        assert engine._pending_resize is None
        engine.step(0.016)
        assert [event.kind for event in seen] == [RESIZE]

    def test_nothing_announced_without_a_pending_resize(self) -> None:
        seen: list[Event] = []
        engine = Engine()
        engine.use_scene(Scene(name="demo", root=_Recorder(seen)))
        engine.step(0.016)
        assert seen == []


class TestEngineFactories:
    def test_make_header_assembles_widget_from_primitives(self) -> None:
        engine = Engine()
        header = engine.make_header("hi", border="red", fg="green")
        assert isinstance(header, Header)
        assert header.size() == Header("hi").size()

    def test_make_footer_assembles_widget_from_primitives(self) -> None:
        engine = Engine()
        footer = engine.make_footer("bye", border="red", fg="green")
        assert isinstance(footer, Footer)
        assert footer.size() == Footer("bye").size()

    def test_make_widget_builds_each_kind(self) -> None:
        engine = Engine()
        assert isinstance(engine.make_widget("Label"), Label)
        assert isinstance(engine.make_widget("Button"), Button)
        assert isinstance(engine.make_widget("TextInput"), TextInput)
        assert isinstance(engine.make_widget("ListView"), ListView)
        assert isinstance(engine.make_widget("Divider"), Divider)
        assert isinstance(engine.make_widget("Nope"), Label)  # unknown kinds fall back

    def test_make_widget_applies_id_and_text(self) -> None:
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
        assert engine.make_widget("Button", id="b", text="").size() == Button("New button").size()
        assert engine.make_widget("TextInput", id="t", text="").value == "New input"
        assert engine.make_widget("ListView", id="options").id == "options"
        assert engine.make_widget("Nope", id="x", text="hey").size() == Label("hey").size()