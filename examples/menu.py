"""A focusable menu: ListView navigation inside a Column layout.

Arrows move the selection, Enter picks an option (printed to stdout), and
Ctrl+C quits. Run with: `uv run python examples/menu.py`.
"""

from __future__ import annotations

from windfall import Column, Divider, Engine, Label, ListView, Scene

_OPTIONS = ["New Game", "Continue", "Options", "Quit"]


def build() -> Scene:
    menu = ListView(items=_OPTIONS, on_select=lambda option, _: print(f"chose {option}"))
    menu.focus(True)
    root = Column()
    root.add(Label("Windfall menu", align="center"))
    root.add(Divider())
    root.add(menu)
    root.add(Label("arrows: move · Enter: select · Ctrl+C: quit"))
    return Scene(name="menu", root=root)


if __name__ == "__main__":
    engine = Engine()
    engine.use_scene(build())
    engine.run()