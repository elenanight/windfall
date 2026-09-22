"""An easing and motion showcase: three racers and a squaring orbiter.

Three dots race to the right edge under the three built-in easings, while a
yellow orbiter squares around its board by chaining ``Motion`` steps in a
``Sequence``. Everything runs on the scene's deterministic clock, so the scene
can be stepped headless. Run with: `uv run python examples/animation.py`.
"""

from __future__ import annotations

from itertools import pairwise

from windfall import Column, Component, Engine, Label, Rect, Scene, Spacer, Stack, Style, Text, Vec2
from windfall.anim import Motion, Sequence, ease_in_out_cubic, ease_linear, ease_out_cubic

_TRACK_LABELS = ("ease-out", "linear", "ease-in-out")
_RACER_GLYPHS = ("●", "▲", "■")
_RACER_COLORS = ("green", "blue", "magenta")


class Dot(Component):
    """A single glyph on a grid, drawn from float ``x``/``y`` motion."""

    def __init__(self, width: int, glyph: str, color: str, height: int = 1) -> None:
        super().__init__()
        self.x = 0.0
        self.y = 0.0
        self._width = width
        self._height = height
        self._glyph = glyph
        self._style = Style(fg=color)

    def size(self) -> Vec2:
        return Vec2(self._width, self._height)

    def draw(self, canvas, rect: Rect) -> None:
        column = max(0, min(rect.width - 1, round(self.x)))
        row = max(0, min(rect.height - 1, round(self.y)))
        canvas.write(self._glyph, rect.x + column, rect.y + row, self._style)


def _track(width: int, dot: Dot) -> Stack:
    return Stack().add(Text("·" * width)).add(dot)


class MotionShowcase(Scene):
    """Races three dots with different easings and squares an orbiter around."""

    def __init__(self, width: int = 30) -> None:
        super().__init__(name="animation")
        self.width = width
        self.racers = [Dot(width, glyph, color) for glyph, color in zip(_RACER_GLYPHS, _RACER_COLORS)]
        edge = 6
        self.orbiter = Dot(width, "●", "yellow", height=edge)
        self._eases = (ease_out_cubic, ease_linear, ease_in_out_cubic)
        board = "\n".join("·" * width for _ in range(edge))
        root = Column()
        root.add(Label("windfall animation", align="center"))
        root.add(Spacer())
        for label, racer in zip(_TRACK_LABELS, self.racers):
            root.add(Label(label))
            root.add(_track(width, racer))
        root.add(Spacer())
        root.add(Label("yellow dot squares around its board"))
        root.add(Stack().add(Text(board)).add(self.orbiter))
        root.add(Spacer())
        root.add(Label("Ctrl+C quits"))
        self.root = root
        self.timeline.add(self._orbit())
        for racer, ease in zip(self.racers, self._eases):
            self.timeline.add(Motion(racer, Vec2(0, 0), Vec2(width - 1, 0), 0.9, ease=ease))

    def _orbit(self) -> Sequence:
        edge = self.orbiter._height - 1
        corners = (Vec2(0, 0), Vec2(edge, 0), Vec2(edge, edge), Vec2(0, edge), Vec2(0, 0))

        def leg(start: Vec2, end: Vec2):
            return lambda: Motion(self.orbiter, start, end, 0.4, ease=ease_out_cubic)

        return Sequence(*(leg(start, end) for start, end in pairwise(corners)))

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.timeline.done:
            self.timeline.clear()
            self.timeline.add(self._orbit())


def build(width: int = 30) -> Scene:
    return MotionShowcase(width)


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build())
    engine.run()