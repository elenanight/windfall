"""Tests for the interactive component base."""

from __future__ import annotations

import pytest

from windfall.component import Component
from windfall.events import Event
from windfall.geom import Rect, Vec2
from windfall.primitives import Primitive


class Dummy(Component):
    def size(self) -> Vec2:
        return Vec2(1, 1)

    def draw(self, canvas, rect: Rect) -> None:
        return None


def test_component_is_a_primitive() -> None:
    assert issubclass(Component, Primitive)
    assert isinstance(Dummy(), Primitive)


def test_component_is_abstract() -> None:
    with pytest.raises(TypeError):
        Component()  # type: ignore[abstract]


def test_component_defaults() -> None:
    widget = Dummy()
    assert widget.focused is False
    assert widget.focusable is False


def test_focus_toggles() -> None:
    widget = Dummy()
    widget.focus(True)
    assert widget.focused is True
    widget.focus(False)
    assert widget.focused is False


def test_update_is_noop() -> None:
    Dummy().update(0.016)


def test_handle_defaults_to_false() -> None:
    assert Dummy().handle(Event("anything")) is False