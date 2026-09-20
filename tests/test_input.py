"""Tests for key mapping and the non-blocking input thread."""

from __future__ import annotations

import os
import time

import pytest
import readchar

from windfall.events import ACTIVATE, CANCEL, KEY, MOVE, QUIT, Event
from windfall.input import InputReader, Keymap, _read_token


def test_keymap_bind_and_map() -> None:
    keymap = Keymap(defaults=False)
    keymap.bind("w", MOVE, {"direction": "up"})
    event = keymap.map("w")
    assert event.kind == MOVE
    assert event.data == {"direction": "up"}


def test_keymap_unbound_falls_back_to_key() -> None:
    keymap = Keymap(defaults=False)
    event = keymap.map("q")
    assert event.kind == KEY
    assert event.data == {"key": "q"}


def test_keymap_unbind() -> None:
    keymap = Keymap(defaults=False)
    keymap.bind("w", QUIT)
    keymap.unbind("w")
    assert keymap.map("w").kind == KEY


def test_keymap_defaults_bind_arrow_keys() -> None:
    keymap = Keymap()
    assert keymap.map(readchar.key.UP).kind == MOVE
    assert keymap.map(readchar.key.DOWN).data["direction"] == "down"
    assert keymap.map(readchar.key.CTRL_C).kind == QUIT


def test_keymap_defaults_bind_both_enter_tokens() -> None:
    keymap = Keymap()
    assert keymap.map("\r").kind == ACTIVATE
    assert keymap.map("\n").kind == ACTIVATE
    assert keymap.map(readchar.key.ESC).kind == CANCEL
    assert keymap.map(readchar.key.ENTER).kind == ACTIVATE


def keymap_does_not_share_binding_state_between_instances() -> None:
    first = Keymap(defaults=False)
    second = Keymap(defaults=False)
    first.bind("x", QUIT)
    assert second.map("x").kind == KEY


def _scripted(tokens: list[str]):
    remaining = list(tokens)

    def read() -> str:
        if remaining:
            return remaining.pop(0)
        raise EOFError

    return read


def test_pump_once_pushes_token() -> None:
    reader = InputReader(read_char=_scripted(["hello"]))
    reader._pump_once()
    assert reader.poll() == "hello"
    assert reader.poll() is None


def test_pump_once_stops_on_eof() -> None:
    reader = InputReader(read_char=_scripted([]))
    with pytest.raises(EOFError):
        reader._pump_once()


def test_poll_empty_returns_none() -> None:
    reader = InputReader(read_char=_scripted([]))
    assert reader.poll() is None
    assert reader.poll(timeout=0.01) is None


def test_poll_waits_for_token_within_timeout() -> None:
    reader = InputReader(read_char=_scripted(["a"]))
    reader.open()
    try:
        assert reader.poll(timeout=2.0) == "a"
    finally:
        reader.close()


def test_threaded_reader_delivers_tokens() -> None:
    reader = InputReader(read_char=_scripted(["a", "\x1b[B"]))
    reader.open()
    try:
        got: list[str] = []
        deadline = time.monotonic() + 2.0
        while len(got) < 2 and time.monotonic() < deadline:
            token = reader.poll(timeout=0.01)
            if token is not None:
                got.append(token)
        assert got == ["a", "\x1b[B"]
    finally:
        reader.close()


def test_close_is_idempotent() -> None:
    reader = InputReader(read_char=_scripted([]))
    reader.open()
    reader.close()
    reader.close()


def test_map_returns_event_instances() -> None:
    keymap = Keymap(defaults=False)
    assert isinstance(keymap.map("z"), Event)


def test_read_token_assembles_escape_sequence() -> None:
    read_fd, write_fd = os.pipe()
    try:
        os.write(write_fd, b"\x1b[B")
        assert _read_token(read_fd) == readchar.key.DOWN
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_read_token_returns_plain_char() -> None:
    read_fd, write_fd = os.pipe()
    try:
        os.write(write_fd, b"q")
        assert _read_token(read_fd) == "q"
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_read_token_returns_lone_esc_after_grace_period() -> None:
    read_fd, write_fd = os.pipe()
    try:
        os.write(write_fd, b"\x1b")
        assert _read_token(read_fd) == "\x1b"
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_read_token_raises_on_eof() -> None:
    read_fd, write_fd = os.pipe()
    try:
        os.close(write_fd)
        with pytest.raises(EOFError):
            _read_token(read_fd)
    finally:
        os.close(read_fd)