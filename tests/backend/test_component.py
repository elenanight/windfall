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


class TestComponent:
    def test_is_a_primitive(self) -> None:
        assert issubclass(Component, Primitive)
        assert isinstance(Dummy(), Primitive)

    def test_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            Component()  # type: ignore[abstract]

    def test_defaults(self) -> None:
        widget = Dummy()
        assert widget.focused is False
        assert widget.focusable is False
        assert widget.id == ""

    def test_id_can_be_passed_or_assigned(self) -> None:
        assert Dummy("greeting").id == "greeting"
        widget = Dummy()
        widget.id = "player"
        assert widget.id == "player"

    def test_focus_toggles(self) -> None:
        widget = Dummy()
        widget.focus(True)
        assert widget.focused is True
        widget.focus(False)
        assert widget.focused is False

    def test_update_is_noop(self) -> None:
        Dummy().update(0.016)

    def test_handle_defaults_to_false(self) -> None:
        assert Dummy().handle(Event("anything")) is False