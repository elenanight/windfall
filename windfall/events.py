"""Event vocabulary, the event value object, and a small FIFO queue."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

KEY = "key"
MOVE = "move"
ACTIVATE = "activate"
QUIT = "quit"
CANCEL = "cancel"
FOCUS = "focus"
BLUR = "blur"
TICK = "tick"
RESIZE = "resize"


@dataclass
class Event:
    """A single unit of input or engine activity, with an optional payload.

    ``kind`` is a string so custom kinds (e.g. ``"score_changed"``) need no
    registry changes; the module constants cover the built-in vocabulary.
    """

    kind: str
    data: dict = field(default_factory=dict)


class EventQueue:
    """Thread-unsafe FIFO of events; passing one queue around is expected."""

    def __init__(self) -> None:
        self._events: deque[Event] = deque()

    def post(self, event: Event) -> None:
        self._events.append(event)

    def poll(self) -> Event | None:
        return self._events.popleft() if self._events else None

    def drain(self) -> list[Event]:
        events = list(self._events)
        self._events.clear()
        return events

    def clear(self) -> None:
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)