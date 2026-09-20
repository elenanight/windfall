"""An animation demo: a ball bouncing across a track on a scene timeline.

A custom ``Ball`` component exposes a plain ``x`` attribute that ``Animation``
rewrites each tick through the scene's own ``Timeline``; when the tween
completes the scene queues the reverse trip. Run with:
`uv run python examples/bouncer.py`.
"""

from __future__ import annotations

from windfall import Animation, Component, Engine, Rect, Scene, Stack, Style, Text, Vec2
from windfall.anim import ease_in_out_cubic


class Ball(Component):
    """A one-dimensional ball whose ``x`` floats along a track."""

    def __init__(self, width: int) -> None:
        super().__init__()
        self.x = 0.0
        self._width = width

    def size(self) -> Vec2:
        return Vec2(self._width, 1)

    def draw(self, canvas, rect: Rect) -> None:
        column = max(0, min(rect.width - 1, round(self.x)))
        canvas.write("●", rect.x + column, rect.y, Style(fg="yellow"))


class BouncerScene(Scene):
    """A scene that bounces its ball right, then left, forever."""

    def __init__(self, width: int = 24, duration: float = 1.0) -> None:
        super().__init__(name="bouncer")
        self.ball = Ball(width)
        self._first = 0.0
        self._last = float(width - 1)
        self._duration = duration
        self._forward = True
        self.root = Stack().add(Text("·" * width)).add(self.ball)
        self.timeline.add(Animation(self.ball, "x", self._first, self._last, duration, ease=ease_in_out_cubic))

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.timeline.done:
            self.timeline.clear()
            self._forward = not self._forward
            start, end = (self._first, self._last) if self._forward else (self._last, self._first)
            self.timeline.add(Animation(self.ball, "x", start, end, self._duration, ease=ease_in_out_cubic))


def build(width: int = 24) -> Scene:
    return BouncerScene(width)


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build())
    engine.run()