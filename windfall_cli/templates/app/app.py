"""@@package@@ — a windfall app scaffolded with `windfall new`."""

from pathlib import Path

from windfall import (
    Button,
    Center,
    Column,
    Config,
    Engine,
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
}


def build(engine: Engine) -> Scene:
    """Assemble the app scene, opening the header editor on first run."""
    cfg = Config.load(CONFIG_PATH, defaults=DEFAULTS)
    header = engine.make_header(cfg.get("header"), border=cfg.get("border"), fg=cfg.get("fg"))
    button = Button("Press Enter", on_activate=lambda: print("hi from @@package@@!"))
    button.focus(True)
    edit = Button("Edit header bar", on_activate=lambda: open_editor())
    quit = Button("Quit", on_activate=engine.stop)
    body = Column()
    center = Center()
    center.add(button)
    body.add(center)
    body.add(Label("Enter: activate · arrows: move · Quit button: quit", align="center"))
    actions = Row()
    actions.add(edit)
    actions.add(quit)
    actions_center = Center()
    actions_center.add(actions)
    body.add(actions_center)
    dialog = Panel(body, title="@@title@@", padding=1)
    dialog_center = Center()
    dialog_center.add(dialog)
    main = Column()
    main.add(header)
    main.add(dialog_center)
    root = Stack()
    root.add(main)
    scene = Scene(name="@@package@@", root=root)

    layer = None

    def open_editor() -> None:
        nonlocal layer
        if layer is not None:
            return
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

    if not CONFIG_PATH.exists():
        open_editor()
    return scene


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build(engine))
    engine.run()
