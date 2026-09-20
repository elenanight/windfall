"""Built-in demo scene used by `windfall demo` and `windfall check`."""

from __future__ import annotations

from windfall import Center, Column, Engine, Label, ListView, Panel, Scene, TextInput


def build_scene() -> Scene:
    field = TextInput(value="windfall")
    menu = ListView(items=["New Game", "Options", "Quit"])
    menu.focus(True)
    body = Column()
    body.add(Label("Windfall", align="center"))
    body.add(Panel(field, title="Project", padding=1))
    body.add(menu)
    root = Center()
    root.add(body)
    return Scene(name="demo", root=root)


def main(*, headless: bool = False, ticks: int = 120) -> int:
    """Run the demo interactively, or step it headless for the given tick count."""
    engine = Engine()
    engine.use_scene(build_scene())
    if headless:
        for _ in range(ticks):
            engine.step(0.016)
        return 0
    engine.run()
    return 0