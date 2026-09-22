"""Shared test utilities: rendering, event synthesis, and tree walking."""

from __future__ import annotations

from windfall.canvas import Canvas
from windfall.component import Component
from windfall.events import KEY, MOVE, Event
from windfall.geom import Rect
from windfall.layout import Column
from windfall.scene import Scene, focusables
from windfall.widgets import Button


def render(widget, width: int | None = None, height: int | None = None) -> list[str]:
    """Draw a widget onto a fresh canvas and return its text grid."""
    size = widget.size()
    width = width if width is not None else size.x
    height = height if height is not None else size.y
    canvas = Canvas(width, height)
    widget.draw(canvas, Rect(0, 0, width, height))
    return canvas.text()


def key(char: str) -> Event:
    return Event(KEY, {"key": char})


def move(direction: str) -> Event:
    return Event(MOVE, {"direction": direction})


def find_all(node, kind: type) -> list:
    """Walk a component tree the way event delivery does (children/box/child)."""
    found = [node] if isinstance(node, kind) else []
    for attr in ("children", "_box", "_child"):
        value = getattr(node, attr, None)
        if value is None:
            continue
        for kid in value if isinstance(value, list) else [value]:
            found.extend(find_all(kid, kind))
    return found


def editor_buttons(editor: Component) -> list[Button]:
    return [w for w in focusables(editor) if isinstance(w, Button)]


def hosted(editor: Component) -> Scene:
    return Scene(root=Column().add(editor))