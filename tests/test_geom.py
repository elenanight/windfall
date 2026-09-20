"""Tests for 2D geometry value objects."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from windfall.geom import Rect, Vec2


def test_vec2_add() -> None:
    assert Vec2(1, 2) + Vec2(3, 4) == Vec2(4, 6)


def test_vec2_sub() -> None:
    assert Vec2(5, 5) - Vec2(2, 1) == Vec2(3, 4)


def test_vec2_mul_scalar() -> None:
    assert Vec2(2, 3) * 4 == Vec2(8, 12)


def test_vec2_immutable() -> None:
    vec = Vec2(1, 2)
    with pytest.raises(FrozenInstanceError):
        vec.x = 99  # type: ignore[misc]


def test_vec2_equality() -> None:
    assert Vec2(1, 2) == Vec2(1, 2)
    assert Vec2(1, 2) != Vec2(2, 1)


def test_rect_rejects_negative_sizes() -> None:
    with pytest.raises(ValueError):
        Rect(0, 0, -1, 5)


def test_rect_equality() -> None:
    assert Rect(1, 2, 3, 4) == Rect(1, 2, 3, 4)
    assert Rect(1, 2, 3, 4) != Rect(0, 0, 0, 0)


def test_rect_contains_points() -> None:
    rect = Rect(0, 0, 10, 5)
    assert Vec2(0, 0) in rect
    assert Vec2(9, 4) in rect
    assert Vec2(10, 4) not in rect  # exclusive right edge
    assert Vec2(5, 5) not in rect  # exclusive bottom edge
    assert Vec2(-1, 0) not in rect


def test_rect_move() -> None:
    rect = Rect(1, 2, 3, 4).move(Vec2(10, 20))
    assert rect == Rect(11, 22, 3, 4)


def test_rect_inset() -> None:
    assert Rect(0, 0, 10, 10).inset(1) == Rect(1, 1, 8, 8)


def test_rect_inset_clamps_at_zero() -> None:
    assert Rect(0, 0, 4, 4).inset(5) == Rect(5, 5, 0, 0)


def test_rect_intersection_overlapping() -> None:
    result = Rect(0, 0, 10, 10).intersection(Rect(5, 5, 10, 10))
    assert result == Rect(5, 5, 5, 5)


def test_rect_intersection_disjoint_returns_none() -> None:
    assert Rect(0, 0, 2, 2).intersection(Rect(5, 5, 2, 2)) is None