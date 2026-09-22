"""Tests for layout containers."""

from __future__ import annotations

import pytest

from windfall.canvas import Canvas
from windfall.geom import Rect, Vec2
from windfall.layout import Center, Column, Row, Stack
from windfall.primitives import Text


class TestContainer:
    def test_add_returns_container(self) -> None:
        column = Column()
        child = Text("x")
        assert column.add(child) is column
        assert column.children == [child]

    def test_remove_and_clear(self) -> None:
        column = Column()
        first = Text("a")
        column.add(first)
        column.add(Text("b"))
        column.remove(first)
        assert len(column.children) == 1
        column.clear()
        assert column.children == []

    def test_empty_size_is_zero(self) -> None:
        assert Column().size() == Vec2(0, 0)
        assert Row().size() == Vec2(0, 0)
        assert Stack().size() == Vec2(0, 0)
        assert Center().size() == Vec2(0, 0)


class TestColumn:
    def test_size_sums_heights(self) -> None:
        column = Column()
        column.add(Text("bb"))
        column.add(Text("ddd"))
        assert column.size() == Vec2(3, 2)

    def test_draw_stacks_top_to_bottom(self) -> None:
        column = Column()
        column.add(Text("aa"))
        column.add(Text("bb"))
        canvas = Canvas(4, 2)
        column.draw(canvas, Rect(0, 0, 4, 2))
        assert canvas.text() == ["aa  ", "bb  "]


class TestRow:
    def test_size_sums_widths(self) -> None:
        row = Row()
        row.add(Text("aa"))
        row.add(Text("bbb"))
        assert row.size() == Vec2(5, 1)

    def test_draw_places_left_to_right(self) -> None:
        row = Row()
        row.add(Text("aa"))
        row.add(Text("bb"))
        canvas = Canvas(4, 1)
        row.draw(canvas, Rect(0, 0, 4, 1))
        assert canvas.text() == ["aabb"]

    def test_fill_shares_extra_width_equally(self) -> None:
        row = Row(fill=True)
        row.add(Text("aa"))
        row.add(Text("bb"))
        assert row.size() == Vec2(4, 1)  # measuring stays natural
        canvas = Canvas(10, 1)
        row.draw(canvas, Rect(0, 0, 10, 1))
        assert canvas.text() == ["aa   bb   "]

    def test_fill_splits_remainder_left_to_right(self) -> None:
        row = Row(fill=True)
        row.add(Text("aa"))
        row.add(Text("bb"))
        canvas = Canvas(9, 1)
        row.draw(canvas, Rect(0, 0, 9, 1))
        assert canvas.text() == ["aa   bb  "]

    def test_fill_keeps_natural_widths_when_cramped(self) -> None:
        row = Row(fill=True)
        row.add(Text("aa"))
        row.add(Text("bb"))
        canvas = Canvas(3, 1)
        row.draw(canvas, Rect(0, 0, 3, 1))
        assert canvas.text() == ["aab"]

    def test_fill_weights_share_extra_proportionally(self) -> None:
        row = Row(fill=True, weights=[1, 0])
        row.add(Text("aa"))
        row.add(Text("bb"))
        canvas = Canvas(10, 1)
        row.draw(canvas, Rect(0, 0, 10, 1))
        assert canvas.text() == ["aa      bb"]

    def test_fill_missing_weights_default_to_one(self) -> None:
        row = Row(fill=True, weights=[2])
        row.add(Text("aa"))
        row.add(Text("bb"))
        canvas = Canvas(10, 1)
        row.draw(canvas, Rect(0, 0, 10, 1))
        assert canvas.text() == ["aa    bb  "]

    def test_fill_all_zero_weights_keeps_natural(self) -> None:
        row = Row(fill=True, weights=[0, 0])
        row.add(Text("aa"))
        row.add(Text("bb"))
        canvas = Canvas(10, 1)
        row.draw(canvas, Rect(0, 0, 10, 1))
        assert canvas.text() == ["aabb      "]


class TestStack:
    def test_size_uses_max_dimensions(self) -> None:
        stack = Stack()
        stack.add(Text("aa"))
        stack.add(Text("bbb"))
        assert stack.size() == Vec2(3, 1)

    def test_draw_overlays_later_children_on_top(self) -> None:
        stack = Stack()
        stack.add(Text("ab"))
        stack.add(Text("c "))
        canvas = Canvas(2, 1)
        stack.draw(canvas, Rect(0, 0, 2, 1))
        assert canvas.text() == ["c "]


class TestCenter:
    def test_size_uses_max_dimensions(self) -> None:
        center = Center()
        center.add(Text("aa"))
        center.add(Text("bbb"))
        assert center.size() == Vec2(3, 1)

    def test_draw_centers_child_horizontally(self) -> None:
        center = Center()
        center.add(Text("ab"))
        canvas = Canvas(6, 1)
        center.draw(canvas, Rect(0, 0, 6, 1))
        assert canvas.text() == ["  ab  "]

    def test_draw_centers_child_vertically(self) -> None:
        center = Center()
        center.add(Text("ab"))
        canvas = Canvas(2, 3)
        center.draw(canvas, Rect(0, 0, 2, 3))
        assert canvas.text() == ["  ", "ab", "  "]

    def test_clips_when_child_is_larger_than_rect(self) -> None:
        center = Center()
        center.add(Text("abcd"))
        canvas = Canvas(2, 1)
        center.draw(canvas, Rect(0, 0, 2, 1))
        assert canvas.text() == ["ab"]

    def test_align_left_pins_child_to_left_edge(self) -> None:
        center = Center(align="left")
        center.add(Text("ab"))
        canvas = Canvas(6, 1)
        center.draw(canvas, Rect(0, 0, 6, 1))
        assert canvas.text() == ["ab    "]

    def test_align_right_pins_child_to_right_edge(self) -> None:
        center = Center(align="right")
        center.add(Text("ab"))
        canvas = Canvas(6, 1)
        center.draw(canvas, Rect(0, 0, 6, 1))
        assert canvas.text() == ["    ab"]

    def test_align_defaults_to_center_and_rejects_unknown(self) -> None:
        center = Center()
        center.add(Text("ab"))
        canvas = Canvas(6, 1)
        center.draw(canvas, Rect(0, 0, 6, 1))
        assert canvas.text() == ["  ab  "]
        with pytest.raises(ValueError):
            Center(align="diagonal")