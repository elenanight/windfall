"""Ownership of the terminal's raw mode while the engine runs."""

from __future__ import annotations

import os
import sys
import termios
import tty


class RawTerminal:
    """Context manager that switches stdin to raw mode and restores it on exit.

    Raw mode disables ``ISIG``, so Ctrl+C arrives as a normal key byte instead
    of a SIGINT that interrupts a read mid-restore. Input is truly raw, but
    output post-processing (``OPOST``/``ONLCR``) is kept on so the renderer's
    ``\\n``-terminated rows translate to CRLF instead of scattering fragments
    across the screen. Because ``__exit__`` restores the saved settings
    regardless of how the block ends, the terminal can never be left in a
    broken state, even if the engine exits through an exception. Non-tty input
    (pipes, captured stdin) is left untouched.
    """

    def __init__(self, fd: int | None = None) -> None:
        self._fd = fd if fd is not None else sys.stdin.fileno()

    def __enter__(self):
        if not os.isatty(self._fd):
            return self
        self._saved = termios.tcgetattr(self._fd)
        tty.setraw(self._fd)
        attrs = termios.tcgetattr(self._fd)
        attrs[1] |= termios.OPOST | termios.ONLCR
        termios.tcsetattr(self._fd, termios.TCSADRAIN, attrs)
        return self

    def __exit__(self, *exc_info) -> bool:
        if os.isatty(self._fd):
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._saved)
        return False