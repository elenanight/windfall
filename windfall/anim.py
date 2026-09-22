"""Deterministic timekeeping, tweens, animations, and timelines."""

from __future__ import annotations

from windfall.geom import Vec2


def ease_linear(t: float) -> float:
    return t


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4 * t**3
    return 1 - (-2 * t + 2) ** 3 / 2


class Clock:
    """Accumulates simulated time; advance it explicitly with :meth:`step`.

    Pausing freezes elapsed time, which stops animations and game logic that
    read :attr:`elapsed`.
    """

    def __init__(self) -> None:
        self._elapsed = 0.0
        self._running = False

    def start(self) -> None:
        self._elapsed = 0.0
        self._running = True

    def pause(self) -> None:
        self._running = False

    def resume(self) -> None:
        self._running = True

    def step(self, dt: float) -> None:
        if self._running:
            self._elapsed += dt

    @property
    def elapsed(self) -> float:
        return self._elapsed


class Tween:
    """Interpolates a scalar from start to end over a duration with an easing.

    Drives animations a fixed step at a time for deterministic headless tests.
    """

    def __init__(self, start, end, duration, ease=ease_out_cubic) -> None:
        self._start = start
        self._end = end
        self._duration = max(0.0, duration)
        self._ease = ease
        self._t = 0.0
        self._done = False

    def step(self, dt: float) -> None:
        if self._done:
            return
        self._t += dt
        if self._t >= self._duration:
            self._t = self._duration
            self._done = True

    @property
    def value(self) -> float:
        if self._duration <= 0.0:
            progress = 1.0
        else:
            progress = self._t / self._duration
        eased = self._ease(progress)
        return self._start + (self._end - self._start) * eased

    @property
    def done(self) -> bool:
        return self._done

    def reset(self) -> None:
        self._t = 0.0
        self._done = False


class Animation:
    """A tween that writes its current value onto a target attribute."""

    def __init__(self, target, attribute: str, start, end, duration, ease=ease_out_cubic) -> None:
        self._target = target
        self._attribute = attribute
        self._tween = Tween(start, end, duration, ease)
        self._apply()

    def step(self, dt: float) -> None:
        if self.done:
            return
        self._tween.step(dt)
        self._apply()

    def _apply(self) -> None:
        setattr(self._target, self._attribute, self._tween.value)

    @property
    def done(self) -> bool:
        return self._tween.done

    def reset(self) -> None:
        self._tween.reset()
        self._apply()


class Motion:
    """Tweens a target's ``x``/``y`` floats along a Vec2 path from start to end.

    Like :class:`Animation` but for 2D motion: both axes share a single eased
    progress so the path stays a straight line between ``start`` and ``end``.
    The start value is applied when the motion is created.
    """

    def __init__(
        self,
        target,
        start: Vec2,
        end: Vec2,
        duration: float,
        ease=ease_out_cubic,
        x_attr: str = "x",
        y_attr: str = "y",
    ) -> None:
        self._target = target
        self._start = start
        self._end = end
        self._duration = max(0.0, duration)
        self._ease = ease
        self._x_attr = x_attr
        self._y_attr = y_attr
        self._t = 0.0
        self._done = False
        self._apply()

    def step(self, dt: float) -> None:
        if self._done:
            return
        self._t += dt
        if self._t >= self._duration:
            self._t = self._duration
            self._done = True
        self._apply()

    def _apply(self) -> None:
        if self._duration <= 0.0:
            progress = 1.0
        else:
            progress = self._t / self._duration
        eased = self._ease(progress)
        start, end = self._start, self._end
        setattr(self._target, self._x_attr, start.x + (end.x - start.x) * eased)
        setattr(self._target, self._y_attr, start.y + (end.y - start.y) * eased)

    @property
    def done(self) -> bool:
        return self._done

    def reset(self) -> None:
        self._t = 0.0
        self._done = False
        self._apply()


class Sequence:
    """Runs tween-like steps one after another, starting each when the previous ends.

    A step is either a tween-like object (a ``Tween``, ``Motion``, ``Animation``,
    or nested ``Sequence``) or a zero-argument callable that returns one.
    Callables are invoked lazily when their turn arrives, so a chain can build
    each step fresh from state that only settles once its turn is up.
    """

    def __init__(self, *steps) -> None:
        self._steps = list(steps)
        self._index = 0
        self._current: Tween | None = None

    def _peek(self) -> None:
        if self._current is not None or self._index >= len(self._steps):
            return
        step = self._steps[self._index]
        self._current = step() if callable(step) else step

    def step(self, dt: float) -> None:
        self._peek()
        if self._current is None:
            return
        self._current.step(dt)
        if self._current.done:
            self._index += 1
            self._current = None

    @property
    def done(self) -> bool:
        return self._index >= len(self._steps)

    def reset(self) -> None:
        for step in self._steps:
            if not callable(step):
                step.reset()
        self._index = 0
        self._current = None


class Timeline:
    """A collection of tweens advanced together, e.g. on a scene's tick."""

    def __init__(self) -> None:
        self._tweens: list[Tween] = []

    def add(self, tween: Tween) -> None:
        self._tweens.append(tween)

    def step(self, dt: float) -> None:
        for tween in self._tweens:
            tween.step(dt)

    @property
    def done(self) -> bool:
        return all(tween.done for tween in self._tweens)

    def clear(self) -> None:
        self._tweens.clear()