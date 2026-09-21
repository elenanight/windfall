"""Persist small user settings for windfall apps."""

from __future__ import annotations

import json
from pathlib import Path


class Config:
    """A tiny JSON-backed key/value store for app settings.

    Missing or corrupt files fall back to ``defaults``; :meth:`save`
    writes the merged mapping back to ``path``.
    """

    def __init__(self, path: str | Path, defaults: dict | None = None) -> None:
        self.path = Path(path)
        self._data = dict(defaults or {})

    @classmethod
    def load(cls, path: str | Path, defaults: dict | None = None) -> Config:
        config = cls(path, defaults)
        try:
            raw = config.path.read_text(encoding="utf-8")
        except OSError:
            return config
        try:
            saved = json.loads(raw)
        except ValueError:
            return config
        if isinstance(saved, dict):
            config._data.update(saved)
        return config

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> Config:
        self._data[key] = value
        return self

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self._data, indent=2, sort_keys=True) + "\n"
        self.path.write_text(text, encoding="utf-8")
