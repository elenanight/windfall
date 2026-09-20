"""Tests for styling and themes."""

from __future__ import annotations

from windfall.style import Style, Theme


def test_style_defaults_are_none() -> None:
    style = Style()
    assert style.fg is None
    assert style.bold is None


def test_style_merge_overrides_set_values() -> None:
    base = Style(fg="red", bold=False)
    override = Style(fg="green")
    merged = base.merge(override)
    assert merged.fg == "green"
    assert merged.bold is False
    assert merged.bg is None


def test_style_merge_preserves_unset_fields() -> None:
    merged = Style(fg="red").merge(Style(bg="blue"))
    assert merged.fg == "red"
    assert merged.bg == "blue"


def test_style_to_rich_maps_fields() -> None:
    rich = Style(fg="red", bg="blue", bold=True).to_rich()
    assert rich.color.name == "red"
    assert rich.bgcolor.name == "blue"
    assert rich.bold is True


def test_style_to_rich_omits_unset_fields() -> None:
    rich = Style().to_rich()
    assert rich.color is None
    assert rich.bgcolor is None
    assert rich.bold is None


def test_style_from_dict_ignores_unknown_keys() -> None:
    style = Style.from_dict({"fg": "red", "bogus": True})
    assert style.fg == "red"
    assert not hasattr(style, "bogus")


def test_theme_register_and_default_fallback() -> None:
    theme = Theme()
    default = theme.style("missing")
    theme.register("title", Style(fg="yellow"))
    assert theme.style("title").fg == "yellow"
    assert theme.style("missing") is default


def test_theme_from_dict() -> None:
    theme = Theme.from_dict({"title": {"fg": "yellow", "bold": True}})
    title = theme.style("title")
    assert title.fg == "yellow"
    assert title.bold is True


def test_theme_custom_default() -> None:
    base = Style(fg="white")
    theme = Theme(default=base)
    fallback = theme.style("anything")
    assert fallback is base