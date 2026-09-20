"""AST-based inspection of windfall apps."""

from __future__ import annotations

import ast
from pathlib import Path

_INTERESTING_BASES = {"Scene", "Component", "Widget"}


def scenes_in(path: str | Path) -> list[str]:
    """Return class names in *path* that extend windfall view types."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
            if any(base in _INTERESTING_BASES for base in bases):
                found.append(node.name)
    return found