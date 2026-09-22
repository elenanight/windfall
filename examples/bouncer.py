"""A bounce demo: a ball arcs between the floor and the ceiling forever.

A custom ``Ball`` exposes float ``x``/``y`` that a ``Sequence`` of ``Motion``
steps (up, then down) rewrites on the scene's deterministic clock; when the
sequence completes the scene re-adds it, so the ball bounces indefinitely.
Run with: `uv run python examples/bouncer.py`.
"""

from __future__ import annotations

from windfall import Column, Component, Engine, Label, Rect, Scene, Stack, Style, Text, Vec2
from windfall.anim import Motion, Sequence, ease_in_out_cubic

_WIDTH = 24
_HEIGHT = 6


class Ball(Component):
    """A one-cell ball with float ``x``/``y`` on a multi-row grid."""

    def __init__(self, width: int, height: int) -> None:
        super().__init__()
        self.x = float(width // 2)
        self.y = float(height - 1)
        self._width = width
        self._height = height

    def size(self) -> Vec2:
        return Vec2(self._width, self._height)

    def draw(self, canvas, rect: Rect) -> None:
        column = max(0, min(rect.width - 1, round(self.x)))
        row = max(0, min(rect.height - 1, round(self.y)))
        canvas.write("●", rect.x + column, rect.y + row, Style(fg="yellow"))


class BouncerScene(Scene):
    """Bounces a ball between the floor and the ceiling forever."""

    def __init__(self, width: int = _WIDTH, height: int = _HEIGHT) -> None:
        super().__init__(name="bouncer")
        self.width = width
        self.height = height
        self.ball = Ball(width, height)
        grid = "\n".join("·" * width for _ in range(height))
        root = Column()
        root.add(Label("bouncer", align="center"))
        root.add(Stack().add(Text(grid)).add(self.ball))
        root.add(Label("bounces forever · Ctrl+C quits"))
        self.root = root
        self.timeline.add(self._bounce())

    def _bounce(self) -> Sequence:
        floor = Vec2(self.width // 2, self.height - 1)
        ceiling = Vec2(self.width // 2, 0)

        def leg(start: Vec2, end: Vec2):
            return lambda: Motion(self.ball, start, end, 1.0, ease=ease_in_out_cubic)

        return Sequence(leg(floor, ceiling), leg(ceiling, floor))

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.timeline.done:
            self.timeline.clear()
            self.timeline.add(self._bounce())


def build(width: int = _WIDTH, height: int = _HEIGHT) -> Scene:
    return BouncerScene(width, height)


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build())
    engine.run()