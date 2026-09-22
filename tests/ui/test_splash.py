"""Tests for the boot splash animation and its menu handoff."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import key
from windfall import Compositor, Engine
from windfall.scene import Frame, focusables
from windfall_cli import menu as menu_module
from windfall_cli.splash import SplashScene, _fade_color, build_splash


class TestSplashRender:
    def test_logo_and_hint_render(self) -> None:
        rows = Compositor(40, 14).text(build_splash())
        assert any("W · I · N · D" in row for row in rows)
        assert any("press any key" in row for row in rows)

    def test_bar_starts_empty_then_fills(self) -> None:
        scene = SplashScene(duration=1.0)
        rows = Compositor(40, 14).text(scene)
        bar = [row for row in rows if "·" in row and "█" not in row and "press" not in row]
        assert bar, "expected an empty progress bar"
        engine = Engine()
        engine.use_scene(scene)
        for _ in range(64):  # 64 * 0.016 = 1.024s > duration
            engine.step(0.016)
        rows = Compositor(40, 14).text(scene)
        assert any("█" in row for row in rows)


class TestSplashFade:
    def test_fade_animates_toward_full_brightness(self) -> None:
        scene = SplashScene(fade=1.0)
        assert scene._fade.value == pytest.approx(0.0)
        engine = Engine()
        engine.use_scene(scene)
        for _ in range(32):
            engine.step(0.016)
        assert 0.0 < scene._fade.value < 1.0
        for _ in range(32):
            engine.step(0.016)
        assert scene._fade.value == pytest.approx(1.0)

    def test_fade_color_blends_from_dim_to_gold(self) -> None:
        assert _fade_color(0.0) == "#2d2d46"
        assert _fade_color(1.0) == "#ffd600"


class TestSplashHandoff:
    def test_callback_fires_once_after_timeline_completes(self) -> None:
        calls: list[str] = []
        scene = SplashScene(duration=0.5, on_done=lambda: calls.append("done"))
        engine = Engine()
        engine.use_scene(scene)
        for _ in range(64):
            engine.step(0.016)
        assert calls == ["done"]
        engine.step(0.016)
        assert calls == ["done"]

    def test_any_key_skips_to_handoff(self) -> None:
        calls: list[str] = []
        scene = SplashScene(duration=60.0, on_done=lambda: calls.append("done"))
        assert scene.handle(key("x")) is True
        assert calls == ["done"]

    def test_key_skips_only_once(self) -> None:
        calls: list[str] = []
        scene = SplashScene(duration=60.0, on_done=lambda: calls.append("done"))
        scene.handle(key("a"))
        scene.handle(key("b"))
        assert calls == ["done"]


class TestSplashMenuHandoff:
    def test_splash_lands_in_the_project_menu(self, tmp_path: Path) -> None:
        project = tmp_path / "project" / "myapp"
        project.mkdir(parents=True)
        (project / "app.py").write_text("value = 1\n", encoding="utf-8")
        engine = Engine()
        menu = menu_module.build_menu(engine, tmp_path)
        engine.use_scene(build_splash(on_done=lambda: engine.frames.replace(Frame(menu))))
        assert engine.frames.current.scene.name == "splash"
        for _ in range(128):
            engine.step(0.016)
        assert engine.frames.current.scene is menu
        assert any(w.focused for w in focusables(menu.root))
        assert any("myapp" in row for row in Compositor(40, 14).text(menu))