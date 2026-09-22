"""Tests for tweens, animations, and timelines."""

from __future__ import annotations

import pytest

from windfall.anim import (
    Animation,
    Clock,
    Motion,
    Sequence,
    Timeline,
    Tween,
    ease_in_out_cubic,
    ease_linear,
    ease_out_cubic,
)
from windfall.geom import Vec2


class TestClock:
    def test_starts_paused_at_zero(self) -> None:
        clock = Clock()
        assert clock.elapsed == 0.0
        clock.step(1.0)
        assert clock.elapsed == 0.0

    def test_start_resets_elapsed(self) -> None:
        clock = Clock()
        clock.start()
        clock.step(2.0)
        clock.start()
        assert clock.elapsed == 0.0

    def test_step_advances_only_while_running(self) -> None:
        clock = Clock()
        clock.start()
        clock.step(0.5)
        clock.pause()
        clock.step(10.0)
        assert clock.elapsed == 0.5
        clock.resume()
        clock.step(0.25)
        assert clock.elapsed == 0.75

    def test_step_accumulates_fixed_steps(self) -> None:
        clock = Clock()
        clock.start()
        for _ in range(3):
            clock.step(0.1)
        assert clock.elapsed == pytest.approx(0.3)

    def test_pause_does_not_advance(self) -> None:
        clock = Clock()
        clock.start()
        clock.step(1.0)
        clock.pause()
        clock.step(1.0)
        assert clock.elapsed == 1.0


class TestTween:
    def test_linear_midpoint(self) -> None:
        tween = Tween(0, 10, 2.0, ease=ease_linear)
        tween.step(1.0)
        assert tween.value == pytest.approx(5.0)

    def test_start_value(self) -> None:
        assert Tween(0, 10, 2.0, ease=ease_linear).value == 0.0

    def test_reaches_end_and_marks_done(self) -> None:
        tween = Tween(0, 10, 2.0, ease=ease_linear)
        tween.step(3.0)
        assert tween.done is True
        assert tween.value == pytest.approx(10.0)

    def test_steps_after_done_are_noops(self) -> None:
        tween = Tween(0, 1, 0.1)
        tween.step(1.0)
        assert tween.done is True
        tween.step(1.0)
        assert tween.value == 1.0

    def test_zero_duration_jumps_to_end(self) -> None:
        tween = Tween(5, 9, 0.0)
        tween.step(0.0)
        assert tween.value == 9.0
        assert tween.done is True

    def test_reset(self) -> None:
        tween = Tween(0, 10, 2.0, ease=ease_linear)
        tween.step(2.0)
        assert tween.done is True
        tween.reset()
        assert tween.done is False
        assert tween.value == 0.0


class TestEasing:
    def test_endpoints(self) -> None:
        for ease in (ease_linear, ease_out_cubic, ease_in_out_cubic):
            assert ease(0.0) == 0.0
            assert ease(1.0) == 1.0


class Holder:
    def __init__(self) -> None:
        self.value = 0.0


class TestAnimation:
    def test_applies_to_target(self) -> None:
        target = Holder()
        anim = Animation(target, "value", 1.0, 0.0, 1.0, ease=ease_linear)
        assert target.value == 1.0  # initial apply
        anim.step(0.5)
        assert target.value == pytest.approx(0.5)
        anim.step(1.0)
        assert anim.done is True
        assert target.value == pytest.approx(0.0)

    def test_reset_restores_start(self) -> None:
        target = Holder()
        anim = Animation(target, "value", 0.0, 10.0, 1.0, ease=ease_linear)
        anim.step(1.0)
        assert target.value == pytest.approx(10.0)
        anim.reset()
        assert target.value == 0.0
        assert anim.done is False


class Positioned:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0


class TestMotion:
    def test_strides_a_straight_path(self) -> None:
        target = Positioned()
        motion = Motion(target, Vec2(0, 0), Vec2(10, 20), 2.0, ease=ease_linear)
        assert (target.x, target.y) == (0.0, 0.0)  # initial apply
        motion.step(1.0)
        assert target.x == pytest.approx(5.0)
        assert target.y == pytest.approx(10.0)
        motion.step(1.0)
        assert motion.done is True
        assert (target.x, target.y) == (10.0, 20.0)

    def test_shared_ease_keeps_axes_on_the_line(self) -> None:
        target = Positioned()
        motion = Motion(target, Vec2(0, 0), Vec2(6, 9), 2.0, ease=ease_in_out_cubic)
        motion.step(1.0)
        assert target.x / target.y == pytest.approx(6 / 9)
        motion.step(1.0)
        assert (target.x, target.y) == (6.0, 9.0)

    def test_zero_duration_jumps_to_end(self) -> None:
        target = Positioned()
        motion = Motion(target, Vec2(1, 2), Vec2(9, 8), 0.0)
        motion.step(0.0)
        assert (target.x, target.y) == (9.0, 8.0)
        assert motion.done is True

    def test_writes_custom_attributes(self) -> None:
        target = Positioned()
        motion = Motion(target, Vec2(0, 0), Vec2(10, 0), 1.0, ease=ease_linear, x_attr="left", y_attr="right")
        assert target.left == 0.0
        motion.step(0.5)
        assert target.left == pytest.approx(5.0)

    def test_reset_restores_start(self) -> None:
        target = Positioned()
        motion = Motion(target, Vec2(1, 2), Vec2(9, 8), 1.0, ease=ease_linear)
        motion.step(1.0)
        assert (target.x, target.y) == (9.0, 8.0)
        motion.reset()
        assert motion.done is False
        assert (target.x, target.y) == (1.0, 2.0)


class TestSequence:
    def test_runs_steps_in_order(self) -> None:
        first = Tween(0, 10, 1.0, ease=ease_linear)
        second = Tween(0, 100, 1.0, ease=ease_linear)
        seq = Sequence(first, second)
        assert seq.done is False
        seq.step(1.0)
        assert first.done is True
        assert second.value == 0.0  # not started yet
        seq.step(0.5)
        assert second.value == pytest.approx(50.0)
        seq.step(1.0)
        assert seq.done is True

    def test_empty_sequence_is_done(self) -> None:
        assert Sequence().done is True

    def test_callable_steps_resolve_lazily(self) -> None:
        built: list[int] = []

        def step_one() -> Tween:
            built.append(1)
            return Tween(0, 1, 1.0, ease=ease_linear)

        def step_two() -> Tween:
            built.append(2)
            return Tween(0, 2, 1.0, ease=ease_linear)

        seq = Sequence(step_one, step_two)
        assert built == []  # nothing resolved until stepped
        seq.step(0.5)
        assert built == [1]  # first leg resolved and is running
        seq.step(0.5)
        assert built == [1]  # second leg not resolved until its turn
        assert seq.done is False
        seq.step(1.0)
        assert built == [1, 2]
        assert seq.done is True

    def test_steps_after_done_are_noops(self) -> None:
        seq = Sequence(Tween(0, 1, 0.1))
        seq.step(1.0)
        assert seq.done is True
        seq.step(10.0)
        assert seq.done is True


class TestTimeline:
    def test_steps_all_tweens(self) -> None:
        timeline = Timeline()
        first = Tween(0, 10, 1.0, ease=ease_linear)
        second = Tween(0, 20, 1.0, ease=ease_linear)
        timeline.add(first)
        timeline.add(second)
        timeline.step(0.5)
        assert first.value == pytest.approx(5.0)
        assert second.value == pytest.approx(10.0)
        assert timeline.done is False

    def test_done_when_all_complete(self) -> None:
        timeline = Timeline()
        timeline.add(Tween(0, 1, 0.1))
        timeline.add(Tween(0, 1, 0.2))
        timeline.step(1.0)
        assert timeline.done is True

    def test_clear(self) -> None:
        timeline = Timeline()
        timeline.add(Tween(0, 1, 0.1))
        timeline.clear()
        assert timeline.done is True  # vacuously true when empty