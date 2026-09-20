"""Reusable interactive widgets assembled from primitives."""

from __future__ import annotations

from windfall.component import Component
from windfall.events import ACTIVATE, KEY, MOVE, Event
from windfall.geom import Rect, Vec2
from windfall.primitives import Border, Box, Text
from windfall.style import Style

_HIGHLIGHT = Style(bg="bright_blue")
_BLOCK = "\u25ae"


class Label(Component):
    """Non-interactive text; the palette-down equivalent of a ``Text``."""

    def __init__(self, text: str, style: Style | None = None, align: str = "left") -> None:
        super().__init__()
        self._text = Text(text, style=style, align=align)

    def size(self) -> Vec2:
        return self._text.size()

    def draw(self, canvas, rect: Rect) -> None:
        self._text.draw(canvas, rect)

    def set_text(self, text: str) -> None:
        self._text.set_text(text)


class Button(Component):
    """A focusable, activating, bordered button."""

    def __init__(
        self,
        label: str,
        on_activate=None,
        style: Style | None = None,
        border_style: Style | None = None,
        padding: int = 1,
    ) -> None:
        super().__init__()
        self.focusable = True
        self._label = Text(label, align="center", style=style)
        self._border = Border(border_style)
        self._style = style
        self._padding = padding
        self.on_activate = on_activate

    def size(self) -> Vec2:
        inner = self._label.size()
        ring = 1 + self._padding
        return Vec2(inner.x + 2 * ring, inner.y + 2 * ring)

    def draw(self, canvas, rect: Rect) -> None:
        inner = rect.inset(1 + self._padding)
        if self.focused and inner.width > 0 and inner.height > 0:
            canvas.fill(rect.x, rect.y, rect.width, rect.height, " ", _HIGHLIGHT)
        if inner.width > 0 and inner.height > 0:
            self._label.draw(canvas, inner)
        self._border.draw(canvas, rect)

    def handle(self, event: Event) -> bool:
        if event.kind != ACTIVATE or not self.focused:
            return False
        if self.on_activate is not None:
            self.on_activate()
        return True

    def set_label(self, label: str) -> None:
        self._label = Text(label, align="center", style=self._style)


class Panel(Component):
    """A titled box that frames a single child component."""

    def __init__(
        self,
        child: Component,
        title: str = "",
        style: Style | None = None,
        border_style: Style | None = None,
        padding: int = 1,
    ) -> None:
        super().__init__()
        self._box = Box(child, style=style, border_style=border_style, padding=padding)
        self._title = Text(title)

    def size(self) -> Vec2:
        return self._box.size()

    def draw(self, canvas, rect: Rect) -> None:
        self._box.draw(canvas, rect)
        if self._title.size().x > 0:
            self._title.draw(canvas, Rect(rect.x + 2, rect.y, max(0, rect.width - 2), 1))

    def set_title(self, title: str) -> None:
        self._title.set_text(title)


class TextInput(Component):
    """A single-line, focusable text field with a block cursor."""

    def __init__(
        self,
        value: str = "",
        on_submit=None,
        style: Style | None = None,
        border_style: Style | None = None,
    ) -> None:
        super().__init__()
        self.focusable = True
        self._text = value
        self._cursor = len(value)
        self._style = style
        self._border = Border(border_style)
        self.on_submit = on_submit

    def size(self) -> Vec2:
        return Vec2(len(self._text) + 2, 3)

    def draw(self, canvas, rect: Rect) -> None:
        self._border.draw(canvas, rect)
        inner = rect.inset(1)
        if inner.width <= 0 or inner.height <= 0:
            return
        if self.focused:
            canvas.fill(inner.x, inner.y, inner.width, inner.height, " ", _HIGHLIGHT)
        canvas.write(self._text[: inner.width], inner.x, inner.y, self._style)
        if self.focused and inner.width > 0:
            cursor_column = min(self._cursor, inner.width - 1)
            canvas.write(_BLOCK, inner.x + cursor_column, inner.y, self._style)

    def handle(self, event: Event) -> bool:
        if not self.focused:
            return False
        if event.kind == KEY:
            key = event.data.get("key", "")
            if key in ("\x7f", "\b") and self._cursor > 0:
                self._text = self._text[: self._cursor - 1] + self._text[self._cursor :]
                self._cursor -= 1
                return True
            if len(key) == 1 and key.isprintable():
                self._text = self._text[: self._cursor] + key + self._text[self._cursor :]
                self._cursor += 1
                return True
            return False
        if event.kind == MOVE:
            direction = event.data.get("direction")
            if direction == "left":
                self._cursor = max(0, self._cursor - 1)
                return True
            if direction == "right":
                self._cursor = min(len(self._text), self._cursor + 1)
                return True
            return False
        if event.kind == ACTIVATE:
            if self.on_submit is not None:
                self.on_submit(self._text)
            return True
        return False

    @property
    def value(self) -> str:
        return self._text


class ListView(Component):
    """A focusable list of options with keyboard navigation."""

    def __init__(self, items=None, on_select=None, style: Style | None = None) -> None:
        super().__init__()
        self.focusable = True
        self._items = list(items or [])
        self._selected = 0
        self._style = style
        self.on_select = on_select

    def size(self) -> Vec2:
        if not self._items:
            return Vec2(0, 0)
        width = max(len(item) for item in self._items) + 2
        return Vec2(width, len(self._items))

    def draw(self, canvas, rect: Rect) -> None:
        if not self._items:
            return
        top = min(max(0, self._selected), max(0, len(self._items) - rect.height))
        for row in range(rect.height):
            index = top + row
            if index >= len(self._items):
                break
            y = rect.y + row
            selected = index == self._selected
            row_style = _HIGHLIGHT if selected and self.focused else self._style
            if selected and self.focused:
                canvas.fill(rect.x, y, rect.width, 1, " ", _HIGHLIGHT)
            Text(f"{'▸' if selected else ' '} {self._items[index]}", style=row_style).draw(
                canvas, Rect(rect.x, y, rect.width, 1)
            )

    def handle(self, event: Event) -> bool:
        if not self.focused or not self._items:
            return False
        if event.kind == MOVE:
            direction = event.data.get("direction")
            if direction == "down":
                self._selected = min(len(self._items) - 1, self._selected + 1)
                return True
            if direction == "up":
                self._selected = max(0, self._selected - 1)
                return True
            return False
        if event.kind == ACTIVATE:
            if self.on_select is not None:
                self.on_select(self._items[self._selected], self._selected)
            return True
        return False

    def set_items(self, items: list[str]) -> None:
        self._items = list(items or [])
        self._selected = 0

    @property
    def selection(self) -> int:
        return self._selected