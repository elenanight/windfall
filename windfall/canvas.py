"""A cell-grid rendering surface that primitives draw onto."""

from __future__ import annotations

from rich.text import Text as _RichText

from windfall.style import Style


class Canvas:
    """A fixed-size grid of styled characters.

    Primitives, layouts, and (later) widgets all draw into a shared canvas.
    The compositor turns it into one rich renderable for the live display,
    and :meth:`text` exposes the plain grid for headless snapshot tests.
    """

    def __init__(self, width: int, height: int, fill: str = " ") -> None:
        self._width = width
        self._height = height
        self._fill = fill
        self._cells = [[(fill, None) for _ in range(width)] for _ in range(height)]

    def write(self, text: str, x: int, y: int, style: Style | None = None) -> None:
        if y < 0 or y >= self._height:
            return
        row = self._cells[y]
        column = x
        for char in text:
            if 0 <= column < self._width:
                row[column] = (char, style)
            column += 1

    def fill(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        char: str = " ",
        style: Style | None = None,
    ) -> None:
        for row in range(max(0, y), min(self._height, y + height)):
            for column in range(max(0, x), min(self._width, x + width)):
                self._cells[row][column] = (char, style)

    def resize(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._cells = [[(self._fill, None) for _ in range(width)] for _ in range(height)]

    def text(self) -> list[str]:
        return ["".join(char for char, _ in row) for row in self._cells]

    def to_rich(self) -> _RichText:
        output = _RichText()
        for row_index, row in enumerate(self._cells):
            if row_index:
                output.append("\n")
            column = 0
            while column < self._width:
                _, style = row[column]
                end = column + 1
                while end < self._width and row[end][1] is style:
                    end += 1
                chunk = "".join(cell[0] for cell in row[column:end])
                output.append(chunk, style=style.to_rich() if style else None)
                column = end
        return output