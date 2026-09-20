"""2D geometry value objects shared across the engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Vec2:
    """Immutable 2D offset expressed in integer terminal cells."""

    x: int
    y: int

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: int) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)


class Rect:
    """Axis-aligned rectangle with a position and a size (width/height >= 0)."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        if width < 0 or height < 0:
            raise ValueError("Rect width and height must be >= 0")
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __contains__(self, point: Vec2) -> bool:
        return (
            self.x <= point.x < self.x + self.width
            and self.y <= point.y < self.y + self.height
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rect):
            return NotImplemented
        return (
            (self.x, self.y, self.width, self.height)
            == (other.x, other.y, other.width, other.height)
        )

    def move(self, offset: Vec2) -> Rect:
        return Rect(self.x + offset.x, self.y + offset.y, self.width, self.height)

    def inset(self, amount: int) -> Rect:
        width = max(0, self.width - 2 * amount)
        height = max(0, self.height - 2 * amount)
        return Rect(self.x + amount, self.y + amount, width, height)

    def intersection(self, other: Rect) -> Rect | None:
        x0 = max(self.x, other.x)
        y0 = max(self.y, other.y)
        x1 = min(self.x + self.width, other.x + other.width)
        y1 = min(self.y + self.height, other.y + other.height)
        if x1 < x0 or y1 < y0:
            return None
        return Rect(x0, y0, x1 - x0, y1 - y0)