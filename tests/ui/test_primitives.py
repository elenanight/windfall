"""Tests for primitives: text, spacer, divider, border, and box."""

from __future__ import annotations

import pytest

from windfall.canvas import Canvas
from windfall.geom import Rect, Vec2
from windfall.primitives import Border, Box, Connector, Divider, Spacer, Text
from windfall.style import Style


class TestText:
    def test_size_single_line(self) -> None:
        assert Text("hello").size() == Vec2(5, 1)

    def test_size_multiline(self) -> None:
        assert Text("ab\nc").size() == Vec2(2, 2)

    def test_draw_left_aligned_and_clipped(self) -> None:
        canvas = Canvas(6, 2)
        Text("hello").draw(canvas, Rect(1, 0, 4, 2))
        assert canvas.text() == [" hell ", "      "]

    def test_draw_center_and_right(self) -> None:
        canvas = Canvas(10, 1)
        Text("abc", align="center").draw(canvas, Rect(0, 0, 10, 1))
        assert canvas.text() == ["   abc    "]
        canvas = Canvas(10, 1)
        Text("abc", align="right").draw(canvas, Rect(0, 0, 10, 1))
        assert canvas.text() == ["       abc"]

    def test_rejects_unknown_align(self) -> None:
        with pytest.raises(ValueError):
            Text("x", align="diagonal")


class TestSpacer:
    def test_size_and_noop_draw(self) -> None:
        spacer = Spacer(3, 2)
        assert spacer.size() == Vec2(3, 2)
        canvas = Canvas(4, 2)
        spacer.draw(canvas, Rect(0, 0, 4, 2))
        assert canvas.text() == ["    ", "    "]


class TestDivider:
    def test_size_and_draw(self) -> None:
        divider = Divider()
        assert divider.size() == Vec2(0, 1)
        canvas = Canvas(5, 1)
        divider.draw(canvas, Rect(0, 0, 5, 1))
        assert canvas.text() == ["─────"]


class TestConnector:
    def test_size_and_centered_shaft(self) -> None:
        assert Connector().size() == Vec2(1, 1)
        assert Connector(height=3).size() == Vec2(1, 3)
        canvas = Canvas(5, 2)
        Connector(height=2).draw(canvas, Rect(0, 0, 5, 2))
        assert canvas.text() == ["  │  ", "  │  "]

    def test_states_map_to_expected_colors(self) -> None:
        assert Connector("available")._style == Style(fg="green")
        assert Connector("unavailable")._style == Style(fg="red")
        assert Connector("unlockable")._style == Style(fg="blue")
        assert Connector("active")._style == Style(fg="dark_orange")

    def test_rejects_unknown_state(self) -> None:
        with pytest.raises(ValueError):
            Connector("purple")

    def test_horizontal_size_and_draw(self) -> None:
        shaft = Connector("available", horizontal=True, width=4)
        assert shaft.size() == Vec2(4, 1)
        canvas = Canvas(6, 3)
        shaft.draw(canvas, Rect(0, 0, 6, 3))
        assert canvas.text() == ["      ", " ──── ", "      "]


class TestBorder:
    def test_size_is_zero(self) -> None:
        assert Border().size() == Vec2(0, 0)

    def test_draw_corners_and_edges(self) -> None:
        canvas = Canvas(7, 5)
        Border().draw(canvas, Rect(1, 1, 5, 3))
        assert canvas.text() == [
            "       ",
            " ┌───┐ ",
            " │   │ ",
            " └───┘ ",
            "       ",
        ]

    def test_draw_noop_for_small_rects(self) -> None:
        canvas = Canvas(2, 2)
        Border().draw(canvas, Rect(0, 0, 1, 1))
        assert canvas.text() == ["  ", "  "]


class TestBox:
    def test_size_includes_border_and_padding(self) -> None:
        assert Box(Text("hi")).size() == Vec2(6, 5)
        assert Box(Text("hi"), padding=0).size() == Vec2(4, 3)

    def test_draw_frames_and_pads_child(self) -> None:
        canvas = Canvas(6, 5)
        Box(Text("hi", align="center")).draw(canvas, Rect(0, 0, 6, 5))
        assert canvas.text() == [
            "┌────┐",
            "│    │",
            "│ hi │",
            "│    │",
            "└────┘",
        ]

    def test_draw_background_fill(self) -> None:
        style = Style(bg="blue")
        canvas = Canvas(4, 3)
        Box(Spacer(0, 0), style=style, padding=0).draw(canvas, Rect(0, 0, 4, 3))
        assert canvas.text() == [
            "┌──┐",
            "│  │",
            "└──┘",
        ]