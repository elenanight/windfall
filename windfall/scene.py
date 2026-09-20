"""Scenes, frames, and the frame stack for navigation."""

from __future__ import annotations

from windfall.anim import Timeline
from windfall.events import MOVE, Event
from windfall.geom import Rect, Vec2


def _iter_children(node):
    for child in getattr(node, "children", ()) or ():
        yield child
    box = getattr(node, "_box", None)
    if box is not None:
        yield box
    child = getattr(node, "_child", None)
    if child is not None:
        yield child


def focusables(node):
    """Yield every focusable component in focus order within a subtree."""
    if getattr(node, "focusable", False):
        yield node
    for child in _iter_children(node):
        yield from focusables(child)


class Scene:
    """One view: a component tree plus tick, event, and focus behavior.

    ``root`` is a component/layout, typically a ``Column`` of widgets. The
    scene forwards events and ticks down the tree and cycles keyboard focus
    across focusable widgets when nothing else consumes the arrow keys.
    """

    def __init__(self, name: str = "", root=None) -> None:
        self.name = name
        self.root = root
        self.timeline = Timeline()

    def size(self) -> Vec2:
        return self.root.size() if self.root is not None else Vec2(0, 0)

    def draw(self, canvas, rect: Rect) -> None:
        if self.root is not None:
            self.root.draw(canvas, rect)

    def update(self, dt: float) -> None:
        if self.root is not None:
            self.root.update(dt)
        self.timeline.step(dt)

    def handle(self, event: Event) -> bool:
        if self.root is not None and self.root.handle(event):
            return True
        if event.kind == MOVE:
            direction = event.data.get("direction")
            if direction in ("up", "left"):
                self.focus_next(-1)
                return True
            if direction in ("down", "right"):
                self.focus_next(1)
                return True
        return False

    def focus_next(self, step: int = 1) -> None:
        items = list(focusables(self.root)) if self.root is not None else []
        if not items:
            return
        focused_index = next((i for i, item in enumerate(items) if item.focused), None)
        if focused_index is None:
            items[0].focus(True)
            return
        items[focused_index].focus(False)
        items[(focused_index + step) % len(items)].focus(True)


class Frame:
    """A named slot holding a scene for the frame stack."""

    def __init__(self, scene: Scene, name: str | None = None) -> None:
        self.scene = scene
        self.name = name or scene.name


class FrameStack:
    """LIFO stack of frames; the compositor renders the current one."""

    def __init__(self) -> None:
        self._frames: list[Frame] = []

    def push(self, frame: Frame) -> None:
        self._frames.append(frame)

    def pop(self) -> Frame | None:
        return self._frames.pop() if self._frames else None

    def replace(self, frame: Frame) -> None:
        if self._frames:
            self._frames[-1] = frame
        else:
            self._frames.append(frame)

    @property
    def current(self) -> Frame | None:
        return self._frames[-1] if self._frames else None

    def __len__(self) -> int:
        return len(self._frames)