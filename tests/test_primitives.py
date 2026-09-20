"""Tests for primitives: text, spacer, divider, border, and box."""

from __future__ import annotations

import pytest

from windfall.canvas import Canvas
from windfall.geom import Rect, Vec2
from windfall.primitives import Border, Box, Divider, Spacer, Text
from windfall.style import Style


def test_text_size_single_line() -> None:
    assert Text("hello").size() == Vec2(5, 1)


def test_text_size_multiline() -> None:
    assert Text("ab\nc").size() == Vec2(2, 2)


def test_text_draw_left_aligned_and_clipped() -> None:
    canvas = Canvas(6, 2)
    Text("hello").draw(canvas, Rect(1, 0, 4, 2))
    assert canvas.text() == [" hell ", "      "]


def test_text_draw_center_and_right() -> None:
    canvas = Canvas(10, 1)
    Text("abc", align="center").draw(canvas, Rect(0, 0, 10, 1))
    assert canvas.text() == ["   abc    "]
    canvas = Canvas(10, 1)
    Text("abc", align="right").draw(canvas, Rect(0, 0, 10, 1))
    assert canvas.text() == ["       abc"]


def test_text_rejects_unknown_align() -> None:
    with pytest.raises(ValueError):
        Text("x", align="diagonal")


def test_spacer_size_and_noop_draw() -> None:
    spacer = Spacer(3, 2)
    assert spacer.size() == Vec2(3, 2)
    canvas = Canvas(4, 2)
    spacer.draw(canvas, Rect(0, 0, 4, 2))
    assert canvas.text() == ["    ", "    "]


def test_divider_size_and_draw() -> None:
    divider = Divider()
    assert divider.size() == Vec2(0, 1)
    canvas = Canvas(5, 1)
    divider.draw(canvas, Rect(0, 0, 5, 1))
    assert canvas.text() == ["─────"]


def test_border_size_is_zero() -> None:
    assert Border().size() == Vec2(0, 0)


def test_border_draw_corners_and_edges() -> None:
    canvas = Canvas(7, 5)
    Border().draw(canvas, Rect(1, 1, 5, 3))
    assert canvas.text() == [
        "       ",
        " ┌───┐ ",
        " │   │ ",
        " └───┘ ",
        "       ",
    ]


def test_border_draw_noop_for_small_rects() -> None:
    canvas = Canvas(2, 2)
    Border().draw(canvas, Rect(0, 0, 1, 1))
    assert canvas.text() == ["  ", "  "]


def test_box_size_includes_border_and_padding() -> None:
    assert Box(Text("hi")).size() == Vec2(6, 5)
    assert Box(Text("hi"), padding=0).size() == Vec2(4, 3)


def test_box_draw_frames_and_pads_child() -> None:
    canvas = Canvas(6, 5)
    Box(Text("hi", align="center")).draw(canvas, Rect(0, 0, 6, 5))
    assert canvas.text() == [
        "┌────┐",
        "│    │",
        "│ hi │",
        "│    │",
        "└────┘",
    ]


def test_box_draw_background_fill() -> None:
    style = Style(bg="blue")
    canvas = Canvas(4, 3)
    Box(Spacer(0, 0), style=style, padding=0).draw(canvas, Rect(0, 0, 4, 3))
    assert canvas.text() == [
        "┌──┐",
        "│  │",
        "└──┘",
    ]