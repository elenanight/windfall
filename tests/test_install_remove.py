"""Tests for the ``windfall install`` and ``windfall uninstall/remove`` commands."""

from __future__ import annotations

import io
from types import SimpleNamespace

import pytest

from windfall_cli import cli


def _stub_run(monkeypatch: pytest.MonkeyPatch, calls: list, returncode: int = 0) -> None:
    def fake_run(command, *args, **kwargs):
        calls.append((command, args, kwargs))
        return SimpleNamespace(returncode=returncode, stdout="", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)


def test_install_defaults_to_current_directory(monkeypatch, capsys):
    calls = []
    _stub_run(monkeypatch, calls)

    assert cli.main(["install"]) == 0

    assert calls[0][0] == ["uv", "tool", "install", "."]
    out = capsys.readouterr().out
    assert "Installed Windfall from ." in out


def test_install_accepts_source_and_force(monkeypatch, capsys, tmp_path):
    calls = []
    _stub_run(monkeypatch, calls)
    source = tmp_path / "windfall-src"
    source.mkdir()
    (source / "pyproject.toml").write_text("[project]\nname='windfall'\n", encoding="utf-8")

    assert cli.main(["install", str(source), "--force"]) == 0

    assert calls[0][0] == ["uv", "tool", "install", str(source), "--force"]
    out = capsys.readouterr().out
    assert f"Installed Windfall from {source}" in out


def test_install_propagates_failure(monkeypatch, capsys):
    calls = []
    _stub_run(monkeypatch, calls, returncode=3)

    assert cli.main(["install"]) == 3

    assert calls[0][0] == ["uv", "tool", "install", "."]
    out = capsys.readouterr().out
    assert "Installed Windfall" not in out


def test_install_reports_missing_uv(monkeypatch, capsys):
    def missing(*args, **kwargs):
        raise FileNotFoundError("uv")

    monkeypatch.setattr(cli.subprocess, "run", missing)

    assert cli.main(["install"]) == 2
    err = capsys.readouterr().err
    assert "uv not found" in err
    assert "cannot install Windfall" in err


def test_uninstall_runs_uv_tool_uninstall(monkeypatch, capsys):
    calls = []
    _stub_run(monkeypatch, calls)

    assert cli.main(["uninstall"]) == 0

    assert calls[0][0] == ["uv", "tool", "uninstall", "windfall"]
    out = capsys.readouterr().out
    assert "Removed Windfall." in out


def test_remove_alias_uninstalls(monkeypatch, capsys):
    calls = []
    _stub_run(monkeypatch, calls)

    assert cli.main(["remove"]) == 0

    assert calls[0][0] == ["uv", "tool", "uninstall", "windfall"]
    out = capsys.readouterr().out
    assert "Removed Windfall." in out


def test_uninstall_propagates_failure(monkeypatch):
    calls = []
    _stub_run(monkeypatch, calls, returncode=1)

    assert cli.main(["uninstall"]) == 1
    assert calls[0][0] == ["uv", "tool", "uninstall", "windfall"]


def test_uninstall_reports_missing_uv(monkeypatch, capsys):
    def missing(*args, **kwargs):
        raise FileNotFoundError("uv")

    monkeypatch.setattr(cli.subprocess, "run", missing)

    assert cli.main(["remove"]) == 2
    err = capsys.readouterr().err
    assert "uv not found" in err
    assert "cannot remove the Windfall tool" in err


def test_install_non_tty_emits_plain_steps_without_control_codes(monkeypatch, capsys):
    calls = []
    _stub_run(monkeypatch, calls)

    assert cli.main(["install"]) == 0
    out = capsys.readouterr().out

    # Plain step lines in order, no animation/control garbage.
    assert "> Preparing install…" in out
    assert "> Installing Windfall (uv tool)…" in out
    assert "> Verifying installation…" in out
    assert "ok Installed Windfall from ." in out
    assert "\r" not in out
    assert "\x1b[" not in out


def test_uninstall_non_tty_emits_plain_steps_without_control_codes(monkeypatch, capsys):
    calls = []
    _stub_run(monkeypatch, calls)

    assert cli.main(["uninstall"]) == 0
    out = capsys.readouterr().out

    assert "> Preparing removal…" in out
    assert "> Removing Windfall (uv tool)…" in out
    assert "> Verifying removal…" in out
    assert "ok Removed Windfall." in out
    assert "\r" not in out
    assert "\x1b[" not in out


def test_install_failure_non_tty_emits_plain_error(monkeypatch, capsys):
    calls = []
    _stub_run(monkeypatch, calls, returncode=1)

    assert cli.main(["install"]) == 1
    out = capsys.readouterr().out

    assert "> Preparing install…" in out
    assert "> Installing Windfall (uv tool)…" in out
    assert "> Verifying installation…" in out
    assert "error Install failed." in out
    assert "Installed Windfall from ." not in out
    assert "\r" not in out
    assert "\x1b[" not in out


def test_install_rejects_non_installable_source(monkeypatch, capsys, tmp_path):
    calls = []
    _stub_run(monkeypatch, calls)
    source = tmp_path / "not-a-project"
    source.mkdir()

    assert cli.main(["install", str(source)]) == 2

    assert calls == []
    err = capsys.readouterr().err
    assert f"install source '{source}' is not an installable Python project" in err
    assert "Windfall source checkout" in err or "explicit source path" in err


def test_install_rejects_missing_default_source_outside_checkout(monkeypatch, capsys, tmp_path):
    calls = []
    _stub_run(monkeypatch, calls)
    monkeypatch.chdir(tmp_path)

    assert cli.main(["install"]) == 2

    assert calls == []
    err = capsys.readouterr().err
    assert "install source '.' is not an installable Python project" in err


def test_install_already_installed_reports_failure(monkeypatch, capsys):
    calls = []

    def fake_run(command, *args, **kwargs):
        calls.append((command, args, kwargs))
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="error: Tool `windfall` is already installed",
        )

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert cli.main(["install"]) == 1
    captured = capsys.readouterr()
    assert "ok Installed Windfall" not in captured.out
    assert "error Install failed." in captured.out
    assert "already installed" in captured.err


def test_install_force_passed_for_reinstall(monkeypatch, capsys):
    calls = []
    _stub_run(monkeypatch, calls)

    assert cli.main(["install", "--force"]) == 0
    assert calls[0][0] == ["uv", "tool", "install", ".", "--force"]
    out = capsys.readouterr().out
    assert "ok Installed Windfall from ." in out


def test_uninstall_not_installed_reports_failure(monkeypatch, capsys):
    calls = []

    def fake_run(command, *args, **kwargs):
        calls.append((command, args, kwargs))
        return SimpleNamespace(
            returncode=2,
            stdout="",
            stderr="error: `windfall` is not installed",
        )

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert cli.main(["uninstall"]) == 2
    captured = capsys.readouterr()
    assert "ok Removed Windfall." not in captured.out
    assert "error Removal failed." in captured.out
    assert "not installed" in captured.err


def test_remove_not_installed_reports_failure(monkeypatch, capsys):
    calls = []

    def fake_run(command, *args, **kwargs):
        calls.append((command, args, kwargs))
        return SimpleNamespace(
            returncode=2,
            stdout="",
            stderr="error: `windfall` is not installed",
        )

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert cli.main(["remove"]) == 2
    captured = capsys.readouterr()
    assert "ok Removed Windfall." not in captured.out
    assert "error Removal failed." in captured.out
    assert "not installed" in captured.err


def test_install_accepts_pyproject_file_as_source(monkeypatch, capsys, tmp_path):
    calls = []
    _stub_run(monkeypatch, calls)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname='windfall'\n", encoding="utf-8")

    assert cli.main(["install", str(pyproject)]) == 0

    assert calls[0][0] == ["uv", "tool", "install", str(pyproject)]
    out = capsys.readouterr().out
    assert f"ok Installed Windfall from {pyproject}" in out


def test_uninstall_command_reports_missing_uv(monkeypatch, capsys):
    def missing(*args, **kwargs):
        raise FileNotFoundError("uv")

    monkeypatch.setattr(cli.subprocess, "run", missing)

    assert cli.main(["uninstall"]) == 2
    err = capsys.readouterr().err
    assert "uv not found" in err
    assert "cannot remove the Windfall tool" in err


class _FakeTTYStream(io.StringIO):
    def isatty(self) -> bool:
        return True


def test_install_tty_path_renders_animated_status_and_success(monkeypatch, capsys):
    calls = []

    class FakeProc:
        def __init__(self):
            self._polls = 0
            self.returncode = 0

        def poll(self):
            self._polls += 1
            if self._polls == 1:
                return None
            self.returncode = 0
            return 0

        def communicate(self):
            self.returncode = 0
            return ("", "")

    def fake_popen(command, *args, **kwargs):
        calls.append((command, args, kwargs))
        return FakeProc()

    # Drive TTY rendering to stdout capture; disable color for stable assertions.
    monkeypatch.setattr(cli.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(cli.sys, "stdout", _FakeTTYStream())
    monkeypatch.setattr(cli.time, "sleep", lambda *_: None)
    ticks = iter([0.0, 0.1, 0.2, 2.5, 2.6, 2.7])
    monkeypatch.setattr(cli.time, "monotonic", lambda: next(ticks, 3.0))
    monkeypatch.setattr(
        cli,
        "ProgressRenderer",
        lambda plan, stream=None, **kwargs: __import__("windfall_cli.progress", fromlist=["ProgressRenderer"]).ProgressRenderer(
            plan, stream=stream, color=False
        ),
    )

    assert cli.main(["install"]) == 0
    out = cli.sys.stdout.getvalue()

    assert calls[0][0] == ["uv", "tool", "install", "."]
    assert "\r" in out  # animated in-place updates
    assert "Preparing install…" in out
    assert "Installing Windfall (uv tool)…" in out
    assert "Verifying installation…" in out
    assert "ok Installed Windfall from ." in out


def test_install_tty_path_reports_failure_detail(monkeypatch):
    class FakeProc:
        def __init__(self):
            self._polls = 0
            self.returncode = 1

        def poll(self):
            self._polls += 1
            if self._polls == 1:
                return None
            self.returncode = 1
            return 1

        def communicate(self):
            self.returncode = 1
            return ("", "error: Tool `windfall` is already installed")

    def fake_popen(command, *args, **kwargs):
        return FakeProc()

    stderr = io.StringIO()
    monkeypatch.setattr(cli.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(cli.sys, "stdout", _FakeTTYStream())
    monkeypatch.setattr(cli.sys, "stderr", stderr)
    monkeypatch.setattr(cli.time, "sleep", lambda *_: None)
    ticks = iter([0.0, 0.1, 0.2, 2.5, 2.6, 2.7])
    monkeypatch.setattr(cli.time, "monotonic", lambda: next(ticks, 3.0))
    monkeypatch.setattr(
        cli,
        "ProgressRenderer",
        lambda plan, stream=None, **kwargs: __import__("windfall_cli.progress", fromlist=["ProgressRenderer"]).ProgressRenderer(
            plan, stream=stream, color=False
        ),
    )

    assert cli.main(["install"]) == 1
    out = cli.sys.stdout.getvalue()
    err = stderr.getvalue()

    assert "error Install failed." in out
    assert "ok Installed Windfall" not in out
    assert "already installed" in err


def test_install_source_validator_class_checks_project_markers(tmp_path):
    assert cli.InstallSourceValidator.is_valid(str(tmp_path)) is False
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    assert cli.InstallSourceValidator.is_valid(str(tmp_path)) is True
    assert cli._install_source_is_valid(str(tmp_path)) is True


def test_uv_tool_runner_class_plain_path(monkeypatch):
    calls = []
    _stub_run(monkeypatch, calls)
    renderer = __import__(
        "windfall_cli.progress", fromlist=["ProgressRenderer", "InstallProgressPlan"]
    ).ProgressRenderer(
        __import__("windfall_cli.progress", fromlist=["InstallProgressPlan"]).InstallProgressPlan,
        stream=io.StringIO(),
        color=False,
    )

    code, detail = cli.UvToolRunner().run(["uv", "tool", "install", "."], renderer, "install")

    assert code == 0
    assert detail == ""
    assert calls[0][0] == ["uv", "tool", "install", "."]


def test_windfall_tool_commands_class_install_and_uninstall(monkeypatch, capsys, tmp_path):
    calls = []
    _stub_run(monkeypatch, calls)
    source = tmp_path / "src"
    source.mkdir()
    (source / "pyproject.toml").write_text("[project]\nname='windfall'\n", encoding="utf-8")
    commands = cli.WindfallToolCommands()

    assert commands.install(SimpleNamespace(source=str(source), force=False)) == 0
    assert calls[0][0] == ["uv", "tool", "install", str(source)]
    assert "ok Installed Windfall from " in capsys.readouterr().out

    calls.clear()
    _stub_run(monkeypatch, calls)
    assert commands.uninstall(SimpleNamespace()) == 0
    assert calls[0][0] == ["uv", "tool", "uninstall", "windfall"]
    assert "ok Removed Windfall." in capsys.readouterr().out

