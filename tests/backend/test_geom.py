"""Tests for 2D geometry value objects."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from windfall.geom import Rect, Vec2


class TestVec2:
    def test_add(self) -> None:
        assert Vec2(1, 2) + Vec2(3, 4) == Vec2(4, 6)

    def test_sub(self) -> None:
        assert Vec2(5, 5) - Vec2(2, 1) == Vec2(3, 4)

    def test_mul_scalar(self) -> None:
        assert Vec2(2, 3) * 4 == Vec2(8, 12)

    def test_immutable(self) -> None:
        vec = Vec2(1, 2)
        with pytest.raises(FrozenInstanceError):
            vec.x = 99  # type: ignore[misc]

    def test_equality(self) -> None:
        assert Vec2(1, 2) == Vec2(1, 2)
        assert Vec2(1, 2) != Vec2(2, 1)


class TestRect:
    def test_rejects_negative_sizes(self) -> None:
        with pytest.raises(ValueError):
            Rect(0, 0, -1, 5)

    def test_equality(self) -> None:
        assert Rect(1, 2, 3, 4) == Rect(1, 2, 3, 4)
        assert Rect(1, 2, 3, 4) != Rect(0, 0, 0, 0)

    def test_contains_points(self) -> None:
        rect = Rect(0, 0, 10, 5)
        assert Vec2(0, 0) in rect
        assert Vec2(9, 4) in rect
        assert Vec2(10, 4) not in rect  # exclusive right edge
        assert Vec2(5, 5) not in rect  # exclusive bottom edge
        assert Vec2(-1, 0) not in rect

    def test_move(self) -> None:
        rect = Rect(1, 2, 3, 4).move(Vec2(10, 20))
        assert rect == Rect(11, 22, 3, 4)

    def test_inset(self) -> None:
        assert Rect(0, 0, 10, 10).inset(1) == Rect(1, 1, 8, 8)

    def test_inset_clamps_at_zero(self) -> None:
        assert Rect(0, 0, 4, 4).inset(5) == Rect(5, 5, 0, 0)

    def test_intersection_overlapping(self) -> None:
        result = Rect(0, 0, 10, 10).intersection(Rect(5, 5, 10, 10))
        assert result == Rect(5, 5, 5, 5)

    def test_intersection_disjoint_returns_none(self) -> None:
        assert Rect(0, 0, 2, 2).intersection(Rect(5, 5, 2, 2)) is None