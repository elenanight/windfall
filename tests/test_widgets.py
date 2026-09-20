"""Tests for the interaction and rendering of widgets."""

from __future__ import annotations

from windfall.canvas import Canvas
from windfall.events import ACTIVATE, KEY, MOVE, Event
from windfall.geom import Rect, Vec2
from windfall.widgets import Button, Label, ListView, Panel, TextInput


def render(widget, width: int | None = None, height: int | None = None) -> list[str]:
    size = widget.size()
    width = width if width is not None else size.x
    height = height if height is not None else size.y
    canvas = Canvas(width, height)
    widget.draw(canvas, Rect(0, 0, width, height))
    return canvas.text()


def key(char: str) -> Event:
    return Event(KEY, {"key": char})


def move(direction: str) -> Event:
    return Event(MOVE, {"direction": direction})


class TestLabel:
    def test_size_matches_text(self) -> None:
        label = Label("hello")
        assert label.size() == Vec2(5, 1)

    def test_draw_renders_text(self) -> None:
        assert render(Label("hi")) == ["hi"]

    def test_set_text_updates(self) -> None:
        label = Label("aa")
        label.set_text("bbb")
        assert label.size() == Vec2(3, 1)
        assert render(label) == ["bbb"]


class TestButton:
    def test_focusable(self) -> None:
        assert Button("OK").focusable is True

    def test_size_includes_border_and_padding(self) -> None:
        assert Button("OK", padding=0).size() == Vec2(4, 3)
        assert Button("OK").size() == Vec2(6, 5)

    def test_activate_consumed_when_focused(self) -> None:
        calls: list[str] = []
        button = Button("OK", on_activate=lambda: calls.append("go"))
        button.focus(True)
        assert button.handle(Event(ACTIVATE)) is True
        assert calls == ["go"]

    def test_activate_ignored_when_not_focused(self) -> None:
        calls: list[str] = []
        button = Button("OK", on_activate=lambda: calls.append("go"))
        assert button.handle(Event(ACTIVATE)) is False
        assert calls == []

    def test_draw_frames_label(self) -> None:
        assert render(Button("OK", padding=0)) == [
            "┌──┐",
            "│OK│",
            "└──┘",
        ]

    def test_set_label(self) -> None:
        button = Button("AA", padding=0)
        button.set_label("BB")
        assert render(button) == [
            "┌──┐",
            "│BB│",
            "└──┘",
        ]


class TestPanel:
    def test_size_wraps_child(self) -> None:
        assert Panel(Label("body"), padding=0).size() == Vec2(6, 3)

    def test_draw_titles_and_frames_child(self) -> None:
        panel = Panel(Label("body"), title="Title", padding=1)
        assert render(panel) == [
            "┌─Title┐",
            "│      │",
            "│ body │",
            "│      │",
            "└──────┘",
        ]

    def test_set_title(self) -> None:
        panel = Panel(Label("x"), title="")
        panel.set_title("New")
        assert panel._title.size().x > 0


class TestTextInput:
    def test_default_value(self) -> None:
        assert TextInput().value == ""

    def test_ignores_keys_when_not_focused(self) -> None:
        field = TextInput()
        field.handle(key("a"))
        assert field.value == ""

    def test_types_when_focused(self) -> None:
        field = TextInput()
        field.focus(True)
        assert field.handle(key("a")) is True
        assert field.handle(key("b")) is True
        assert field.value == "ab"

    def test_backspace_deletes(self) -> None:
        field = TextInput("ab")
        field.focus(True)
        assert field.handle(key("\x7f")) is True
        assert field.value == "a"
        field.handle(key("\x7f"))
        assert field.value == ""

    def test_cursor_moves_left_and_right(self) -> None:
        field = TextInput("ab")
        field.focus(True)
        field.handle(move("left"))
        field.handle(key("X"))
        assert field.value == "aXb"

    def test_submit_on_activate(self) -> None:
        submitted: list[str] = []
        field = TextInput("hey", on_submit=submitted.append)
        field.focus(True)
        assert field.handle(Event(ACTIVATE)) is True
        assert submitted == ["hey"]

    def test_draw_shows_text_and_cursor(self) -> None:
        field = TextInput("hi")
        field.focus(True)
        field.handle(move("left"))
        field.handle(move("left"))
        assert render(field) == ["┌──┐", "│▮i│", "└──┘"]


class TestListView:
    def test_focusable(self) -> None:
        assert ListView(items=["a"]).focusable is True

    def test_size_uses_longest_item(self) -> None:
        view = ListView(items=["a", "bbb"])
        assert view.size() == Vec2(5, 2)

    def test_arrow_keys_navigate_selection(self) -> None:
        view = ListView(items=["a", "b", "c"])
        view.focus(True)
        view.handle(move("down"))
        assert view.selection == 1
        view.handle(move("down"))
        assert view.selection == 2
        view.handle(move("down"))
        assert view.selection == 2  # clamped
        view.handle(move("up"))
        assert view.selection == 1

    def test_arrow_keys_ignored_when_not_focused(self) -> None:
        view = ListView(items=["a", "b"])
        assert view.handle(move("down")) is False
        assert view.selection == 0

    def test_activate_selects_item(self) -> None:
        picks: list[tuple] = []
        view = ListView(items=["a", "b"], on_select=lambda item, index: picks.append((item, index)))
        view.focus(True)
        view.handle(move("down"))
        assert view.handle(Event(ACTIVATE)) is True
        assert picks == [("b", 1)]

    def test_set_items_resets_selection(self) -> None:
        view = ListView(items=["a", "b"])
        view.focus(True)
        view.handle(move("down"))
        view.set_items(["x"])
        assert view.selection == 0
        assert view.size() == Vec2(3, 1)

    def test_draw_marks_selection(self) -> None:
        view = ListView(items=["Alpha", "Beta", "Gamma"])
        view.focus(True)
        assert render(view) == ["▸ Alpha", "  Beta ", "  Gamma"]

    def test_draw_highlight_is_styled(self) -> None:
        view = ListView(items=["Alpha", "Beta"])
        view.focus(True)
        canvas = Canvas(7, 2)
        view.draw(canvas, Rect(0, 0, 7, 2))
        assert canvas.to_rich().spans