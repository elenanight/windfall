"""Splash-inspired progress rendering for install/remove CLI flows.

Reusable, deterministic, and testable: renders the gold-on-gray bar and
phase messages with Windfall's splash palette. TTY/color output can be
disabled for headless or piped contexts.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

# Splash palette (see windfall_cli/splash.py).
GOLD = (255, 214, 0)  # #ffd600
INDIGO_DIM = (45, 45, 70)  # #2d2d46
TRACK_GRAY = (85, 85, 85)  # #555555
HINT_GRAY = (136, 136, 136)  # #888888
SUCCESS_GREEN = (80, 200, 120)
FAIL_RED = (220, 90, 90)

BAR_TRACK = "·"
BAR_FILL = "█"

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def clamp_progress(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def visible_length(text: str) -> int:
    return len(_ANSI_RE.sub("", text))


@dataclass(frozen=True)
class ProgressPhase:
    """One named phase with a display message and progress range."""

    key: str
    label: str
    start: float
    end: float


class ProgressTheme:
    """Color helpers for splash-inspired terminal output."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    @staticmethod
    def _rgb(code: tuple[int, int, int], text: str) -> str:
        r, g, b = code
        return f"\x1b[38;2;{r};{g};{b}m{text}\x1b[0m"

    def paint(self, text: str, color: tuple[int, int, int]) -> str:
        if not self.enabled:
            return text
        return self._rgb(color, text)

    def gold(self, text: str) -> str:
        return self.paint(text, GOLD)

    def track(self, text: str) -> str:
        return self.paint(text, TRACK_GRAY)

    def dim(self, text: str) -> str:
        return self.paint(text, HINT_GRAY)

    def success(self, text: str) -> str:
        return self.paint(text, SUCCESS_GREEN)

    def failure(self, text: str) -> str:
        return self.paint(text, FAIL_RED)

    def accent(self, text: str) -> str:
        return self.paint(text, INDIGO_DIM)


class InstallProgressPlan:
    """Phase plan and messages for `windfall install`."""

    @staticmethod
    def phases() -> list[ProgressPhase]:
        return [
            ProgressPhase("prepare", "Preparing install…", 0.0, 0.20),
            ProgressPhase("install", "Installing Windfall (uv tool)…", 0.20, 0.85),
            ProgressPhase("verify", "Verifying installation…", 0.85, 1.0),
        ]

    @staticmethod
    def success(source: str) -> str:
        text = f"Installed Windfall from {source}"
        return text if text.endswith(".") else f"{text}."

    @staticmethod
    def failure() -> str:
        return "Install failed."


class RemoveProgressPlan:
    """Phase plan and messages for `windfall uninstall`/`remove`."""

    @staticmethod
    def phases() -> list[ProgressPhase]:
        return [
            ProgressPhase("prepare", "Preparing removal…", 0.0, 0.25),
            ProgressPhase("uninstall", "Removing Windfall (uv tool)…", 0.25, 0.85),
            ProgressPhase("verify", "Verifying removal…", 0.85, 1.0),
        ]

    @staticmethod
    def success() -> str:
        return "Removed Windfall."

    @staticmethod
    def failure() -> str:
        return "Removal failed."


class ProgressRenderer:
    """Render splash-inspired progress bars and step messages."""

    def __init__(
        self,
        plan,
        *,
        width: int = 24,
        color: bool | None = None,
        stream=None,
    ) -> None:
        self.plan = plan
        self.width = max(1, int(width))
        self.stream = stream if stream is not None else sys.stdout
        if color is None:
            color = bool(getattr(self.stream, "isatty", lambda: False)())
        self.theme = ProgressTheme(enabled=bool(color))
        self.color = bool(color)

    def bar(self, progress: float) -> str:
        p = clamp_progress(progress)
        filled = round(p * self.width)
        fill = BAR_FILL * filled
        track = BAR_TRACK * (self.width - filled)
        return self.theme.gold(fill) + self.theme.track(track)

    def phase_progress(self, phase_key: str, fraction: float = 0.0) -> float:
        fraction = clamp_progress(fraction)
        for phase in self.plan.phases():
            if phase.key == phase_key:
                return phase.start + (phase.end - phase.start) * fraction
        return 0.0

    def status_line(self, message: str, progress: float) -> str:
        pct = round(clamp_progress(progress) * 100)
        pct_text = self.theme.dim(f"{pct:3d}%")
        return f"{self.bar(progress)} {pct_text} {message}"

    def step_line(self, message: str) -> str:
        # Plain/non-animated step line for non-TTY fallback.
        bullet = self.theme.gold("▸") if self.color else ">"
        return f"{bullet} {message}"

    def success_line(self, message: str) -> str:
        mark = self.theme.success("✔") if self.color else "ok"
        return f"{mark} {message}"

    def failure_line(self, message: str) -> str:
        mark = self.theme.failure("✖") if self.color else "error"
        return f"{mark} {message}"

    def emit(self, text: str, *, newline: bool = True) -> None:
        end = "\n" if newline else ""
        print(text, end=end, file=self.stream, flush=True)

    def render_phase(self, phase_key: str, *, fraction: float = 0.0, tty: bool = False) -> str:
        progress = self.phase_progress(phase_key, fraction)
        message = phase_key
        for phase in self.plan.phases():
            if phase.key == phase_key:
                message = phase.label
                break
        if tty:
            return self.status_line(message, progress)
        return self.step_line(message)

    def render_success(self, message: str) -> str:
        return self.success_line(message)

    def render_failure(self, message: str) -> str:
        return self.failure_line(message)
