"""Reusable interactive widgets assembled from primitives."""

from __future__ import annotations

from windfall.component import Component
from windfall.events import ACTIVATE, KEY, MOVE, Event
from windfall.geom import Rect, Vec2
from windfall.layout import Column, Row
from windfall.primitives import Border, Box, Connector, Text
from windfall.style import Style

_HIGHLIGHT = Style(bg="bright_blue")
_BLOCK = "\u25ae"


class Label(Component):
    """Non-interactive text; the palette-down equivalent of a ``Text``."""

    def __init__(self, text: str, style: Style | None = None, align: str = "left") -> None:
        super().__init__()
        self._text = Text(text, style=style, align=align)

    def size(self) -> Vec2:
        return self._text.size()

    def draw(self, canvas, rect: Rect) -> None:
        self._text.draw(canvas, rect)

    def set_text(self, text: str) -> None:
        self._text.set_text(text)


class Header(Component):
    """A full-width bar assembled from a bordered box and a styled label."""

    def __init__(self, text: str = "", *, border: str | None = "cyan", fg: str | None = "white") -> None:
        super().__init__()
        self._text = text
        self._border = border
        self._fg = fg
        self._label = Label(text, style=Style(fg=fg), align="center")
        self._box = Box(self._label, border_style=Style(fg=border), padding=0)

    def size(self) -> Vec2:
        return self._box.size()

    def draw(self, canvas, rect: Rect) -> None:
        self._box.draw(canvas, rect)

    def set_text(self, text: str) -> None:
        self._text = text
        self._label.set_text(text)

    def set_colors(self, *, border: str | None = None, fg: str | None = None) -> None:
        if border is not None:
            self._border = border
        if fg is not None:
            self._fg = fg
        self._label = Label(self._text, style=Style(fg=self._fg), align="center")
        self._box = Box(self._label, border_style=Style(fg=self._border), padding=0)


class Footer(Component):
    """A full-width bar for the bottom of the screen, mirroring ``Header``."""

    def __init__(self, text: str = "", *, border: str | None = "cyan", fg: str | None = "white") -> None:
        super().__init__()
        self._text = text
        self._border = border
        self._fg = fg
        self._label = Label(text, style=Style(fg=fg), align="center")
        self._box = Box(self._label, border_style=Style(fg=border), padding=0)

    def size(self) -> Vec2:
        return self._box.size()

    def draw(self, canvas, rect: Rect) -> None:
        self._box.draw(canvas, rect)

    def set_text(self, text: str) -> None:
        self._text = text
        self._label.set_text(text)

    def set_colors(self, *, border: str | None = None, fg: str | None = None) -> None:
        if border is not None:
            self._border = border
        if fg is not None:
            self._fg = fg
        self._label = Label(self._text, style=Style(fg=self._fg), align="center")
        self._box = Box(self._label, border_style=Style(fg=self._border), padding=0)


class Button(Component):
    """A focusable, activating, bordered button."""

    def __init__(
        self,
        label: str,
        on_activate=None,
        style: Style | None = None,
        border_style: Style | None = None,
        padding: int = 1,
    ) -> None:
        super().__init__()
        self.focusable = True
        self._text = label
        self._label = Text(label, align="center", style=style)
        self._border = Border(border_style)
        self._style = style
        self._padding = padding
        self.on_activate = on_activate

    def size(self) -> Vec2:
        inner = self._label.size()
        ring = 1 + self._padding
        return Vec2(inner.x + 2 * ring, inner.y + 2 * ring)

    def draw(self, canvas, rect: Rect) -> None:
        inner = rect.inset(1 + self._padding)
        if self.focused and inner.width > 0 and inner.height > 0:
            canvas.fill(rect.x, rect.y, rect.width, rect.height, " ", _HIGHLIGHT)
        if inner.width > 0 and inner.height > 0:
            if self.focused:
                base = self._style if self._style is not None else Style()
                text_style = base.merge(_HIGHLIGHT)
            else:
                text_style = self._style
            Text(self._text, align="center", style=text_style).draw(canvas, inner)
        self._border.draw(canvas, rect)

    def handle(self, event: Event) -> bool:
        if event.kind != ACTIVATE or not self.focused:
            return False
        if self.on_activate is not None:
            self.on_activate()
        return True

    def set_label(self, label: str) -> None:
        self._text = label
        self._label = Text(label, align="center", style=self._style)


class Panel(Component):
    """A titled box that frames a single child component."""

    def __init__(
        self,
        child: Component,
        title: str = "",
        style: Style | None = None,
        border_style: Style | None = None,
        padding: int = 1,
    ) -> None:
        super().__init__()
        self._box = Box(child, style=style, border_style=border_style, padding=padding)
        self._title = Text(title)

    def size(self) -> Vec2:
        return self._box.size()

    def draw(self, canvas, rect: Rect) -> None:
        self._box.draw(canvas, rect)
        if self._title.size().x > 0:
            self._title.draw(canvas, Rect(rect.x + 2, rect.y, max(0, rect.width - 2), 1))

    def set_title(self, title: str) -> None:
        self._title.set_text(title)


class TextInput(Component):
    """A single-line, focusable text field with a block cursor."""

    def __init__(
        self,
        value: str = "",
        on_submit=None,
        style: Style | None = None,
        border_style: Style | None = None,
    ) -> None:
        super().__init__()
        self.focusable = True
        self._text = value
        self._cursor = len(value)
        self._style = style
        self._border = Border(border_style)
        self.on_submit = on_submit

    def size(self) -> Vec2:
        return Vec2(len(self._text) + 2, 3)

    def draw(self, canvas, rect: Rect) -> None:
        self._border.draw(canvas, rect)
        inner = rect.inset(1)
        if inner.width <= 0 or inner.height <= 0:
            return
        if self.focused:
            canvas.fill(inner.x, inner.y, inner.width, inner.height, " ", _HIGHLIGHT)
            base = self._style if self._style is not None else Style()
            text_style = base.merge(_HIGHLIGHT)
        else:
            text_style = self._style
        canvas.write(self._text[: inner.width], inner.x, inner.y, text_style)
        if self.focused and inner.width > 0:
            cursor_column = min(self._cursor, inner.width - 1)
            canvas.write(_BLOCK, inner.x + cursor_column, inner.y, text_style)

    def handle(self, event: Event) -> bool:
        if not self.focused:
            return False
        if event.kind == KEY:
            key = event.data.get("key", "")
            if key in ("\x7f", "\b") and self._cursor > 0:
                self._text = self._text[: self._cursor - 1] + self._text[self._cursor :]
                self._cursor -= 1
                return True
            if len(key) == 1 and key.isprintable():
                self._text = self._text[: self._cursor] + key + self._text[self._cursor :]
                self._cursor += 1
                return True
            return False
        if event.kind == MOVE:
            direction = event.data.get("direction")
            if direction == "left":
                self._cursor = max(0, self._cursor - 1)
                return True
            if direction == "right":
                self._cursor = min(len(self._text), self._cursor + 1)
                return True
            return False
        if event.kind == ACTIVATE:
            if self.on_submit is not None:
                self.on_submit(self._text)
            return True
        return False

    @property
    def value(self) -> str:
        return self._text


class ListView(Component):
    """A focusable list of options with keyboard navigation."""

    def __init__(self, items=None, on_select=None, style: Style | None = None) -> None:
        super().__init__()
        self.focusable = True
        self._items = list(items or [])
        self._selected = 0
        self._style = style
        self.on_select = on_select

    def size(self) -> Vec2:
        if not self._items:
            return Vec2(0, 0)
        width = max(len(item) for item in self._items) + 2
        return Vec2(width, len(self._items))

    def draw(self, canvas, rect: Rect) -> None:
        if not self._items:
            return
        top = min(max(0, self._selected), max(0, len(self._items) - rect.height))
        for row in range(rect.height):
            index = top + row
            if index >= len(self._items):
                break
            y = rect.y + row
            selected = index == self._selected
            row_style = _HIGHLIGHT if selected and self.focused else self._style
            if selected and self.focused:
                canvas.fill(rect.x, y, rect.width, 1, " ", _HIGHLIGHT)
            Text(f"{'▸' if selected else ' '} {self._items[index]}", style=row_style).draw(
                canvas, Rect(rect.x, y, rect.width, 1)
            )

    def handle(self, event: Event) -> bool:
        if not self.focused or not self._items:
            return False
        if event.kind == MOVE:
            direction = event.data.get("direction")
            if direction == "down":
                self._selected = min(len(self._items) - 1, self._selected + 1)
                return True
            if direction == "up":
                self._selected = max(0, self._selected - 1)
                return True
            return False
        if event.kind == ACTIVATE:
            if self.on_select is not None:
                self.on_select(self._items[self._selected], self._selected)
            return True
        return False

    def set_items(self, items: list[str]) -> None:
        self._items = list(items or [])
        self._selected = 0

    def select(self, index: int) -> None:
        if not self._items:
            return
        self._selected = max(0, min(index, len(self._items) - 1))

    @property
    def selection(self) -> int:
        return self._selected


BORDER_COLORS = ("cyan", "blue", "magenta", "green", "yellow", "red", "white")
TEXT_COLORS = (
    "bright_white",
    "white",
    "bright_cyan",
    "bright_yellow",
    "bright_green",
    "bright_magenta",
    "yellow",
)


def _index_of(choices: list[str], value: str | None) -> int:
    try:
        return choices.index(value)
    except ValueError:
        return 0


def _pad_equal(*lists: list[str]) -> list[list[str]]:
    """Pad choice lists to a shared width so side-by-side lists split evenly."""
    width = max((len(item) for choices in lists for item in choices), default=0)
    return [[item.ljust(width) for item in choices] for choices in lists]


class HeaderEditor(Panel):
    """In-place editor panel for header text and colors.

    A ``Panel`` subclass wrapping a full-width ``TextInput``, side-by-side
    curated-color ``ListView``s, a visibility toggle, and Update/Cancel
    buttons. ``on_save`` receives ``(text, border, fg, visible)``;
    ``on_cancel`` takes no arguments. Lists preselect the given values.
    Events reach the nested widgets through the inherited panel/box
    traversal.
    """

    def __init__(
        self,
        *,
        text: str = "",
        border: str = "cyan",
        fg: str = "white",
        visible: bool = True,
        border_choices=None,
        text_choices=None,
        on_save=None,
        on_cancel=None,
        title: str = "Edit header bar",
    ) -> None:
        self._text = text
        self._border_choices = list(border_choices or BORDER_COLORS)
        self._text_choices = list(text_choices or TEXT_COLORS)
        self.on_save = on_save
        self.on_cancel = on_cancel
        self._field = TextInput(text)
        border_shown, fg_shown, vis_shown = _pad_equal(
            self._border_choices, self._text_choices, ["Yes", "No"]
        )
        self._borders = ListView(items=border_shown)
        self._borders.select(_index_of(self._border_choices, border))
        self._fgs = ListView(items=fg_shown)
        self._fgs.select(_index_of(self._text_choices, fg))
        self._visible = ListView(items=vis_shown)
        self._visible.select(0 if visible else 1)
        body = Column()
        body.add(Label("Header text:"))
        body.add(self._field)
        body.add(Connector("available"))
        thirds = Row(fill=True)
        left = Column()
        left.add(Label("Border:"))
        left.add(self._borders)
        middle = Column()
        middle.add(Label("Text:"))
        middle.add(self._fgs)
        right = Column()
        right.add(Label("Visible:"))
        right.add(self._visible)
        thirds.add(left)
        thirds.add(middle)
        thirds.add(right)
        body.add(thirds)
        body.add(Connector("available"))
        actions = Row()
        actions.add(Button("Update", on_activate=self._commit))
        actions.add(Button("Cancel", on_activate=self._abort))
        body.add(actions)
        super().__init__(body, title=title, padding=1)

    def _commit(self) -> None:
        text = self._field.value.strip() or self._text
        border = self._border_choices[self._borders.selection]
        fg = self._text_choices[self._fgs.selection]
        visible = self._visible.selection == 0
        if self.on_save is not None:
            self.on_save(text, border, fg, visible)

    def _abort(self) -> None:
        if self.on_cancel is not None:
            self.on_cancel()


class FooterEditor(Panel):
    """In-place editor panel for footer text and colors, mirroring ``HeaderEditor``."""

    def __init__(
        self,
        *,
        text: str = "",
        border: str = "cyan",
        fg: str = "white",
        visible: bool = True,
        border_choices=None,
        text_choices=None,
        on_save=None,
        on_cancel=None,
        title: str = "Edit footer bar",
    ) -> None:
        self._text = text
        self._border_choices = list(border_choices or BORDER_COLORS)
        self._text_choices = list(text_choices or TEXT_COLORS)
        self.on_save = on_save
        self.on_cancel = on_cancel
        self._field = TextInput(text)
        border_shown, fg_shown, vis_shown = _pad_equal(
            self._border_choices, self._text_choices, ["Yes", "No"]
        )
        self._borders = ListView(items=border_shown)
        self._borders.select(_index_of(self._border_choices, border))
        self._fgs = ListView(items=fg_shown)
        self._fgs.select(_index_of(self._text_choices, fg))
        self._visible = ListView(items=vis_shown)
        self._visible.select(0 if visible else 1)
        body = Column()
        body.add(Label("Footer text:"))
        body.add(self._field)
        body.add(Connector("available"))
        thirds = Row(fill=True)
        left = Column()
        left.add(Label("Border:"))
        left.add(self._borders)
        middle = Column()
        middle.add(Label("Text:"))
        middle.add(self._fgs)
        right = Column()
        right.add(Label("Visible:"))
        right.add(self._visible)
        thirds.add(left)
        thirds.add(middle)
        thirds.add(right)
        body.add(thirds)
        body.add(Connector("available"))
        actions = Row()
        actions.add(Button("Update", on_activate=self._commit))
        actions.add(Button("Cancel", on_activate=self._abort))
        body.add(actions)
        super().__init__(body, title=title, padding=1)

    def _commit(self) -> None:
        text = self._field.value.strip() or self._text
        border = self._border_choices[self._borders.selection]
        fg = self._text_choices[self._fgs.selection]
        visible = self._visible.selection == 0
        if self.on_save is not None:
            self.on_save(text, border, fg, visible)

    def _abort(self) -> None:
        if self.on_cancel is not None:
            self.on_cancel()


class Hotkey(Component):
    """A non-visual key binding that fires when its key is pressed.

    Matching is case-insensitive, so ``"e"`` fires on both ``e`` and ``E``.
    Place it after text inputs in a container so typing takes precedence:
    a focused input consumes its keys before delivery reaches the hotkey.
    """

    def __init__(self, key: str = "", on_press=None) -> None:
        super().__init__()
        self._key = key
        self.on_press = on_press

    def size(self) -> Vec2:
        return Vec2(0, 0)

    def draw(self, canvas, rect: Rect) -> None:
        return None

    def handle(self, event: Event) -> bool:
        key = event.data.get("key", "")
        if event.kind != KEY or key.lower() != self._key.lower():
            return False
        if self.on_press is not None:
            self.on_press()
        return True


WIDGET_KINDS = ("Label", "Button", "TextInput", "ListView", "Divider")
PLACEMENTS = ("left", "center", "right", "full", "sidebar")
STRETCH = ("No", "Yes")


class AddWidget(Panel):
    """Palette panel for dropping a widget into the content section.

    Offers a curated widget list, a placement list (left, center, right,
    full width, or sidebar), and a stretch option. ``on_add`` receives
    ``(kind, placement, stretch)``; ``on_cancel`` takes no arguments.
    ``fits`` optionally validates ``(kind, placement, stretch)`` and
    returns a refusal reason (or ``None``); on refusal the palette stays
    open showing the reason in its status line.
    """

    def __init__(
        self,
        *,
        on_add=None,
        on_cancel=None,
        fits=None,
        title: str = "Add widget",
    ) -> None:
        self._kinds = list(WIDGET_KINDS)
        self._placements = list(PLACEMENTS)
        self._stretch_choices = list(STRETCH)
        self.on_add = on_add
        self.on_cancel = on_cancel
        self._fits = fits
        self._status = Label("")
        kind_shown, place_shown, stretch_shown = _pad_equal(
            self._kinds, self._placements, self._stretch_choices
        )
        self._types = ListView(items=kind_shown)
        self._places = ListView(items=place_shown)
        self._stretch = ListView(items=stretch_shown)
        halves = Row(fill=True)
        left = Column()
        left.add(Label("Widget:"))
        left.add(self._types)
        middle = Column()
        middle.add(Label("Placement:"))
        middle.add(self._places)
        right = Column()
        right.add(Label("Stretch:"))
        right.add(self._stretch)
        halves.add(left)
        halves.add(middle)
        halves.add(right)
        body = Column()
        body.add(halves)
        body.add(Connector("available"))
        actions = Row()
        actions.add(Button("Add", on_activate=self._commit))
        actions.add(Button("Cancel", on_activate=self._abort))
        body.add(actions)
        body.add(self._status)
        super().__init__(body, title=title, padding=1)

    def _commit(self) -> None:
        kind = self._kinds[self._types.selection]
        placement = self._placements[self._places.selection]
        stretch = self._stretch.selection == 1
        if self._fits is not None:
            reason = self._fits(kind, placement, stretch)
            if reason:
                self._status.set_text(reason)
                return
        if self.on_add is not None:
            self.on_add(kind, placement, stretch)

    def preset(self, kind: str, placement: str, stretch: bool) -> None:
        """Preselect lists for editing an existing placement."""
        self._types.select(_index_of(self._kinds, kind))
        self._places.select(_index_of(self._placements, placement))
        self._stretch.select(1 if stretch else 0)

    def _abort(self) -> None:
        if self.on_cancel is not None:
            self.on_cancel()


class RemoveWidget(Panel):
    """Palette panel listing placed widgets for removal.

    Entries are human-readable ``"Kind · placement"`` strings. ``on_remove``
    receives the selected entry index; ``on_cancel`` takes no arguments.
    With no entries the list shows a placeholder and Remove does nothing.
    """

    def __init__(
        self,
        entries=None,
        *,
        on_remove=None,
        on_cancel=None,
        title: str = "Remove widget",
    ) -> None:
        self._entries = list(entries or [])
        self.on_remove = on_remove
        self.on_cancel = on_cancel
        self._list = ListView(items=self._entries or ["(no widgets placed)"])
        body = Column()
        body.add(Label("Placed widgets:"))
        body.add(self._list)
        body.add(Connector("available"))
        actions = Row()
        actions.add(Button("Remove", on_activate=self._commit))
        actions.add(Button("Cancel", on_activate=self._abort))
        body.add(actions)
        super().__init__(body, title=title, padding=1)

    def _commit(self) -> None:
        if not self._entries:
            return
        if self.on_remove is not None:
            self.on_remove(self._list.selection)

    def _abort(self) -> None:
        if self.on_cancel is not None:
            self.on_cancel()


class EditMenu(Panel):
    """Drill-down list of editable things: bars first, then placed widgets.

    Entries are display strings; ``on_pick`` receives the selected index
    and ``on_cancel`` takes no arguments. Picking fires straight from the
    list, so there is no confirm button — just Cancel.
    """

    def __init__(
        self,
        entries=None,
        *,
        on_pick=None,
        on_cancel=None,
        title: str = "Edit",
    ) -> None:
        self._entries = list(entries or [])
        self.on_pick = on_pick
        self.on_cancel = on_cancel
        self._list = ListView(
            items=self._entries or ["(nothing to edit)"],
            on_select=self._pick,
        )
        body = Column()
        body.add(Label("What to edit:"))
        body.add(self._list)
        body.add(Connector("available"))
        actions = Row()
        actions.add(Button("Cancel", on_activate=self._abort))
        body.add(actions)
        super().__init__(body, title=title, padding=1)

    def _pick(self, item: str, index: int) -> None:
        if not self._entries:
            return
        if self.on_pick is not None:
            self.on_pick(index)

    def _abort(self) -> None:
        if self.on_cancel is not None:
            self.on_cancel()