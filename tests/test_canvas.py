"""Tests for the canvas cell surface."""

from __future__ import annotations

from windfall.canvas import Canvas
from windfall.style import Style


def test_write_and_text_roundtrip() -> None:
    canvas = Canvas(5, 2)
    canvas.write("hi", 1, 0)
    assert canvas.text() == [" hi  ", "     "]


def test_write_clips_out_of_bounds() -> None:
    canvas = Canvas(3, 1)
    canvas.write("abcdef", 0, 0)
    assert canvas.text() == ["abc"]


def test_write_ignores_offscreen_row() -> None:
    canvas = Canvas(3, 1)
    canvas.write("abc", 0, 5)
    assert canvas.text() == ["   "]


def test_write_styles_cells() -> None:
    canvas = Canvas(3, 1)
    style = Style(fg="red")
    canvas.write("abc", 0, 0, style)
    assert canvas.to_rich().spans  # at least one styled span
    assert canvas.to_rich().plain == "abc"


def test_fill_region() -> None:
    canvas = Canvas(4, 3)
    canvas.fill(1, 1, 2, 2, "x")
    assert canvas.text() == ["    ", " xx ", " xx "]


def test_resize_resets_contents() -> None:
    canvas = Canvas(4, 2)
    canvas.write("abc", 0, 0)
    canvas.resize(2, 2)
    assert canvas.text() == ["  ", "  "]


def test_to_rich_preserves_plain_text() -> None:
    canvas = Canvas(2, 2)
    canvas.write("a", 0, 0)
    canvas.write("b", 1, 1)
    assert canvas.to_rich().plain == "a \n b"


def test_default_fill_is_space() -> None:
    canvas = Canvas(2, 1)
    assert canvas.text() == ["  "]