"""Tests for the event vocabulary and queue."""

from __future__ import annotations

from windfall.events import KEY, QUIT, Event, EventQueue


def test_event_default_payload() -> None:
    event = Event(QUIT)
    assert event.kind == QUIT
    assert event.data == {}


def test_event_custom_payload() -> None:
    event = Event(KEY, {"key": "w"})
    assert event.data["key"] == "w"


def test_queue_post_poll_in_order() -> None:
    queue = EventQueue()
    first = Event(KEY, {"key": "a"})
    second = Event(KEY, {"key": "b"})
    queue.post(first)
    queue.post(second)
    assert queue.poll() is first
    assert queue.poll() is second
    assert queue.poll() is None


def test_queue_len() -> None:
    queue = EventQueue()
    assert len(queue) == 0
    queue.post(Event(QUIT))
    assert len(queue) == 1


def test_queue_drain() -> None:
    queue = EventQueue()
    queue.post(Event(KEY, {"key": "a"}))
    queue.post(Event(KEY, {"key": "b"}))
    drained = queue.drain()
    assert len(drained) == 2
    assert len(queue) == 0


def test_queue_clear() -> None:
    queue = EventQueue()
    queue.post(Event(QUIT))
    queue.clear()
    assert queue.poll() is None
    assert len(queue) == 0