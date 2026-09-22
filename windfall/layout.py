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
        if not isinstance(child, Container):
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
    """Places children left-to-right, each at its natural width.

    With ``fill=True`` the extra width is shared across children so the row
    spans the available rect; the default keeps natural widths for
    developers who do not want their widgets stretched. ``weights`` tunes
    each child's share (``0`` keeps that child at its natural width);
    missing entries default to ``1``.
    """

    def __init__(self, fill: bool = False, weights=None) -> None:
        super().__init__()
        self._fill = fill
        self._weights = list(weights) if weights is not None else []

    def size(self) -> Vec2:
        width = sum(child.size().x for child in self.children)
        height = max((child.size().y for child in self.children), default=0)
        return Vec2(width, height)

    def _weight(self, index: int) -> int:
        if index < len(self._weights):
            return max(0, self._weights[index])
        return 1

    def draw(self, canvas, rect: Rect) -> None:
        if not self._fill or not self.children:
            self._draw_natural(canvas, rect)
            return
        natural = [child.size() for child in self.children]
        extra = max(0, rect.width - sum(size.x for size in natural))
        total = sum(self._weight(index) for index in range(len(self.children)))
        if total <= 0:
            self._draw_natural(canvas, rect)
            return
        shares = []
        for index in range(len(self.children)):
            shares.append(extra * self._weight(index) // total)
        remainder = extra - sum(shares)
        x = rect.x
        for index, child in enumerate(self.children):
            width = natural[index].x + shares[index] + (1 if index < remainder else 0)
            child.draw(canvas, Rect(x, rect.y, width, rect.height))
            x += width

    def _draw_natural(self, canvas, rect: Rect) -> None:
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
    """Positions each child within the available rect at its natural size.

    ``align`` pins children horizontally: ``"left"``, ``"center"`` (the
    default), or ``"right"``. Vertical placement stays centered.
    """

    def __init__(self, align: str = "center") -> None:
        if align not in ("left", "center", "right"):
            raise ValueError(f"align must be one of left/center/right, got {align!r}")
        super().__init__()
        self._align = align

    def size(self) -> Vec2:
        width = max((child.size().x for child in self.children), default=0)
        height = max((child.size().y for child in self.children), default=0)
        return Vec2(width, height)

    def draw(self, canvas, rect: Rect) -> None:
        for child in self.children:
            child_size = child.size()
            if self._align == "left":
                dx = 0
            elif self._align == "right":
                dx = rect.width - child_size.x
            else:
                dx = (rect.width - child_size.x) // 2
            inner = Rect(
                rect.x + max(0, dx),
                rect.y + max(0, (rect.height - child_size.y) // 2),
                child_size.x,
                child_size.y,
            )
            child.draw(canvas, inner)