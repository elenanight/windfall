"""Headless smoke check used by `windfall check`."""

from __future__ import annotations

from windfall import MOVE, Compositor, Engine, Event, ListView
from windfall.scene import focusables
from windfall_cli.demo import build_scene


def run_check(*, ticks: int = 60) -> int:
    """Step the demo engine headless; return 0 if every assertion holds."""
    engine = Engine(compositor=Compositor(60, 20))
    scene = build_scene()
    engine.use_scene(scene)
    menus = [node for node in focusables(scene.root) if isinstance(node, ListView)]
    if not menus:
        print("check failed: no ListView found in demo scene")
        return 1
    menu = menus[0]
    engine.post_event(Event(MOVE, {"direction": "down"}))
    engine.step(0.016)
    if menu.selection != 1:
        print(f"check failed: selection {menu.selection} != 1")
        return 1
    for _ in range(max(0, ticks - 1)):
        engine.step(0.016)
    rows = engine.compositor.text(scene)
    if not any(row.strip() for row in rows):
        print("check failed: rendered frame was blank")
        return 1
    return 0