"""Headless tests for the example apps in examples/."""

from __future__ import annotations

import pytest

from examples import bouncer, menu, snake
from tests.helpers import move
from windfall import Compositor, Engine
from windfall.events import ACTIVATE, Event
from windfall.widgets import ListView

_TICK = snake._TICK


class TestExampleMenu:
    def test_arrows_move_selection(self) -> None:
        scene = menu.build()
        engine = Engine()
        engine.use_scene(scene)
        engine.post_event(move("down"))
        engine.step(0.016)
        list_view = scene.root.children[2]
        assert isinstance(list_view, ListView)
        assert list_view.selection == 1

    def test_renders(self) -> None:
        scene = menu.build()
        rows = Compositor(40, 12).text(scene)
        assert any(row.strip() for row in rows)


class TestBouncer:
    def test_animates_and_reverses(self) -> None:
        scene = bouncer.build(width=24)
        engine = Engine()
        engine.use_scene(scene)
        engine.step(0.5)
        assert scene.ball.x == pytest.approx(11.5)
        engine.step(1.0)
        assert scene.ball.x == pytest.approx(23.0)
        engine.step(0.5)
        assert scene.ball.x == pytest.approx(11.5)

    def test_renders(self) -> None:
        scene = bouncer.build(width=24)
        rows = Compositor(24, 4).text(scene)
        assert any(row.strip() for row in rows)


class TestSnake:
    def test_steers_and_eats(self) -> None:
        scene = snake.build()
        game = scene.root
        engine = Engine()
        engine.use_scene(scene)
        game._food = (game.width // 2 + 1, game.height // 2)
        engine.step(_TICK)
        assert game._body[0] == (game.width // 2 + 1, game.height // 2)
        assert len(game._body) == 2
        engine.post_event(move("up"))
        engine.step(_TICK)
        assert game._body[0] == (game.width // 2 + 1, game.height // 2 - 1)

    def test_dies_and_restarts(self) -> None:
        scene = snake.build()
        game = scene.root
        engine = Engine()
        engine.use_scene(scene)
        assert game.alive is True
        engine.post_event(move("up"))
        for _ in range(6):
            engine.step(_TICK)
        assert game.alive is False
        engine.post_event(Event(ACTIVATE))
        engine.step(0.016)
        assert game.alive is True
        assert game._body == [(game.width // 2, game.height // 2)]

    def test_renders(self) -> None:
        rows = Compositor(20, 10).text(snake.build())
        assert any(row.strip() for row in rows)