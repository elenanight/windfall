"""Headless tests for the example apps in examples/."""

from __future__ import annotations

import pytest

from examples import bouncer, menu, snake
from windfall import Compositor, Engine, Event
from windfall.events import ACTIVATE, MOVE
from windfall.widgets import ListView

_TICK = snake._TICK


def test_menu_arrows_move_selection() -> None:
    scene = menu.build()
    engine = Engine()
    engine.use_scene(scene)
    engine.post_event(Event(MOVE, {"direction": "down"}))
    engine.step(0.016)
    list_view = scene.root.children[2]
    assert isinstance(list_view, ListView)
    assert list_view.selection == 1


def test_menu_renders() -> None:
    scene = menu.build()
    rows = Compositor(40, 12).text(scene)
    assert any(row.strip() for row in rows)


def test_bouncer_animates_and_reverses() -> None:
    scene = bouncer.build(width=24)
    engine = Engine()
    engine.use_scene(scene)
    engine.step(0.5)
    assert scene.ball.x == pytest.approx(11.5)
    engine.step(1.0)
    assert scene.ball.x == pytest.approx(23.0)
    engine.step(0.5)
    assert scene.ball.x == pytest.approx(11.5)


def test_bouncer_renders() -> None:
    scene = bouncer.build(width=24)
    rows = Compositor(24, 4).text(scene)
    assert any(row.strip() for row in rows)


def test_snake_steers_and_eats() -> None:
    scene = snake.build()
    game = scene.root
    engine = Engine()
    engine.use_scene(scene)
    game._food = (game.width // 2 + 1, game.height // 2)
    engine.step(_TICK)
    assert game._body[0] == (game.width // 2 + 1, game.height // 2)
    assert len(game._body) == 2
    engine.post_event(Event(MOVE, {"direction": "up"}))
    engine.step(_TICK)
    assert game._body[0] == (game.width // 2 + 1, game.height // 2 - 1)


def test_snake_dies_and_restarts() -> None:
    scene = snake.build()
    game = scene.root
    engine = Engine()
    engine.use_scene(scene)
    assert game.alive is True
    engine.post_event(Event(MOVE, {"direction": "up"}))
    for _ in range(6):
        engine.step(_TICK)
    assert game.alive is False
    engine.post_event(Event(ACTIVATE))
    engine.step(0.016)
    assert game.alive is True
    assert game._body == [(game.width // 2, game.height // 2)]


def test_snake_renders() -> None:
    rows = Compositor(20, 10).text(snake.build())
    assert any(row.strip() for row in rows)