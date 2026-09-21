"""@@package@@ — a windfall app scaffolded with `windfall new`."""

from pathlib import Path

from windfall import (
    Button,
    Column,
    Config,
    Connector,
    Engine,
    FooterEditor,
    HeaderEditor,
    Label,
    Panel,
    Row,
    Scene,
    Stack,
)

CONFIG_PATH = Path(__file__).resolve().parent / ".windfallrc.json"

DEFAULTS = {
    "header": "hello from @@package@@!",
    "border": "cyan",
    "fg": "bright_white",
    "footer": "built with windfall",
    "footer_border": "cyan",
    "footer_fg": "white",
}


def build(engine: Engine) -> Scene:
    """Assemble the app scene: header, menu, content, and footer bars."""
    cfg = Config.load(CONFIG_PATH, defaults=DEFAULTS)
    header = engine.make_header(cfg.get("header"), border=cfg.get("border"), fg=cfg.get("fg"))
    footer = engine.make_footer(
        cfg.get("footer"), border=cfg.get("footer_border"), fg=cfg.get("footer_fg")
    )
    # Hook for later: widget choices + editor plug in here.
    add = Button("Add widget", on_activate=None)
    edit_header = Button("Edit header bar", on_activate=lambda: open_editor("header"))
    edit_footer = Button("Edit footer bar", on_activate=lambda: open_editor("footer"))
    quit = Button("Quit", on_activate=engine.stop)
    body = Column()
    actions = Row()
    actions.add(add)
    actions.add(Connector("available", horizontal=True))
    actions.add(edit_header)
    actions.add(Connector("available", horizontal=True))
    actions.add(edit_footer)
    actions.add(Connector("available", horizontal=True))
    actions.add(quit)
    body.add(actions)
    body.add(Label("Enter: activate · arrows: move · Quit button: quit", align="center"))
    dialog = Panel(body, title="@@title@@", padding=1)
    content_body = Column()
    content_body.add(Label("Build your app here.", align="center"))
    content_body.add(Label("Add widgets to the content section in app.py.", align="center"))
    content = Panel(content_body, title="Content", padding=1)
    main = Column()
    main.add(header)
    main.add(dialog)
    main.add(content)
    main.add(footer)
    root = Stack()
    root.add(main)
    scene = Scene(name="@@package@@", root=root)

    layer = None

    def open_editor(kind: str) -> None:
        nonlocal layer
        if layer is not None:
            close_editor()
        if kind == "footer":
            editor = FooterEditor(
                text=cfg.get("footer"),
                border=cfg.get("footer_border"),
                fg=cfg.get("footer_fg"),
                on_save=save_footer,
                on_cancel=close_editor,
            )
        else:
            editor = HeaderEditor(
                text=cfg.get("header"),
                border=cfg.get("border"),
                fg=cfg.get("fg"),
                on_save=save_header,
                on_cancel=close_editor,
            )
        # Left-docked overlay: the row draws the editor at the left edge
        # while the app body shows through on the right.
        layer = Row()
        layer.add(editor)
        root.add(layer)
        scene.set_focus_scope(editor)

    def close_editor() -> None:
        nonlocal layer
        if layer is None:
            return
        root.remove(layer)
        layer = None
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

    return scene


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build(engine))
    engine.run()
