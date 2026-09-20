"""Composite containers that position primitives: rows, columns, stacks, centers."""

from __future__ import annotations

from windfall.events import Event
from windfall.geom import Rect, Vec2
from windfall.primitives import Primitive


def _yield_children(node):
    """Yield every child of a node regardless of how it holds them.

    Containers store a ``children`` list; ``Box`` holds one ``_child``; ``Panel``
    frames its content through a ``_box``. Event dispatch and ticking walk the
    whole tree so widgets nested inside panels and boxes still respond.
    """
    yield from getattr(node, "children", ()) or ()
    box = getattr(node, "_box", None)
    if box is not None:
        yield box
    child = getattr(node, "_child", None)
    if child is not None:
        yield child


class Container:
    """Base for any group of primitives with add/remove/clear bookkeeping.

    ``update`` and ``handle`` forward down the tree so interactive widgets
    nested inside layouts, boxes, and panels receive ticks and events.
    """

    def __init__(self) -> None:
        self.children: list[Primitive] = []

    def add(self, child: Primitive) -> Container:
        self.children.append(child)
        return self

    def remove(self, child: Primitive) -> None:
        self.children.remove(child)

    def clear(self) -> None:
        self.children.clear()

    def update(self, dt: float) -> None:
        _tick(self, dt)

    def handle(self, event: Event) -> bool:
        for child in _yield_children(self):
            handler = getattr(child, "handle", None)
            if handler is not None and handler(event):
                return True
            if _deliver(child, event):
                return True
        return False


def _tick(node, dt: float) -> None:
    """Depth-first ticking so nested widgets update inside panels and boxes."""
    for child in _yield_children(node):
        updater = getattr(child, "update", None)
        if updater is not None:
            updater(dt)
        _tick(child, dt)


def _deliver(node, event: Event) -> bool:
    """Depth-first delivery: let nested handlers consume an event in order."""
    for child in _yield_children(node):
        handler = getattr(child, "handle", None)
        if handler is not None and handler(event):
            return True
        if _deliver(child, event):
            return True
    return False


class Column(Container):
    """Stacks children top-to-bottom, each at its natural height."""

    def size(self) -> Vec2:
        width = max((child.size().x for child in self.children), default=0)
        height = sum(child.size().y for child in self.children)
        return Vec2(width, height)

    def draw(self, canvas, rect: Rect) -> None:
        y = rect.y
        for child in self.children:
            child_size = child.size()
            child_rect = Rect(rect.x, y, rect.width, child_size.y)
            child.draw(canvas, child_rect)
            y += child_size.y


class Row(Container):
    """Places children left-to-right, each at its natural width."""

    def size(self) -> Vec2:
        width = sum(child.size().x for child in self.children)
        height = max((child.size().y for child in self.children), default=0)
        return Vec2(width, height)

    def draw(self, canvas, rect: Rect) -> None:
        x = rect.x
        for child in self.children:
            child_size = child.size()
            child_rect = Rect(x, rect.y, child_size.x, rect.height)
            child.draw(canvas, child_rect)
            x += child_size.x


class Stack(Container):
    """Overlays children in the same rect; later children draw on top."""

    def size(self) -> Vec2:
        width = max((child.size().x for child in self.children), default=0)
        height = max((child.size().y for child in self.children), default=0)
        return Vec2(width, height)

    def draw(self, canvas, rect: Rect) -> None:
        for child in self.children:
            child.draw(canvas, rect)


class Center(Container):
    """Centers each child within the available rect at its natural size."""

    def size(self) -> Vec2:
        width = max((child.size().x for child in self.children), default=0)
        height = max((child.size().y for child in self.children), default=0)
        return Vec2(width, height)

    def draw(self, canvas, rect: Rect) -> None:
        for child in self.children:
            child_size = child.size()
            inner = Rect(
                rect.x + max(0, (rect.width - child_size.x) // 2),
                rect.y + max(0, (rect.height - child_size.y) // 2),
                child_size.x,
                child_size.y,
            )
            child.draw(canvas, inner)