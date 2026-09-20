"""@@package@@ — a windfall app scaffolded with `windfall new`."""

from windfall import Button, Center, Column, Engine, Label, Panel, Scene


def build() -> Scene:
    """Assemble the app's root scene."""
    button = Button("Press Enter", on_activate=lambda: print("hi from @@package@@!"))
    button.focus(True)
    body = Column()
    center = Center()
    center.add(button)
    body.add(center)
    body.add(Label("Enter: activate · arrows: move · Ctrl+C: quit", align="center"))
    dialog = Panel(body, title="@@title@@", padding=1)
    root = Center()
    root.add(dialog)
    return Scene(name="@@package@@", root=root)


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build())
    engine.run()