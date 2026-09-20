"""Compositor: lays a scene out onto a canvas and produces rich renderables."""

from __future__ import annotations

from rich.text import Text as _RichText

from windfall.canvas import Canvas
from windfall.geom import Rect


class Compositor:
    """Renders the current scene onto a sized canvas for the live display.

    :meth:`render` produces one rich renderable for ``rich.Live``; :meth:`text`
    exposes the same frame as a plain-text grid for headless checks.
    """

    def __init__(self, width: int = 80, height: int = 24) -> None:
        self._width = width
        self._height = height
        self._canvas = Canvas(width, height)

    def resize(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._canvas.resize(width, height)

    def render(self, scene) -> _RichText:
        self._canvas.fill(0, 0, self._width, self._height)
        if scene is not None:
            scene.draw(self._canvas, Rect(0, 0, self._width, self._height))
        return self._canvas.to_rich()

    def text(self, scene) -> list[str]:
        self.render(scene)
        return self._canvas.text()