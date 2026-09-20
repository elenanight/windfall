"""Tests for tweens, animations, and timelines."""

from __future__ import annotations

import pytest

from windfall.anim import (
    Animation,
    Clock,
    Timeline,
    Tween,
    ease_in_out_cubic,
    ease_linear,
    ease_out_cubic,
)


def test_clock_starts_paused_at_zero() -> None:
    clock = Clock()
    assert clock.elapsed == 0.0
    clock.step(1.0)
    assert clock.elapsed == 0.0


def test_clock_start_resets_elapsed() -> None:
    clock = Clock()
    clock.start()
    clock.step(2.0)
    clock.start()
    assert clock.elapsed == 0.0


def test_clock_step_advances_only_while_running() -> None:
    clock = Clock()
    clock.start()
    clock.step(0.5)
    clock.pause()
    clock.step(10.0)
    assert clock.elapsed == 0.5
    clock.resume()
    clock.step(0.25)
    assert clock.elapsed == 0.75


def test_clock_step_accumulates_fixed_steps() -> None:
    clock = Clock()
    clock.start()
    for _ in range(3):
        clock.step(0.1)
    assert clock.elapsed == pytest.approx(0.3)


def test_clock_pause_does_not_advance() -> None:
    clock = Clock()
    clock.start()
    clock.step(1.0)
    clock.pause()
    clock.step(1.0)
    assert clock.elapsed == 1.0


def test_tween_linear_midpoint() -> None:
    tween = Tween(0, 10, 2.0, ease=ease_linear)
    tween.step(1.0)
    assert tween.value == pytest.approx(5.0)


def test_tween_start_value() -> None:
    assert Tween(0, 10, 2.0, ease=ease_linear).value == 0.0


def test_tween_reaches_end_and_marks_done() -> None:
    tween = Tween(0, 10, 2.0, ease=ease_linear)
    tween.step(3.0)
    assert tween.done is True
    assert tween.value == pytest.approx(10.0)


def test_tween_steps_after_done_are_noops() -> None:
    tween = Tween(0, 1, 0.1)
    tween.step(1.0)
    assert tween.done is True
    tween.step(1.0)
    assert tween.value == 1.0


def test_tween_zero_duration_jumps_to_end() -> None:
    tween = Tween(5, 9, 0.0)
    tween.step(0.0)
    assert tween.value == 9.0
    assert tween.done is True


def test_tween_reset() -> None:
    tween = Tween(0, 10, 2.0, ease=ease_linear)
    tween.step(2.0)
    assert tween.done is True
    tween.reset()
    assert tween.done is False
    assert tween.value == 0.0


def test_ease_endpoints() -> None:
    for ease in (ease_linear, ease_out_cubic, ease_in_out_cubic):
        assert ease(0.0) == 0.0
        assert ease(1.0) == 1.0


class Holder:
    def __init__(self) -> None:
        self.value = 0.0


def test_animation_applies_to_target() -> None:
    target = Holder()
    anim = Animation(target, "value", 1.0, 0.0, 1.0, ease=ease_linear)
    assert target.value == 1.0  # initial apply
    anim.step(0.5)
    assert target.value == pytest.approx(0.5)
    anim.step(1.0)
    assert anim.done is True
    assert target.value == pytest.approx(0.0)


def test_animation_reset_restores_start() -> None:
    target = Holder()
    anim = Animation(target, "value", 0.0, 10.0, 1.0, ease=ease_linear)
    anim.step(1.0)
    assert target.value == pytest.approx(10.0)
    anim.reset()
    assert target.value == 0.0
    assert anim.done is False


def test_timeline_steps_all_tweens() -> None:
    timeline = Timeline()
    first = Tween(0, 10, 1.0, ease=ease_linear)
    second = Tween(0, 20, 1.0, ease=ease_linear)
    timeline.add(first)
    timeline.add(second)
    timeline.step(0.5)
    assert first.value == pytest.approx(5.0)
    assert second.value == pytest.approx(10.0)
    assert timeline.done is False


def test_timeline_done_when_all_complete() -> None:
    timeline = Timeline()
    timeline.add(Tween(0, 1, 0.1))
    timeline.add(Tween(0, 1, 0.2))
    timeline.step(1.0)
    assert timeline.done is True


def test_timeline_clear() -> None:
    timeline = Timeline()
    timeline.add(Tween(0, 1, 0.1))
    timeline.clear()
    assert timeline.done is True  # vacuously true when empty