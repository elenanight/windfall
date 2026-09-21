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
    EditMenu,
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
    "header_visible": True,
    "footer": "built with windfall",
    "footer_border": "cyan",
    "footer_fg": "white",
    "footer_visible": True,
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
    edit = Button("Edit", on_activate=lambda: open_edit_menu(), padding=0)
    quit = Button("← Back", on_activate=engine.stop, padding=0)
    body = Column()
    actions = Row()
    actions.add(add)
    actions.add(Connector("available", horizontal=True))
    actions.add(remove)
    actions.add(Connector("available", horizontal=True))
    actions.add(edit)
    actions.add(Connector("available", horizontal=True))
    actions.add(quit)
    actions_center = Center()
    actions_center.add(actions)
    body.add(actions_center)
    body.add(Label("W add · E edit · R remove · Q back · arrows move · Enter activate", align="center"))
    dialog = Panel(body, title="@@title@@", padding=0)
    content_main = Column()
    guide_build = Label("Build your app here.", align="center")
    guide_where = Label("Add widgets to the content section in app.py.", align="center")
    content_main.add(guide_build)
    content_main.add(guide_where)
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
        """Focus the Edit button, the single entry to bar and widget editing."""
        focus_widget(edit)

    hotkeys = [
        Hotkey("w", on_press=lambda: focus_widget(add)),
        Hotkey("e", on_press=focus_first_action),
        Hotkey("r", on_press=lambda: focus_widget(remove)),
        Hotkey("q", on_press=engine.stop),
    ]
    for hotkey in hotkeys:
        root.add(hotkey)

    def _show_editor(editor) -> None:
        """Swap any open editor for ``editor``, parking hotkeys and scoping focus."""
        nonlocal layer
        if layer is not None:
            close_editor()
        for hotkey in hotkeys:
            root.remove(hotkey)
        # Rest inline under the menu and above the header; the layout
        # reflows around it until save/cancel takes it away.
        layer = editor
        main.children.insert(1, editor)
        scene.set_focus_scope(editor)

    def open_editor(kind: str) -> None:
        if kind == "footer":
            editor = FooterEditor(
                text=cfg.get("footer"),
                border=cfg.get("footer_border"),
                fg=cfg.get("footer_fg"),
                visible=cfg.get("footer_visible", True),
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
                visible=cfg.get("header_visible", True),
                on_save=save_header,
                on_cancel=close_editor,
            )
        _show_editor(editor)

    def open_edit_menu() -> None:
        entries = [
            "Header bar" + ("" if cfg.get("header_visible", True) else " (hidden)"),
            "Footer bar" + ("" if cfg.get("footer_visible", True) else " (hidden)"),
        ]
        entries.extend(f"{spec.get('type')} · {spec.get('placement')}" for spec, _, _ in placed)
        _show_editor(EditMenu(entries, on_pick=pick_edit_target, on_cancel=close_editor))

    def pick_edit_target(index: int) -> None:
        if index == 0:
            open_editor("header")
        elif index == 1:
            open_editor("footer")
        else:
            open_edit_widget(index - 2)

    def open_edit_widget(index: int) -> None:
        spec, _, _ = placed[index]
        editor = AddWidget(
            title="Edit widget",
            on_add=lambda kind, placement, stretch: save_edited(index, kind, placement, stretch),
            on_cancel=close_editor,
            fits=space_reason,
        )
        editor.preset(spec.get("type", "Label"), spec.get("placement", "full"), spec.get("stretch", False))
        _show_editor(editor)

    def close_editor() -> None:
        nonlocal layer
        if layer is None:
            return
        main.remove(layer)
        layer = None
        for hotkey in hotkeys:
            root.add(hotkey)
        scene.clear_focus_scope()

    def save_header(text: str, border: str, fg: str, visible: bool) -> None:
        cfg.set("header", text).set("border", border).set("fg", fg).set("header_visible", visible).save()
        header.set_text(text)
        header.set_colors(border=border, fg=fg)
        close_editor()
        _sync_bars()

    def save_footer(text: str, border: str, fg: str, visible: bool) -> None:
        cfg.set("footer", text).set("footer_border", border).set("footer_fg", fg).set(
            "footer_visible", visible
        ).save()
        footer.set_text(text)
        footer.set_colors(border=border, fg=fg)
        close_editor()
        _sync_bars()

    def _sync_bars() -> None:
        """Match bar presence to the saved visibility flags."""
        for bar in (header, footer):
            if bar in main.children:
                main.remove(bar)
        if cfg.get("header_visible", True):
            main.children.insert(1, header)
        if cfg.get("footer_visible", True):
            main.add(footer)

    placed: list = []  # (spec, parent, node) records backing removal
    guides = [guide_build, guide_where]

    def _sync_guides() -> None:
        """Show the guide labels only while no widgets are placed."""
        if placed:
            for guide in guides:
                if guide in content_main.children:
                    content_main.remove(guide)
        else:
            for guide in guides:
                if guide not in content_main.children:
                    content_main.add(guide)

    def build_slot(kind: str, placement: str, stretch: bool = False):
        """Assemble a placed widget and its slot without attaching either."""
        widget = engine.make_widget(kind)
        target = content_aside if placement == "sidebar" else content_main
        if stretch or placement in ("sidebar", "full"):
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
        return target, slot

    def place_widget(kind: str, placement: str, stretch: bool = False):
        """Drop an assembled widget into the content section at a placement."""
        target, node = build_slot(kind, placement, stretch)
        target.add(node)
        return target, node

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
        _sync_guides()
        close_editor()

    def save_edited(index: int, kind: str, placement: str, stretch: bool) -> None:
        _, parent, node = placed[index]
        new_parent, new_node = build_slot(kind, placement, stretch)
        if new_parent is parent:
            new_parent.children[parent.children.index(node)] = new_node
        else:
            parent.remove(node)
            new_parent.add(new_node)
        new_spec = {"type": kind, "placement": placement, "stretch": stretch}
        placed[index] = (new_spec, new_parent, new_node)
        cfg.set("widgets", [record[0] for record in placed]).save()
        close_editor()

    def remove_widget(index: int) -> None:
        _, parent, node = placed.pop(index)
        parent.remove(node)
        cfg.set("widgets", [record[0] for record in placed]).save()
        _sync_guides()
        close_editor()

    for spec in cfg.get("widgets", []):
        kind = spec.get("type", "Label")
        placement = spec.get("placement", "full")
        stretch = spec.get("stretch", False)
        parent, node = place_widget(kind, placement, stretch)
        placed.append(({"type": kind, "placement": placement, "stretch": stretch}, parent, node))

    _sync_guides()
    _sync_bars()
    return scene


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build(engine))
    engine.run()
    home = windfall_home()
    if home is not None:
        print(f"Back to Windfall with: cd {home}")
