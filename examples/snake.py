"""A clean grid snake: steer with arrows, grow on food, die on walls or self.

Movement is stepped by ``update(dt)`` on a fixed tick so steering, eating,
collisions, and restarts are deterministic and headless-testable. Deaths —
and an entire-board win — pause play until Enter restarts. Run with:
`uv run python examples/snake.py`.
"""

from __future__ import annotations

import random

from windfall import Column, Component, Engine, Label, Rect, Scene, Stack, Style, Text, Vec2
from windfall.events import ACTIVATE, MOVE

_TICK = 0.2

_DIRECTIONS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}

_GRID = "·"
_BODY = "■"
_HEAD = "●"
_FOOD = "o"


def _random_food(body, width: int, height: int, rng) -> tuple | None:
    """Pick a free cell for food, or ``None`` when the board is fully eaten."""
    occupied = set(body)
    free = [(x, y) for x in range(width) for y in range(height) if (x, y) not in occupied]
    return rng.choice(free) if free else None


class Snake(Component):
    """A playable grid snake that grows on food and dies on walls or itself.

    ``alive`` is ``False`` while paused after a collision — or a board-clearing
    win — and an ``ACTIVATE`` event restarts once more. ``score`` counts food
    eaten (body length minus one).
    """

    def __init__(self, width: int = 20, height: int = 10, seed: int | None = None) -> None:
        super().__init__()
        self.width = width
        self.height = height
        self._rng = random.Random(seed)
        self._body = [(width // 2, height // 2)]
        self._dir = (1, 0)
        self._timer = 0.0
        self.alive = True
        self.won = False
        self._food = _random_food(self._body, width, height, self._rng)

    @property
    def score(self) -> int:
        return len(self._body) - 1

    def size(self) -> Vec2:
        return Vec2(self.width, self.height)

    def draw(self, canvas, rect: Rect) -> None:
        if self._food is not None:
            food_x, food_y = self._food
            canvas.write(_FOOD, rect.x + food_x, rect.y + food_y, Style(fg="yellow"))
        for index, (x, y) in enumerate(self._body):
            glyph = _HEAD if index == 0 else _BODY
            canvas.write(glyph, rect.x + x, rect.y + y, Style(fg="green"))

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        self._timer += dt
        while self._timer >= _TICK and self.alive:
            self._timer -= _TICK
            self._move()

    def handle(self, event) -> bool:
        if event.kind == MOVE and self.alive:
            direction = event.data.get("direction")
            if direction not in _DIRECTIONS:
                return False
            step_x, step_y = _DIRECTIONS[direction]
            if (step_x, step_y) != (-self._dir[0], -self._dir[1]):
                self._dir = (step_x, step_y)
            return True
        if event.kind == ACTIVATE and not self.alive:
            self._body = [(self.width // 2, self.height // 2)]
            self._dir = (1, 0)
            self._timer = 0.0
            self.alive = True
            self.won = False
            self._food = _random_food(self._body, self.width, self.height, self._rng)
            return True
        return False

    def _move(self) -> None:
        head_x, head_y = self._body[0]
        step_x, step_y = self._dir
        next_head = (head_x + step_x, head_y + step_y)
        if not (0 <= next_head[0] < self.width and 0 <= next_head[1] < self.height):
            self.alive = False
            return
        if next_head in self._body:
            self.alive = False
            return
        self._body.insert(0, next_head)
        if next_head == self._food:
            self._food = _random_food(self._body, self.width, self.height, self._rng)
            if self._food is None:
                self.alive = False
                self.won = True
        else:
            self._body.pop()


class SnakeScene(Scene):
    """A clean grid game: title, the snake board, and a live status line."""

    def __init__(self, width: int = 20, height: int = 10, seed: int | None = None) -> None:
        super().__init__(name="snake")
        self.width = width
        self.height = height
        self.snake = Snake(width, height, seed)
        grid = "\n".join(_GRID * width for _ in range(height))
        self.status = Label("↑↓←→ steer · ctrl+c quits")
        root = Column()
        root.add(Label("snake", align="center"))
        root.add(Stack().add(Text(grid)).add(self.snake))
        root.add(self.status)
        self.root = root

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.snake.won:
            self.status.set_text("you ate the whole board! · enter restarts")
        elif not self.snake.alive:
            self.status.set_text("game over · enter restarts")
        else:
            self.status.set_text(f"length {self.snake.score} · ↑↓←→ steer · ctrl+c quits")


def build(width: int = 20, height: int = 10, seed: int | None = 7) -> Scene:
    return SnakeScene(width, height, seed)


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build())
    engine.run()