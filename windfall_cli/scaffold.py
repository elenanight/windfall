"""Scaffolding for new windfall apps."""

from __future__ import annotations

import re
from os.path import relpath
from pathlib import Path

_PACKAGE_TOKEN = "@@package@@"
_TITLE_TOKEN = "@@title@@"
_UV_SOURCES_TOKEN = "# @@uv_sources@@"


class Scaffolder:
    """Copies a project template, replacing project tokens along the way."""

    def __init__(self, templates_dir: str | Path) -> None:
        self.templates_dir = Path(templates_dir)

    def create(
        self,
        name: str,
        template: str = "app",
        destination: str | Path | None = None,
    ) -> Path:
        if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", name):
            raise ValueError(f"{name!r} is not a valid project name")
        source = self.templates_dir / template
        if not source.is_dir():
            raise FileNotFoundError(f"no such template: {template!r}")
        base = Path(destination) if destination is not None else Path.cwd()
        target = base / "project" / name
        if target.exists():
            raise FileExistsError(f"{target} already exists")
        self._copy_tree(source, target, name, self._windfall_block(target))
        return target

    def _copy_tree(self, source: Path, target: Path, name: str, windfall_block: str) -> None:
        for path in source.rglob("*"):
            if path.is_dir():
                continue
            destination = target / path.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            rendered = self._render(path.read_text(encoding="utf-8"), name, windfall_block)
            destination.write_text(rendered, encoding="utf-8")

    def _render(self, text: str, name: str, windfall_block: str) -> str:
        title = name.replace("-", " ").replace("_", " ").title()
        return (
            text.replace(_PACKAGE_TOKEN, name)
            .replace(_TITLE_TOKEN, title)
            .replace(_UV_SOURCES_TOKEN, windfall_block)
        )

    def _windfall_block(self, target: Path) -> str:
        root = Path(__file__).resolve().parents[1]
        if not (root / "pyproject.toml").is_file():
            return ""
        path = relpath(root, target).replace("\\", "/")
        return f'[tool.uv.sources]\nwindfall = {{ path = "{path}", editable = true }}\n'