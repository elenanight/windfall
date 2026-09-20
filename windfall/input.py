"""Keyboard input: raw reads off a scriptable source plus token -> Event maps."""

from __future__ import annotations

import os
import select
import sys
import threading
import time
from collections import deque

import readchar

from windfall.events import ACTIVATE, CANCEL, KEY, MOVE, QUIT, Event

_ESC = "\x1b"
_ESC_TIMEOUT = 0.05
_MAX_ESC = 6


def _read_byte(fd: int) -> str:
    data = os.read(fd, 1)
    if not data:
        raise EOFError
    return data.decode("latin-1")


def _read_token(fd: int) -> str:
    """Read one key token, assembling escape sequences into a single token.

    A lone ESC is returned after a short grace period so that ESC itself can
    still be mapped (e.g. to CANCEL) without blocking forever on a second byte.
    """
    first = _read_byte(fd)
    if first != _ESC:
        return first
    token = first
    while len(token) < _MAX_ESC:
        ready, _, _ = select.select([fd], [], [], _ESC_TIMEOUT)
        if not ready:
            return token
        token += _read_byte(fd)
    return token


def _read_char() -> str:
    return _read_token(sys.stdin.fileno())


class Keymap:
    """Maps raw key tokens to ``EventKind``s.

    Unbound tokens fall back to a ``KEY`` event carrying the raw token, so
    every keypress becomes an ``Event``.
    """

    def __init__(self, defaults: bool = True) -> None:
        self._bindings: dict[str, tuple[str, dict]] = {}
        if defaults:
            self.bind_defaults()

    def bind(self, token: str, kind: str, data: dict | None = None) -> None:
        self._bindings[token] = (kind, data or {})

    def unbind(self, token: str) -> None:
        self._bindings.pop(token, None)

    def map(self, token: str) -> Event:
        bound = self._bindings.get(token)
        if bound is None:
            return Event(KEY, {"key": token})
        return Event(bound[0], dict(bound[1]))

    def bind_defaults(self) -> None:
        self._bindings.clear()
        self.bind(readchar.key.CTRL_C, QUIT)
        self.bind(readchar.key.ESC, CANCEL)
        self.bind(readchar.key.UP, MOVE, {"direction": "up"})
        self.bind(readchar.key.DOWN, MOVE, {"direction": "down"})
        self.bind(readchar.key.LEFT, MOVE, {"direction": "left"})
        self.bind(readchar.key.RIGHT, MOVE, {"direction": "right"})
        self.bind(readchar.key.ENTER, ACTIVATE)
        self.bind("\r", ACTIVATE)
        self.bind("\n", ACTIVATE)


class InputReader:
    """Non-blocking key source.

    ``read_char`` is a callable returning one raw token (or raising ``EOFError``
    on end of input). A daemon thread feeds a queue, and :meth:`poll` drains it
    without blocking. Defaults to an escape-assembling reader over stdin.
    """

    def __init__(self, read_char=_read_char) -> None:
        self._read_char = read_char
        self._queue: deque[str] = deque()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def open(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._pump, name="windfall-input", daemon=True)
        self._thread.start()

    def close(self, timeout: float = 0.5) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def poll(self, timeout: float = 0.0) -> str | None:
        if self._queue:
            return self._queue.popleft()
        if timeout > 0.0:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if self._queue:
                    return self._queue.popleft()
                time.sleep(0.001)
        return None

    def _pump(self) -> None:
        try:
            while not self._stop.is_set():
                self._pump_once()
        except EOFError:
            pass

    def _pump_once(self) -> None:
        token = self._read_char()
        if token in ("", None):
            raise EOFError
        self._queue.append(token)