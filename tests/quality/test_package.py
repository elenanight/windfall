"""Package import smoke tests for the scaffold."""

from __future__ import annotations

import importlib.metadata

import windfall


class TestPackage:
    def test_version_exposed(self) -> None:
        assert windfall.__version__ == importlib.metadata.version("windfall")

    def test_cli_entry_point_imports(self) -> None:
        from windfall_cli import cli

        assert callable(cli.main)