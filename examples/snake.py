"""A tiny snake game: a custom ``Component`` driven by the engine loop.

Arrows steer, Enter restarts after a collision, and Ctrl+C quits. Movement is
stepped by ``update(dt)`` on a fixed tick, so steering and collisions are
deterministic and headless-testable. Run with:
`uv run python examples/snake.py`.
"""

from __future__ import annotations

import random

from windfall import Component, Engine, Event, Rect, Scene, Vec2
from windfall.events import ACTIVATE, MOVE

_TICK = 0.12

_DIRECTIONS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def _random_food(body, width: int, height: int, rng) -> tuple:
    occupied = set(body)
    free = [(x, y) for x in range(width) for y in range(height) if (x, y) not in occupied]
    return rng.choice(free) if free else body[0]


class Snake(Component):
    """A playable grid snake: grows on food, dies on walls or itself."""

    def __init__(self, width: int = 20, height: int = 10, seed: int | None = None) -> None:
        super().__init__()
        self.width = width
        self.height = height
        self._rng = random.Random(seed)
        self._body = [(width // 2, height // 2)]
        self._dir = (1, 0)
        self._timer = 0.0
        self.alive = True
        self._food = _random_food(self._body, width, height, self._rng)

    def size(self) -> Vec2:
        return Vec2(self.width, self.height)

    def draw(self, canvas, rect: Rect) -> None:
        canvas.fill(rect.x, rect.y, rect.width, rect.height, "·")
        food_x, food_y = self._food
        canvas.write("o", rect.x + food_x, rect.y + food_y)
        for x, y in self._body:
            canvas.write("■", rect.x + x, rect.y + y)
        head_x, head_y = self._body[0]
        canvas.write("●", rect.x + head_x, rect.y + head_y, None)

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        self._timer += dt
        while self._timer >= _TICK and self.alive:
            self._timer -= _TICK
            self._move()

    def handle(self, event: Event) -> bool:
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
        else:
            self._body.pop()


def build() -> Scene:
    return Scene(name="snake", root=Snake(width=20, height=10, seed=7))


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build())
    engine.run()