"""Windfall — a class-based TUI compositor and engine for terminal apps and games.

Radially importable: pick a submodule (``windfall.geom``) for the whole API,
or take the convenience exports below.
"""

from __future__ import annotations

from windfall.anim import (
    Animation,
    Clock,
    Timeline,
    Tween,
    ease_in_out_cubic,
    ease_linear,
    ease_out_cubic,
)
from windfall.canvas import Canvas
from windfall.component import Component
from windfall.compositor import Compositor
from windfall.config import Config
from windfall.engine import Engine
from windfall.events import (
    ACTIVATE,
    BLUR,
    CANCEL,
    FOCUS,
    KEY,
    MOVE,
    QUIT,
    RESIZE,
    TICK,
    Event,
    EventQueue,
)
from windfall.geom import Rect, Vec2
from windfall.input import InputReader, Keymap
from windfall.layout import Center, Column, Container, Row, Stack
from windfall.primitives import Border, Box, Connector, Divider, Primitive, Spacer, Text
from windfall.scene import Frame, FrameStack, Scene
from windfall.style import Style, Theme
from windfall.widgets import (
    AddWidget,
    Button,
    Footer,
    FooterEditor,
    Header,
    HeaderEditor,
    Hotkey,
    Label,
    ListView,
    Panel,
    TextInput,
)

__version__ = "0.2.2"

__all__ = [
    "ACTIVATE",
    "BLUR",
    "CANCEL",
    "FOCUS",
    "KEY",
    "MOVE",
    "QUIT",
    "RESIZE",
    "TICK",
    "AddWidget",
    "Animation",
    "Border",
    "Box",
    "Button",
    "Canvas",
    "Center",
    "Clock",
    "Column",
    "Component",
    "Compositor",
    "Config",
    "Connector",
    "Container",
    "Divider",
    "Engine",
    "Event",
    "EventQueue",
    "Footer",
    "FooterEditor",
    "Frame",
    "FrameStack",
    "Header",
    "HeaderEditor",
    "Hotkey",
    "InputReader",
    "Keymap",
    "Label",
    "ListView",
    "Panel",
    "Primitive",
    "Rect",
    "Row",
    "Scene",
    "Spacer",
    "Stack",
    "Style",
    "Text",
    "TextInput",
    "Theme",
    "Timeline",
    "Tween",
    "Vec2",
    "__version__",
    "ease_in_out_cubic",
    "ease_linear",
    "ease_out_cubic",
]