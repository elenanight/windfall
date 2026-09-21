"""Terminal styling: named colors, attributes, and themes."""

from __future__ import annotations

from dataclasses import dataclass

from rich.style import Style as _RichStyle

_STYLE_FIELDS = ("fg", "bg", "bold", "italic", "underline", "link")


@dataclass
class Style:
    """A declarative, mergeable description of a terminal visual style.

    ``None`` means "unset" so styles can be layered without clobbering.
    """

    fg: str | None = None
    bg: str | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    link: str | None = None

    def merge(self, other: Style) -> Style:
        return Style(
            fg=other.fg if other.fg is not None else self.fg,
            bg=other.bg if other.bg is not None else self.bg,
            bold=other.bold if other.bold is not None else self.bold,
            italic=other.italic if other.italic is not None else self.italic,
            underline=other.underline if other.underline is not None else self.underline,
            link=other.link if other.link is not None else self.link,
        )

    def to_rich(self) -> _RichStyle:
        params = {
            "color": self.fg,
            "bgcolor": self.bg,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "link": self.link,
        }
        return _RichStyle(**{name: value for name, value in params.items() if value is not None})

    @classmethod
    def from_dict(cls, data: dict) -> Style:
        return cls(**{key: value for key, value in data.items() if key in _STYLE_FIELDS})


class Theme:
    """A named collection of styles with a fallback default style."""

    def __init__(self, default: Style | None = None, overrides: dict[str, Style] | None = None) -> None:
        self._default = default if default is not None else Style()
        self._styles: dict[str, Style] = {}
        if overrides:
            for name, style in overrides.items():
                self.register(name, style)

    def register(self, name: str, style: Style) -> None:
        self._styles[name] = style

    def style(self, name: str) -> Style:
        return self._styles.get(name, self._default)

    @classmethod
    def from_dict(cls, data: dict[str, dict]) -> Theme:
        return cls(overrides={name: Style.from_dict(value) for name, value in data.items()})