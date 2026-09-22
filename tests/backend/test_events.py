"""Tests for the event vocabulary and queue."""

from __future__ import annotations

from windfall.events import KEY, QUIT, Event, EventQueue


class TestEvent:
    def test_default_payload(self) -> None:
        event = Event(QUIT)
        assert event.kind == QUIT
        assert event.data == {}

    def test_custom_payload(self) -> None:
        event = Event(KEY, {"key": "w"})
        assert event.data["key"] == "w"


class TestEventQueue:
    def test_post_poll_in_order(self) -> None:
        queue = EventQueue()
        first = Event(KEY, {"key": "a"})
        second = Event(KEY, {"key": "b"})
        queue.post(first)
        queue.post(second)
        assert queue.poll() is first
        assert queue.poll() is second
        assert queue.poll() is None

    def test_len(self) -> None:
        queue = EventQueue()
        assert len(queue) == 0
        queue.post(Event(QUIT))
        assert len(queue) == 1

    def test_drain(self) -> None:
        queue = EventQueue()
        queue.post(Event(KEY, {"key": "a"}))
        queue.post(Event(KEY, {"key": "b"}))
        drained = queue.drain()
        assert len(drained) == 2
        assert len(queue) == 0

    def test_clear(self) -> None:
        queue = EventQueue()
        queue.post(Event(QUIT))
        queue.clear()
        assert queue.poll() is None
        assert len(queue) == 0