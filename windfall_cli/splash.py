"""Boot splash: an ASCII windmill fading in over a filling progress bar.

``SplashScene`` shows a small turbine drawing that fades from a dim color
into a bright one while a progress bar fills. When the animation finishes —
or the user presses any key — it invokes the ``on_done`` callback so the
caller can swap in the real menu. Both timings use the scene's deterministic
clock, so the whole splash can be stepped headless and asserted in tests.
"""

from __future__ import annotations

from windfall.anim import Tween, ease_linear, ease_out_cubic
from windfall.geom import Rect
from windfall.scene import Scene
from windfall.style import Style

_LOGO = r"""
      \    / \    /
       \  /   \  /
        \/     \/
     ──────●──────
        /\     /\
       /  \   /  \
      /    \ /    \
   W · I · N · D · F · A · L · L
"""

_FADE_START = (45, 45, 70)
_FADE_END = (255, 214, 0)
_BAR_TRACK = "·"
_BAR_FILL = "█"


def _fade_color(t: float) -> str:
    """Blend the logo foreground from dim indigo to bright gold by ``t``."""
    channels = (
        round(start + (end - start) * t)
        for start, end in zip(_FADE_START, _FADE_END)
    )
    return "#{:02x}{:02x}{:02x}".format(*channels)


def _lines() -> list[str]:
    return [line for line in _LOGO.splitlines() if line]


class SplashScene(Scene):
    """Fades the logo in while a progress bar fills, then hands off.

    ``on_done`` fires once, when the timeline completes or any key is
    pressed. It is typically an engine ``FrameStack.replace`` call that
    swaps the splash for the project menu.
    """

    def __init__(
        self,
        *,
        on_done=None,
        duration: float = 1.6,
        fade: float = 1.0,
        bar_width: int = 24,
    ) -> None:
        super().__init__(name="splash")
        self._on_done = on_done
        self._bar_width = bar_width
        self._handoff = False
        self._progress = Tween(0.0, 1.0, duration, ease=ease_linear)
        self._fade = Tween(0.0, 1.0, fade, ease=ease_out_cubic)
        self.timeline.add(self._progress)
        self.timeline.add(self._fade)

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.timeline.done:
            self._finish()

    def handle(self, event) -> bool:
        self._finish()
        return True

    def draw(self, canvas, rect: Rect) -> None:
        logo = _lines()
        logo_width = max(len(line) for line in logo)
        style = Style(fg=_fade_color(self._fade.value), bold=True)
        top = max(0, (rect.height - len(logo) - 2) // 2)
        row = top
        for line in logo:
            canvas.write(line, rect.x + (rect.width - logo_width) // 2, row, style)
            row += 1
        bar_x = rect.x + (rect.width - self._bar_width) // 2
        filled = round(self._progress.value * self._bar_width)
        canvas.write(_BAR_TRACK * self._bar_width, bar_x, row, Style(fg="#555555"))
        canvas.write(_BAR_FILL * filled, bar_x, row, Style(fg=_fade_color(1.0)))
        hint = "press any key"
        canvas.write(hint, rect.x + (rect.width - len(hint)) // 2, row + 1, Style(fg="#888888"))

    def _finish(self) -> None:
        if self._handoff:
            return
        self._handoff = True
        if self._on_done is not None:
            self._on_done()


def build_splash(on_done=None) -> SplashScene:
    """Build the boot splash scene; ``on_done`` run on finish or keypress."""
    return SplashScene(on_done=on_done)