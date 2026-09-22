"""Golden snapshot tests: composed UIs rendered to plain text grids."""

from __future__ import annotations

from tests.helpers import render
from windfall.layout import Column, Row
from windfall.primitives import Box, Divider, Text


class TestSnapshots:
    def test_menu_column_snapshot(self) -> None:
        column = Column()
        column.add(Box(Text("hello"), padding=0))
        column.add(Divider())
        column.add(Text("windfall"))
        column.add(Row().add(Text("A ")).add(Text("B")))
        assert render(column, 9, 7) == [
            "┌───────┐",
            "│hello  │",
            "└───────┘",
            "─────────",
            "windfall ",
            "A B      ",
            "         ",
        ]

    def test_padded_centered_box_snapshot(self) -> None:
        assert render(Box(Text("hi", align="center")), 6, 5) == [
            "┌────┐",
            "│    │",
            "│ hi │",
            "│    │",
            "└────┘",
        ]

    def test_nested_boxes_snapshot(self) -> None:
        outer = Box(Column().add(Box(Text("in"), padding=0)))
        assert render(outer, 8, 7) == [
            "┌──────┐",
            "│      │",
            "│ ┌──┐ │",
            "│ │in│ │",
            "│ └──┘ │",
            "│      │",
            "└──────┘",
        ]