"""Headless tests for the example apps in examples/."""

from __future__ import annotations

import pytest

from examples import animation, bouncer, menu, snake
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
    def test_bounces_up_then_back_down(self) -> None:
        scene = bouncer.build(width=24)
        engine = Engine()
        engine.use_scene(scene)
        assert scene.ball.y == pytest.approx(5.0)  # resting on the floor
        engine.step(0.5)
        assert scene.ball.y == pytest.approx(2.5)  # halfway up
        engine.step(0.5)
        assert scene.ball.y == pytest.approx(0.0)  # at the ceiling
        engine.step(0.5)
        assert scene.ball.y == pytest.approx(2.5)  # halfway down
        engine.step(0.5)
        assert scene.ball.y == pytest.approx(5.0)  # floor again, loop restarts

    def test_renders(self) -> None:
        rows = Compositor(24, 8).text(bouncer.build(width=24))
        assert any(row.strip() for row in rows)


class TestAnimationShowcase:
    def test_racers_reach_the_edge(self) -> None:
        scene = animation.build(width=24)
        engine = Engine()
        engine.use_scene(scene)
        for _ in range(200):
            engine.step(0.016)
        assert scene.racers[0].x == pytest.approx(23.0)
        assert scene.racers[1].x == pytest.approx(23.0)
        assert scene.racers[2].x == pytest.approx(23.0)

    def test_orbiter_traces_a_visible_square(self) -> None:
        scene = animation.build(width=24)
        engine = Engine()
        engine.use_scene(scene)
        for _ in range(25):  # leg 1: along the top to the right corner
            engine.step(0.016)
        assert scene.orbiter.x == pytest.approx(5.0)
        assert scene.orbiter.y == pytest.approx(0.0)
        for _ in range(25):  # leg 2: down the right edge
            engine.step(0.016)
        assert scene.orbiter.y == pytest.approx(5.0)
        for _ in range(50):  # legs 3-4: back along the bottom and up
            engine.step(0.016)
        assert scene.orbiter.x == pytest.approx(0.0)
        assert scene.orbiter.y == pytest.approx(0.0)
        for _ in range(100):  # a second orbit still returns to the corner
            engine.step(0.016)
        assert scene.orbiter.x == pytest.approx(0.0)
        assert scene.orbiter.y == pytest.approx(0.0)

    def test_renders(self) -> None:
        rows = Compositor(30, 18).text(animation.build(width=24))
        assert any(row.strip() for row in rows)


class TestSnake:
    def test_steers_and_eats(self) -> None:
        scene = snake.build()
        game = scene.snake
        engine = Engine()
        engine.use_scene(scene)
        game._food = (game.width // 2 + 1, game.height // 2)
        engine.step(_TICK)
        assert game._body[0] == (game.width // 2 + 1, game.height // 2)
        assert game.score == 1
        engine.post_event(move("up"))
        engine.step(_TICK)
        assert game._body[0] == (game.width // 2 + 1, game.height // 2 - 1)

    def test_dies_and_restarts(self) -> None:
        scene = snake.build()
        game = scene.snake
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

    def test_no_turning_back_into_itself(self) -> None:
        scene = snake.build()
        game = scene.snake
        engine = Engine()
        engine.use_scene(scene)
        engine.post_event(move("left"))  # reverse of the starting rightward dir
        engine.step(_TICK)
        assert game._body[0] == (game.width // 2 + 1, game.height // 2)

    def test_win_when_board_is_eaten(self) -> None:
        game = snake.Snake(2, 1, seed=1)
        game._body = [(0, 0)]  # one cell free: (1, 0) holds the food
        game._food = (1, 0)
        game._dir = (1, 0)
        game._move()  # eat the final cell; nothing left for food
        assert game.won is True
        assert game.alive is False

    def test_status_line_reports_length(self) -> None:
        scene = snake.build()
        engine = Engine()
        engine.use_scene(scene)
        game = scene.snake
        game._food = (game.width // 2 + 1, game.height // 2)
        engine.step(_TICK)
        rows = Compositor(40, 14).text(scene)
        assert any("length 1" in row for row in rows)

    def test_renders(self) -> None:
        rows = Compositor(40, 14).text(snake.build())
        assert any(row.strip() for row in rows)