"""Atomic visual units: text, spacing, dividers, borders, and boxes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from windfall.geom import Rect, Vec2
from windfall.style import Style

_ALIGNS = ("left", "center", "right")


class Primitive(ABC):
    """A drawable that knows its natural size and can render into a rect."""

    @abstractmethod
    def size(self) -> Vec2:
        ...

    @abstractmethod
    def draw(self, canvas, rect: Rect) -> None:
        ...


class Text(Primitive):
    """One or more lines of styled text, optionally aligned within its rect."""

    def __init__(self, text: str, style: Style | None = None, align: str = "left") -> None:
        if align not in _ALIGNS:
            raise ValueError(f"align must be one of {_ALIGNS}, got {align!r}")
        self._lines = text.splitlines() or [""]
        self._style = style
        self._align = align

    def size(self) -> Vec2:
        width = max(len(line) for line in self._lines)
        return Vec2(width, len(self._lines))

    def set_text(self, text: str) -> None:
        self._lines = text.splitlines() or [""]

    def draw(self, canvas, rect: Rect) -> None:
        for index, line in enumerate(self._lines[: rect.height]):
            visible = line[: rect.width]
            spare = max(0, rect.width - len(visible))
            offset = {"left": 0, "center": spare // 2, "right": spare}[self._align]
            canvas.write(visible, rect.x + offset, rect.y + index, self._style)


class Spacer(Primitive):
    """Blank flexible space with an explicit natural size."""

    def __init__(self, width: int = 0, height: int = 0) -> None:
        self._size = Vec2(width, height)

    def size(self) -> Vec2:
        return self._size

    def draw(self, canvas, rect: Rect) -> None:
        return None


class Divider(Primitive):
    """A horizontal rule that fills the top row of its rect."""

    def __init__(self, style: Style | None = None, char: str = "─") -> None:
        self._style = style
        self._char = char

    def size(self) -> Vec2:
        return Vec2(0, 1)

    def draw(self, canvas, rect: Rect) -> None:
        if rect.width <= 0:
            return
        canvas.fill(rect.x, rect.y, rect.width, min(1, rect.height), self._char, self._style)


_CONNECTOR_STATES = {
    "available": "green",
    "unavailable": "red",
    "unlockable": "blue",
    "active": "dark_orange",
}


class Connector(Primitive):
    """A vertical shaft linking stacked boxes, colored by node state.

    States are ``"available"`` (green), ``"unavailable"`` (red),
    ``"unlockable"`` (blue), and ``"active"`` (``"dark_orange"`` — plain
    ``"orange"`` is not a valid terminal color). The shaft centers itself
    within the given rect.
    """

    def __init__(self, state: str = "available", height: int = 1) -> None:
        if state not in _CONNECTOR_STATES:
            raise ValueError(f"state must be one of {sorted(_CONNECTOR_STATES)}, got {state!r}")
        self.state = state
        self._style = Style(fg=_CONNECTOR_STATES[state])
        self._height = max(0, height)

    def size(self) -> Vec2:
        return Vec2(1, self._height)

    def draw(self, canvas, rect: Rect) -> None:
        if rect.width <= 0 or self._height <= 0:
            return
        x = rect.x + rect.width // 2
        bottom = min(rect.y + self._height, rect.y + rect.height)
        for y in range(rect.y, bottom):
            canvas.write("│", x, y, self._style)


class Border(Primitive):
    """A box outline drawn around the edges of a rect."""

    def __init__(self, style: Style | None = None) -> None:
        self._style = style

    def size(self) -> Vec2:
        return Vec2(0, 0)

    def draw(self, canvas, rect: Rect) -> None:
        if rect.width < 2 or rect.height < 2:
            return
        left = rect.x
        right = rect.x + rect.width - 1
        top = rect.y
        bottom = rect.y + rect.height - 1
        canvas.write("┌" + "─" * (rect.width - 2) + "┐", left, top, self._style)
        for y in range(top + 1, bottom):
            canvas.write("│", left, y, self._style)
            canvas.write("│", right, y, self._style)
        canvas.write("└" + "─" * (rect.width - 2) + "┘", left, bottom, self._style)


class Box(Primitive):
    """A bordered frame around a child primitive, with inner padding."""

    def __init__(
        self,
        child: Primitive,
        style: Style | None = None,
        border_style: Style | None = None,
        padding: int = 1,
    ) -> None:
        self._child = child
        self._style = style
        self._padding = padding
        self._border = Border(border_style)

    def size(self) -> Vec2:
        inner = self._child.size()
        ring = 1 + self._padding
        return Vec2(inner.x + 2 * ring, inner.y + 2 * ring)

    def draw(self, canvas, rect: Rect) -> None:
        if rect.width < 1 or rect.height < 1:
            return
        if self._style:
            canvas.fill(rect.x, rect.y, rect.width, rect.height, " ", self._style)
        inner = rect.inset(1 + self._padding)
        if inner.width > 0 and inner.height > 0:
            self._child.draw(canvas, inner)
        self._border.draw(canvas, rect)