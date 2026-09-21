"""Tests for the interaction and rendering of widgets."""

from __future__ import annotations

from windfall.canvas import Canvas
from windfall.events import ACTIVATE, KEY, MOVE, Event
from windfall.geom import Rect, Vec2
from windfall.layout import Column
from windfall.primitives import Connector
from windfall.scene import Scene, focusables
from windfall.widgets import (
    BORDER_COLORS,
    TEXT_COLORS,
    AddWidget,
    Button,
    Footer,
    FooterEditor,
    Header,
    HeaderEditor,
    Hotkey,
    Label,
    ListView,
    Panel,
    RemoveWidget,
    TextInput,
)


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

    def test_focused_label_carries_highlight(self) -> None:
        button = Button("OK", padding=0)
        button.focus(True)
        canvas = Canvas(4, 3)
        button.draw(canvas, Rect(0, 0, 4, 3))
        spans = canvas.to_rich().spans
        assert any(span.style is not None and span.style.bgcolor for span in spans)


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

    def test_focused_text_carries_highlight(self) -> None:
        field = TextInput("hi")
        field.focus(True)
        canvas = Canvas(4, 3)
        field.draw(canvas, Rect(0, 0, 4, 3))
        spans = canvas.to_rich().spans
        assert any(span.style is not None and span.style.bgcolor for span in spans)


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

    def test_select_clamps_and_ignores_empty(self) -> None:
        view = ListView(items=["a", "b"])
        view.select(9)
        assert view.selection == 1
        view.select(-4)
        assert view.selection == 0
        ListView().select(3)  # no items: no crash

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


class TestHeader:
    def test_not_focusable(self) -> None:
        assert Header("hi").focusable is False

    def test_size_wraps_label(self) -> None:
        assert Header("hi").size() == Vec2(4, 3)

    def test_draw_frames_centered_label(self) -> None:
        assert render(Header("hi")) == [
            "┌──┐",
            "│hi│",
            "└──┘",
        ]

    def test_set_text_updates(self) -> None:
        header = Header("aa")
        header.set_text("b")
        assert header.size() == Vec2(3, 3)
        assert render(header) == [
            "┌─┐",
            "│b│",
            "└─┘",
        ]

    def test_set_colors_keeps_text(self) -> None:
        header = Header("hi", border="red", fg="green")
        header.set_colors(border="blue", fg="yellow")
        assert render(header) == [
            "┌──┐",
            "│hi│",
            "└──┘",
        ]


def _editor_buttons(editor: HeaderEditor) -> list[Button]:
    return [w for w in focusables(editor) if isinstance(w, Button)]


def _find_all(node, kind: type) -> list:
    """Walk a component tree the way event delivery does (children/box/child)."""
    found = [node] if isinstance(node, kind) else []
    for attr in ("children", "_box", "_child"):
        value = getattr(node, attr, None)
        if value is None:
            continue
        for kid in value if isinstance(value, list) else [value]:
            found.extend(_find_all(kid, kind))
    return found


def _hosted(editor: HeaderEditor) -> Scene:
    return Scene(root=Column().add(editor))


class TestHeaderEditor:
    def test_preselects_given_colors(self) -> None:
        editor = HeaderEditor(text="Hi", border="red", fg="bright_green")
        views = [w for w in focusables(editor) if isinstance(w, ListView)]
        assert views[0].selection == BORDER_COLORS.index("red")
        assert views[1].selection == TEXT_COLORS.index("bright_green")

    def test_save_delivers_text_and_colors(self) -> None:
        saved: list[tuple] = []
        editor = HeaderEditor(
            text="Hi",
            border="red",
            fg="bright_green",
            on_save=lambda text, border, fg: saved.append((text, border, fg)),
        )
        save, _ = _editor_buttons(editor)
        save.focus(True)
        assert _hosted(editor).handle(Event(ACTIVATE)) is True
        assert saved == [("Hi", "red", "bright_green")]

    def test_save_follows_moved_selection(self) -> None:
        saved: list[tuple] = []
        editor = HeaderEditor(
            text="Hi",
            border="red",
            fg="bright_green",
            on_save=lambda text, border, fg: saved.append((text, border, fg)),
        )
        views = [w for w in focusables(editor) if isinstance(w, ListView)]
        views[0].focus(True)
        views[0].handle(move("down"))
        views[0].focus(False)
        save, _ = _editor_buttons(editor)
        save.focus(True)
        _hosted(editor).handle(Event(ACTIVATE))
        assert saved[0][1] == BORDER_COLORS[BORDER_COLORS.index("red") + 1]

    def test_cancel_calls_on_cancel_only(self) -> None:
        saved: list[tuple] = []
        cancelled: list[bool] = []
        editor = HeaderEditor(
            text="Hi",
            on_save=lambda text, border, fg: saved.append((text, border, fg)),
            on_cancel=lambda: cancelled.append(True),
        )
        _, cancel = _editor_buttons(editor)
        cancel.focus(True)
        assert _hosted(editor).handle(Event(ACTIVATE)) is True
        assert cancelled == [True]
        assert saved == []

    def test_empty_text_falls_back_to_initial(self) -> None:
        saved: list[tuple] = []
        editor = HeaderEditor(
            text="Hi", on_save=lambda text, border, fg: saved.append((text, border, fg))
        )
        fields = [w for w in focusables(editor) if isinstance(w, TextInput)]
        fields[0].focus(True)
        fields[0].handle(key("\x7f"))
        fields[0].handle(key("\x7f"))
        fields[0].focus(False)
        save, _ = _editor_buttons(editor)
        save.focus(True)
        _hosted(editor).handle(Event(ACTIVATE))
        assert saved[0][0] == "Hi"

    def test_links_boxes_with_available_shafts(self) -> None:
        shafts = _find_all(HeaderEditor(text="Hi"), Connector)
        assert len(shafts) == 3
        assert all(shaft.state == "available" for shaft in shafts)


class TestFooter:
    def test_not_focusable(self) -> None:
        assert Footer("hi").focusable is False

    def test_size_wraps_label(self) -> None:
        assert Footer("hi").size() == Vec2(4, 3)

    def test_draw_frames_centered_label(self) -> None:
        assert render(Footer("hi")) == [
            "┌──┐",
            "│hi│",
            "└──┘",
        ]

    def test_set_text_and_colors(self) -> None:
        footer = Footer("aa")
        footer.set_text("b")
        footer.set_colors(border="blue", fg="yellow")
        assert footer.size() == Vec2(3, 3)
        assert render(footer) == [
            "┌─┐",
            "│b│",
            "└─┘",
        ]


class TestFooterEditor:
    def test_preselects_given_colors(self) -> None:
        editor = FooterEditor(text="Bye", border="magenta", fg="yellow")
        views = [w for w in focusables(editor) if isinstance(w, ListView)]
        assert views[0].selection == BORDER_COLORS.index("magenta")
        assert views[1].selection == TEXT_COLORS.index("yellow")

    def test_save_delivers_text_and_colors(self) -> None:
        saved: list[tuple] = []
        editor = FooterEditor(
            text="Bye",
            border="magenta",
            fg="yellow",
            on_save=lambda text, border, fg: saved.append((text, border, fg)),
        )
        save, _ = _editor_buttons(editor)
        save.focus(True)
        assert _hosted(editor).handle(Event(ACTIVATE)) is True
        assert saved == [("Bye", "magenta", "yellow")]

    def test_cancel_calls_on_cancel_only(self) -> None:
        saved: list[tuple] = []
        cancelled: list[bool] = []
        editor = FooterEditor(
            text="Bye",
            on_save=lambda text, border, fg: saved.append((text, border, fg)),
            on_cancel=lambda: cancelled.append(True),
        )
        _, cancel = _editor_buttons(editor)
        cancel.focus(True)
        assert _hosted(editor).handle(Event(ACTIVATE)) is True
        assert cancelled == [True]
        assert saved == []

    def test_links_boxes_with_available_shafts(self) -> None:
        shafts = _find_all(FooterEditor(text="Bye"), Connector)
        assert len(shafts) == 3
        assert all(shaft.state == "available" for shaft in shafts)


class TestAddWidget:
    def test_save_delivers_kind_and_placement(self) -> None:
        added: list[tuple] = []
        editor = AddWidget(on_add=lambda kind, placement: added.append((kind, placement)))
        kinds, places = [w for w in focusables(editor) if isinstance(w, ListView)]
        kinds.focus(True)
        kinds.handle(move("down"))
        kinds.handle(move("down"))
        kinds.focus(False)
        places.focus(True)
        for _ in range(4):
            places.handle(move("down"))
        places.focus(False)
        save, _ = _editor_buttons(editor)
        save.focus(True)
        assert _hosted(editor).handle(Event(ACTIVATE)) is True
        assert added == [("TextInput", "sidebar")]

    def test_cancel_calls_on_cancel_only(self) -> None:
        added: list[tuple] = []
        cancelled: list[bool] = []
        editor = AddWidget(
            on_add=lambda kind, placement: added.append((kind, placement)),
            on_cancel=lambda: cancelled.append(True),
        )
        _, cancel = _editor_buttons(editor)
        cancel.focus(True)
        assert _hosted(editor).handle(Event(ACTIVATE)) is True
        assert cancelled == [True]
        assert added == []


class TestRemoveWidget:
    def test_commit_delivers_selected_index(self) -> None:
        removed: list[int] = []
        editor = RemoveWidget(
            ["Label · left", "Button · full"], on_remove=removed.append
        )
        views = [w for w in focusables(editor) if isinstance(w, ListView)]
        views[0].focus(True)
        views[0].handle(move("down"))
        views[0].focus(False)
        remove, _ = _editor_buttons(editor)
        remove.focus(True)
        assert _hosted(editor).handle(Event(ACTIVATE)) is True
        assert removed == [1]

    def test_cancel_calls_on_cancel_only(self) -> None:
        removed: list[int] = []
        cancelled: list[bool] = []
        editor = RemoveWidget(
            ["Label · left"],
            on_remove=removed.append,
            on_cancel=lambda: cancelled.append(True),
        )
        _, cancel = _editor_buttons(editor)
        cancel.focus(True)
        assert _hosted(editor).handle(Event(ACTIVATE)) is True
        assert cancelled == [True]
        assert removed == []

    def test_empty_entries_remove_is_noop(self) -> None:
        removed: list[int] = []
        editor = RemoveWidget([], on_remove=removed.append)
        remove, _ = _editor_buttons(editor)
        remove.focus(True)
        assert _hosted(editor).handle(Event(ACTIVATE)) is True
        assert removed == []


class TestHotkey:
    def test_not_focusable_and_zero_size(self) -> None:
        hotkey = Hotkey("e")
        assert hotkey.focusable is False
        assert hotkey.size() == Vec2(0, 0)

    def test_draw_is_noop(self) -> None:
        canvas = Canvas(3, 1)
        Hotkey("e").draw(canvas, Rect(0, 0, 3, 1))
        assert canvas.text() == ["   "]

    def test_fires_on_matching_key(self) -> None:
        pressed: list[bool] = []
        hotkey = Hotkey("e", on_press=lambda: pressed.append(True))
        assert hotkey.handle(key("e")) is True
        assert hotkey.handle(key("E")) is True
        assert pressed == [True, True]

    def test_ignores_other_keys_and_events(self) -> None:
        pressed: list[bool] = []
        hotkey = Hotkey("e", on_press=lambda: pressed.append(True))
        assert hotkey.handle(key("q")) is False
        assert hotkey.handle(move("down")) is False
        assert hotkey.handle(Event(ACTIVATE)) is False
        assert pressed == []

    def test_missing_callback_is_safe(self) -> None:
        assert Hotkey("e").handle(key("e")) is True