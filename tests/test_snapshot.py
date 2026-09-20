"""Golden snapshot tests: composed UIs rendered to plain text grids."""

from __future__ import annotations

from windfall.canvas import Canvas
from windfall.geom import Rect
from windfall.layout import Column, Row
from windfall.primitives import Box, Divider, Text


def render(width: int, height: int, prim) -> list[str]:
    canvas = Canvas(width, height)
    prim.draw(canvas, Rect(0, 0, width, height))
    return canvas.text()


def test_menu_column_snapshot() -> None:
    column = Column()
    column.add(Box(Text("hello"), padding=0))
    column.add(Divider())
    column.add(Text("windfall"))
    column.add(Row().add(Text("A ")).add(Text("B")))
    assert render(9, 7, column) == [
        "┌───────┐",
        "│hello  │",
        "└───────┘",
        "─────────",
        "windfall ",
        "A B      ",
        "         ",
    ]


def test_padded_centered_box_snapshot() -> None:
    assert render(6, 5, Box(Text("hi", align="center"))) == [
        "┌────┐",
        "│    │",
        "│ hi │",
        "│    │",
        "└────┘",
    ]


def test_nested_boxes_snapshot() -> None:
    outer = Box(Column().add(Box(Text("in"), padding=0)))
    assert render(8, 7, outer) == [
        "┌──────┐",
        "│      │",
        "│ ┌──┐ │",
        "│ │in│ │",
        "│ └──┘ │",
        "│      │",
        "└──────┘",
    ]