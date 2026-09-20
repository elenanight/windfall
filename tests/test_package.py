"""Package import smoke tests for the scaffold."""

from __future__ import annotations

import windfall


def test_version_exposed() -> None:
    assert windfall.__version__ == "0.1.0"


def test_cli_entry_point_imports() -> None:
    from windfall_cli import cli

    assert callable(cli.main)