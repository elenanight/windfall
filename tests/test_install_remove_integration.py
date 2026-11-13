"""Integration smoke checks for real `uv tool` install/uninstall flow (VWS-143).

Runs in an isolated uv tool environment (UV_TOOL_DIR/UV_TOOL_BIN_DIR) so it
does not affect the user's installed tools.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from windfall_cli import cli

pytestmark = pytest.mark.skipif(shutil.which("uv") is None, reason="uv not available")

REPO_ROOT = Path(__file__).resolve().parents[1]


def _isolated_uv_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tool_dir = tmp_path / "uv-tools"
    bin_dir = tmp_path / "uv-bin"
    tool_dir.mkdir()
    bin_dir.mkdir()
    monkeypatch.setenv("UV_TOOL_DIR", str(tool_dir))
    monkeypatch.setenv("UV_TOOL_BIN_DIR", str(bin_dir))


def test_real_install_and_remove_flow_isolated(tmp_path, monkeypatch, capsys):
    _isolated_uv_env(tmp_path, monkeypatch)
    monkeypatch.chdir(REPO_ROOT)

    assert cli.main(["install", "."]) == 0
    out = capsys.readouterr().out
    assert "> Preparing install…" in out
    assert "> Installing Windfall (uv tool)…" in out
    assert "> Verifying installation…" in out
    assert "ok Installed Windfall from ." in out

    listed = subprocess.run(
        ["uv", "tool", "list"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    assert "windfall" in listed.stdout

    assert cli.main(["remove"]) == 0
    out = capsys.readouterr().out
    assert "> Preparing removal…" in out
    assert "> Removing Windfall (uv tool)…" in out
    assert "> Verifying removal…" in out
    assert "ok Removed Windfall." in out

    listed = subprocess.run(
        ["uv", "tool", "list"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    assert "windfall" not in listed.stdout
