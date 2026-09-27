"""Tests for the compositor that turns scenes into rich renderables."""

from __future__ import annotations

from rich.text import Text as RichText

from windfall.compositor import Compositor
from windfall.geom import Vec2
from windfall.layout import Column
from windfall.primitives import Text
from windfall.scene import Scene


def _scene() -> Scene:
    root = Column()
    root.add(Text("ab"))
    root.add(Text("cd"))
    return Scene(name="doc", root=root)


class TestCompositor:
    def test_render_returns_rich_text(self) -> None:
        compositor = Compositor(6, 3)
        output = compositor.render(_scene())
        assert isinstance(output, RichText)
        assert str(output).splitlines() == ["ab    ", "cd    ", "      "]

    def test_text_renders_plain_grid(self) -> None:
        compositor = Compositor(6, 2)
        assert compositor.text(_scene()) == ["ab    ", "cd    "]

    def test_resize_changes_frame_size(self) -> None:
        compositor = Compositor(6, 2)
        compositor.resize(3, 1)
        assert compositor.text(_scene()) == ["ab "]

    def test_empty_scene_clears_frame(self) -> None:
        compositor = Compositor(4, 2)
        compositor.render(_scene())
        assert compositor.text(Scene(name="blank")) == ["    ", "    "]

    def test_size_reports_the_drawable_area(self) -> None:
        compositor = Compositor(80, 24)
        assert compositor.size() == Vec2(80, 24)

    def test_size_follows_resize(self) -> None:
        compositor = Compositor(80, 24)
        compositor.resize(120, 40)
        assert compositor.size() == Vec2(120, 40)