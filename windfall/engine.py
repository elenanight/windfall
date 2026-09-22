"""Engine: the interactive loop driving input, scenes, updates, and rendering."""

from __future__ import annotations

import shutil
import signal
import time

from rich.live import Live

from windfall.compositor import Compositor
from windfall.events import QUIT, Event, EventQueue
from windfall.input import InputReader, Keymap
from windfall.primitives import Divider
from windfall.scene import Frame, FrameStack
from windfall.terminal import RawTerminal
from windfall.widgets import Button, Footer, Header, Label, ListView, TextInput


class Engine:
    """Owns input, a frame stack, and a compositor; steps the game loop.

    ``run`` blocks in an interactive loop that drains input, dispatches events,
    ticks the current scene, and redraws through ``rich.Live``. ``step`` drives
    the same dispatch-and-update work headless, one deterministic tick at a
    time, with events posted via :meth:`post_event`.
    """

    def __init__(
        self,
        *,
        keymap: Keymap | None = None,
        input_reader: InputReader | None = None,
        compositor: Compositor | None = None,
    ) -> None:
        self.frames = FrameStack()
        self.keymap = keymap if keymap is not None else Keymap()
        self.input = input_reader if input_reader is not None else InputReader()
        self.compositor = compositor if compositor is not None else Compositor()
        self.running = False
        self._queue = EventQueue()

    def use_scene(self, scene) -> None:
        self.frames.push(Frame(scene))

    def make_header(self, text: str = "", *, border: str = "cyan", fg: str = "white") -> Header:
        """Assemble a header bar from primitives with the given colors."""
        return Header(text, border=border, fg=fg)

    def make_footer(self, text: str = "", *, border: str = "cyan", fg: str = "white") -> Footer:
        """Assemble a footer bar from primitives with the given colors."""
        return Footer(text, border=border, fg=fg)

    def make_widget(self, kind: str = "Label", *, id: str = "", text: str = ""):
        """Assemble a content widget of the given kind with a name and text.

        ``id`` names the widget so it can be referenced and relabeled in
        config; ``text`` seeds the widget's content (label, button, or
        input value) and is ignored by kinds without a single text field.
        Unknown kinds fall back to a ``Label`` so a corrupt config can
        never break app boot.
        """
        if kind == "Button":
            widget = Button(text or "New button")
        elif kind == "TextInput":
            widget = TextInput(text or "New input")
        elif kind == "ListView":
            widget = ListView(items=["Option 1", "Option 2"])
        elif kind == "Divider":
            widget = Divider()
        else:
            widget = Label(text or "New label", align="center")
        widget.id = id
        return widget

    def post_event(self, event: Event) -> None:
        self._queue.post(event)

    def stop(self) -> None:
        self.running = False

    def step(self, dt: float = 0.016) -> None:
        while True:
            event = self._queue.poll()
            if event is None:
                break
            if event.kind == QUIT:
                self.stop()
                return
            scene = self.frames.current.scene if self.frames.current else None
            if scene is not None:
                scene.handle(event)
        scene = self.frames.current.scene if self.frames.current else None
        if scene is not None:
            scene.update(dt)

    def run(self, fps: int = 30) -> None:
        self.running = True
        try:
            with RawTerminal():
                self.input.open()
                size = shutil.get_terminal_size((80, 24))
                self.compositor.resize(size.columns, size.lines)
                self._pending_resize = None

                def _on_winch(_signum, _frame) -> None:
                    size = shutil.get_terminal_size((80, 24))
                    self._pending_resize = (size.columns, size.lines)

                try:
                    signal.signal(signal.SIGWINCH, _on_winch)
                except (ValueError, AttributeError):
                    pass
                with Live(auto_refresh=False, screen=True) as live:
                    last = time.perf_counter()
                    while self.running:
                        now = time.perf_counter()
                        dt = min(max(now - last, 0.0), 0.25)
                        last = now
                        while True:
                            token = self.input.poll(timeout=0.0)
                            if token is None:
                                break
                            self.post_event(self.keymap.map(token))
                        self.step(dt)
                        if self._pending_resize is not None:
                            self.compositor.resize(*self._pending_resize)
                            self._pending_resize = None
                        scene = self.frames.current.scene if self.frames.current else None
                        if scene is not None:
                            live.update(self.compositor.render(scene))
                        live.refresh()
                        time.sleep(max(0.0, 1.0 / fps - (time.perf_counter() - now)))
        finally:
            self.input.close()
            self.running = False