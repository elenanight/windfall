"""@@package@@ — a windfall app scaffolded with `windfall new`."""

from pathlib import Path

import windfall
from windfall import (
    AddWidget,
    Button,
    Center,
    Column,
    Config,
    Connector,
    Engine,
    FooterEditor,
    HeaderEditor,
    Hotkey,
    Label,
    Panel,
    RemoveWidget,
    Row,
    Scene,
    Stack,
)
from windfall.scene import focusables

CONFIG_PATH = Path(__file__).resolve().parent / ".windfallrc.json"

DEFAULTS = {
    "header": "hello from @@package@@!",
    "border": "cyan",
    "fg": "bright_white",
    "footer": "built with windfall",
    "footer_border": "cyan",
    "footer_fg": "white",
    "widgets": [],
}


def windfall_home() -> Path | None:
    """Locate the Windfall checkout backing this app, if it runs from one."""
    init = getattr(windfall, "__file__", None)
    if not init:
        return None
    root = Path(init).resolve().parent.parent
    return root if (root / "pyproject.toml").is_file() else None


def build(engine: Engine) -> Scene:
    """Assemble the app scene: header, menu, content, and footer bars."""
    cfg = Config.load(CONFIG_PATH, defaults=DEFAULTS)
    header = engine.make_header(cfg.get("header"), border=cfg.get("border"), fg=cfg.get("fg"))
    footer = engine.make_footer(
        cfg.get("footer"), border=cfg.get("footer_border"), fg=cfg.get("footer_fg")
    )
    add = Button("Add widget", on_activate=lambda: open_editor("widget"), padding=0)
    remove = Button("Remove widget", on_activate=lambda: open_editor("remove"), padding=0)
    edit_header = Button("Edit header bar", on_activate=lambda: open_editor("header"), padding=0)
    edit_footer = Button("Edit footer bar", on_activate=lambda: open_editor("footer"), padding=0)
    quit = Button("Quit", on_activate=engine.stop, padding=0)
    body = Column()
    actions = Row()
    actions.add(add)
    actions.add(Connector("available", horizontal=True))
    actions.add(remove)
    actions.add(Connector("available", horizontal=True))
    actions.add(edit_header)
    actions.add(Connector("available", horizontal=True))
    actions.add(edit_footer)
    actions.add(Connector("available", horizontal=True))
    actions.add(quit)
    actions_center = Center()
    actions_center.add(actions)
    body.add(actions_center)
    body.add(Label("A add · E edit · R remove · Q quit · arrows move · Enter activate", align="center"))
    dialog = Panel(body, title="@@title@@", padding=0)
    content_main = Column()
    content_main.add(Label("Build your app here.", align="center"))
    content_main.add(Label("Add widgets to the content section in app.py.", align="center"))
    content_aside = Column()
    content_row = Row(fill=True, weights=[1, 0])
    content_row.add(content_main)
    content_row.add(content_aside)
    content = Panel(content_row, title="Content", padding=1)
    main = Column()
    main.add(dialog)
    main.add(header)
    main.add(content)
    main.add(footer)
    root = Stack()
    root.add(main)
    scene = Scene(name="@@package@@", root=root)

    layer = None

    def focus_widget(target) -> None:
        for widget in focusables(scene.root):
            widget.focus(False)
        target.focus(True)

    def focus_first_action() -> None:
        """Focus the first actionable menu button, skipping unwired placeholders."""
        for widget in focusables(main):
            if isinstance(widget, Button) and widget.on_activate is not None:
                focus_widget(widget)
                return

    hotkeys = [
        Hotkey("a", on_press=lambda: focus_widget(add)),
        Hotkey("e", on_press=focus_first_action),
        Hotkey("r", on_press=lambda: focus_widget(remove)),
        Hotkey("q", on_press=engine.stop),
    ]
    for hotkey in hotkeys:
        root.add(hotkey)

    def open_editor(kind: str) -> None:
        nonlocal layer
        if layer is not None:
            close_editor()
        for hotkey in hotkeys:
            root.remove(hotkey)
        if kind == "footer":
            editor = FooterEditor(
                text=cfg.get("footer"),
                border=cfg.get("footer_border"),
                fg=cfg.get("footer_fg"),
                on_save=save_footer,
                on_cancel=close_editor,
            )
        elif kind == "widget":
            editor = AddWidget(on_add=save_widget, on_cancel=close_editor, fits=space_reason)
        elif kind == "remove":
            entries = [f"{spec.get('type')} · {spec.get('placement')}" for spec, _, _ in placed]
            editor = RemoveWidget(entries, on_remove=remove_widget, on_cancel=close_editor)
        else:
            editor = HeaderEditor(
                text=cfg.get("header"),
                border=cfg.get("border"),
                fg=cfg.get("fg"),
                on_save=save_header,
                on_cancel=close_editor,
            )
        # Rest inline under the menu and above the header; the layout
        # reflows around it until save/cancel takes it away.
        layer = editor
        main.children.insert(1, editor)
        scene.set_focus_scope(editor)

    def close_editor() -> None:
        nonlocal layer
        if layer is None:
            return
        main.remove(layer)
        layer = None
        for hotkey in hotkeys:
            root.add(hotkey)
        scene.clear_focus_scope()

    def save_header(text: str, border: str, fg: str) -> None:
        cfg.set("header", text).set("border", border).set("fg", fg).save()
        header.set_text(text)
        header.set_colors(border=border, fg=fg)
        close_editor()

    def save_footer(text: str, border: str, fg: str) -> None:
        cfg.set("footer", text).set("footer_border", border).set("footer_fg", fg).save()
        footer.set_text(text)
        footer.set_colors(border=border, fg=fg)
        close_editor()

    placed: list = []  # (spec, parent, node) records backing removal

    def place_widget(kind: str, placement: str, stretch: bool = False):
        """Drop an assembled widget into the content section at a placement."""
        widget = engine.make_widget(kind)
        target = content_aside if placement == "sidebar" else content_main
        if stretch or placement in ("sidebar", "full"):
            target.add(widget)
            return target, widget
        if placement == "left":
            slot = Row()
            slot.add(widget)
        elif placement == "center":
            slot = Center()
            slot.add(widget)
        else:
            slot = Center(align="right")
            slot.add(widget)
        target.add(slot)
        return target, slot

    def space_reason(kind: str, placement: str, stretch: bool) -> str | None:
        """Refuse placement when the widget is wider than the content area."""
        if stretch:
            return None
        widget = engine.make_widget(kind)
        target = content_aside if placement == "sidebar" else content_main
        width = max((child.size().x for child in target.children), default=0)
        if widget.size().x > width:
            return f"No room: {kind} needs {widget.size().x} cols, content has {width}"
        return None

    def save_widget(kind: str, placement: str, stretch: bool) -> None:
        parent, node = place_widget(kind, placement, stretch)
        spec = {"type": kind, "placement": placement, "stretch": stretch}
        placed.append((spec, parent, node))
        cfg.set("widgets", [record[0] for record in placed]).save()
        close_editor()

    def remove_widget(index: int) -> None:
        _, parent, node = placed.pop(index)
        parent.remove(node)
        cfg.set("widgets", [record[0] for record in placed]).save()
        close_editor()

    for spec in cfg.get("widgets", []):
        kind = spec.get("type", "Label")
        placement = spec.get("placement", "full")
        stretch = spec.get("stretch", False)
        parent, node = place_widget(kind, placement, stretch)
        placed.append(({"type": kind, "placement": placement, "stretch": stretch}, parent, node))

    return scene


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build(engine))
    engine.run()
    home = windfall_home()
    if home is not None:
        print(f"Back to Windfall with: cd {home}")
