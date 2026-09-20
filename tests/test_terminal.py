"""Tests for the raw terminal context manager."""

from __future__ import annotations

import os

from windfall.terminal import RawTerminal


def test_raw_terminal_is_a_noop_on_non_tty() -> None:
    read_fd, write_fd = os.pipe()
    try:
        with RawTerminal(fd=read_fd):
            pass
        with RawTerminal(fd=read_fd):
            raise RuntimeError("leak probe")
    except RuntimeError:
        pass
    finally:
        os.close(read_fd)
        os.close(write_fd)