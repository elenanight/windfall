"""Interactive primitives: components add focus, event handling, and ticking."""

from __future__ import annotations

from windfall.events import Event
from windfall.primitives import Primitive


class Component(Primitive):
    """A drawable primitive that can also handle events, tick, and take focus.

    ``Components`` are ``Primitives`` (same ``size``/``draw`` contract), so any
    container, box, or layout accepts them unchanged. Subclasses implement
    ``size`` and ``draw``; ``update`` and ``handle`` default to harmless no-ops.
    """

    def __init__(self) -> None:
        self.focused = False
        self.focusable = False

    def update(self, dt: float) -> None:
        return None

    def handle(self, event: Event) -> bool:
        return False

    def focus(self, active: bool = True) -> None:
        self.focused = active