"""Tests for scenes, frames, and the frame stack."""

from __future__ import annotations

from windfall.anim import Tween, ease_linear
from windfall.canvas import Canvas
from windfall.component import Component
from windfall.events import ACTIVATE, KEY, MOVE, Event
from windfall.geom import Rect, Vec2
from windfall.layout import Center, Column
from windfall.scene import Frame, FrameStack, Scene
from windfall.widgets import Button, Label, ListView, Panel


def move(direction: str) -> Event:
    return Event(MOVE, {"direction": direction})


class Updating(Component):
    def __init__(self) -> None:
        super().__init__()
        self.ticks = 0

    def size(self) -> Vec2:
        return Vec2(0, 0)

    def draw(self, canvas, rect: Rect) -> None:
        return None

    def update(self, dt: float) -> None:
        self.ticks += 1


class TestScene:
    def test_empty_scene_size_is_zero(self) -> None:
        assert Scene().size() == Vec2(0, 0)

    def test_size_comes_from_root(self) -> None:
        scene = Scene(root=ListView(items=["Alpha", "Beta"]))
        assert scene.size() == Vec2(7, 2)

    def test_update_reaches_children(self) -> None:
        counter = Updating()
        scene = Scene(root=Column().add(counter))
        scene.update(0.016)
        scene.update(0.016)
        assert counter.ticks == 2

    def test_update_steps_timeline(self) -> None:
        tween = Tween(0, 10, 1.0, ease=ease_linear)
        scene = Scene()
        scene.timeline.add(tween)
        scene.update(0.5)
        assert tween.value == 5.0

    def test_draw_renders_root(self) -> None:
        scene = Scene(root=Column().add(Label("hi")).add(Label("there")))
        canvas = Canvas(6, 2)
        scene.draw(canvas, Rect(0, 0, 6, 2))
        assert canvas.text() == ["hi    ", "there "]

    def test_scene_draw_of_widget_column(self) -> None:
        button = Button("OK", padding=0)
        button.focus(True)
        scene = Scene(root=Column().add(button).add(Label("x")))
        canvas = Canvas(6, 4)
        scene.draw(canvas, Rect(0, 0, 6, 4))
        assert canvas.text() == [
            "┌────┐",
            "│ OK │",
            "└────┘",
            "x     ",
        ]

    def test_arrow_focuses_first_widget_then_cycles(self) -> None:
        first = Button("A", padding=0)
        second = Button("B", padding=0)
        scene = Scene(root=Column().add(first).add(second))
        assert scene.handle(move("down")) is True
        assert first.focused is True
        scene.handle(move("down"))
        assert first.focused is False
        assert second.focused is True
        scene.handle(move("down"))
        assert first.focused is True
        scene.handle(move("up"))
        assert second.focused is True

    def test_arrows_move_focus_backwards_with_up(self) -> None:
        first = Button("A", padding=0)
        second = Button("B", padding=0)
        scene = Scene(root=Column().add(first).add(second))
        scene.handle(move("up"))  # no focus yet -> first gains focus
        assert first.focused
        scene.handle(move("up"))  # step -1 from first wraps to last
        assert second.focused

    def test_focused_list_consumes_arrows(self) -> None:
        view = ListView(items=["a", "b"])
        view.focus(True)
        scene = Scene(root=Column().add(view))
        assert scene.handle(move("down")) is True
        assert view.selection == 1
        assert view.focused is True  # scene did not steal focus

    def test_routes_activate_to_focused_button(self) -> None:
        calls: list[str] = []
        button = Button("GO", on_activate=lambda: calls.append("go"), padding=0)
        scene = Scene(root=Column().add(button))
        scene.handle(move("down"))
        assert scene.handle(Event(ACTIVATE)) is True
        assert calls == ["go"]

    def test_routes_activate_through_panel_and_box(self) -> None:
        calls: list[str] = []
        button = Button("GO", on_activate=lambda: calls.append("go"), padding=0)
        button.focus(True)
        dialog = Panel(button, title="title")
        root = Center()
        root.add(dialog)
        scene = Scene(root=root)
        assert scene.handle(Event(ACTIVATE)) is True
        assert calls == ["go"]

    def test_focus_cycle_finds_widget_inside_panel(self) -> None:
        first = Button("A", padding=0)
        second = Button("B", padding=0)
        panel = Panel(Column().add(first).add(second))
        scene = Scene(root=Column().add(panel))
        scene.handle(move("down"))
        assert first.focused is True
        scene.handle(move("down"))
        assert first.focused is False
        assert second.focused is True
        scene.handle(move("down"))
        assert first.focused is True

    def test_update_tick_reaches_widget_nested_in_panel(self) -> None:
        counter = Updating()
        scene = Scene(root=Column().add(Panel(counter)))
        scene.update(0.016)
        scene.update(0.016)
        assert counter.ticks == 2

    def test_focus_next_focuses_first_when_none_focused(self) -> None:
        first = Button("A", padding=0)
        scene = Scene(root=Column().add(first))
        scene.focus_next()
        assert first.focused is True

    def test_handle_returns_false_when_unhandled(self) -> None:
        scene = Scene()
        assert scene.handle(Event(KEY, {"key": "z"})) is False

    def test_focus_scope_traps_arrow_cycling_inside_editor(self) -> None:
        background = Button("App", padding=0)
        save = Button("Save", padding=0)
        cancel = Button("Cancel", padding=0)
        editor = Panel(Column().add(save).add(cancel), title="Header")
        scene = Scene(root=Column().add(background).add(editor))

        scene.handle(move("down"))
        assert background.focused is True

        scene.set_focus_scope(editor)
        assert background.focused is False
        assert save.focused is True

        scene.handle(move("down"))
        assert save.focused is False
        assert cancel.focused is True
        scene.handle(move("down"))
        assert save.focused is True
        assert background.focused is False

    def test_clear_focus_scope_restores_previous_focus(self) -> None:
        background = Button("App", padding=0)
        save = Button("Save", padding=0)
        editor = Panel(Column().add(save), title="Header")
        scene = Scene(root=Column().add(background).add(editor))

        scene.handle(move("down"))
        scene.set_focus_scope(editor)
        assert save.focused is True

        scene.clear_focus_scope()
        assert save.focused is False
        assert background.focused is True


class TestFrameStack:
    def test_frame_uses_scene_name(self) -> None:
        frame = Frame(Scene("menu"))
        assert frame.name == "menu"
        assert isinstance(frame.scene, Scene)

    def test_frame_empty_stack(self) -> None:
        stack = FrameStack()
        assert stack.current is None
        assert len(stack) == 0
        assert stack.pop() is None

    def test_push_and_current(self) -> None:
        stack = FrameStack()
        stack.push(Frame(Scene("menu")))
        stack.push(Frame(Scene("game")))
        assert stack.current.scene.name == "game"
        assert len(stack) == 2

    def test_pop_returns_top(self) -> None:
        stack = FrameStack()
        top = Frame(Scene("a"))
        stack.push(Frame(Scene("b")))
        stack.push(top)
        assert stack.pop() is top
        assert stack.current.scene.name == "b"

    def test_replace_swaps_top(self) -> None:
        stack = FrameStack()
        stack.push(Frame(Scene("a")))
        replacement = Frame(Scene("c"))
        stack.replace(replacement)
        assert stack.current is replacement
        assert len(stack) == 1

    def test_replace_on_empty_pushes(self) -> None:
        stack = FrameStack()
        frame = Frame(Scene("x"))
        stack.replace(frame)
        assert stack.current is frame