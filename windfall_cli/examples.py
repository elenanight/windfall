"""Run the bundled example apps from the `windfall` command."""

from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

from windfall import Engine

_EXAMPLES = ("menu", "bouncer", "animation", "snake")
_DESCRIPTIONS = {
    "menu": "a focusable menu (ListView)",
    "bouncer": "a ball bouncing on a scene timeline",
    "animation": "easing and motion with Motion and Sequence",
    "snake": "a tiny grid snake game",
}
_EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def run_example(name: str, *, headless: bool = False, ticks: int = 120) -> int:
    """Build and run one bundled example, interactively or headless."""
    if name not in _EXAMPLES:
        options = ", ".join(sorted(_EXAMPLES))
        print(f"windfall: unknown example {name!r}; choose from: {options}", file=sys.stderr)
        return 2
    module = _load(name)
    engine = Engine()
    engine.use_scene(module.build())
    if headless:
        for _ in range(ticks):
            engine.step(0.016)
        return 0
    engine.run()
    return 0


def list_examples() -> None:
    for name in _EXAMPLES:
        print(f"{name:<10} {_DESCRIPTIONS[name]}")


def _load(name):
    path = _EXAMPLES_DIR / f"{name}.py"
    if path.is_file():
        return SimpleNamespace(**runpy.run_path(str(path)))
    try:
        return importlib.import_module(f"examples.{name}")
    except ImportError as error:
        raise FileNotFoundError(f"example {name!r} not found ({path})") from error