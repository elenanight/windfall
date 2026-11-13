"""Tests for splash-inspired install/remove progress rendering (VWS-136)."""

from __future__ import annotations

import io

from windfall_cli.progress import (
    BAR_FILL,
    BAR_TRACK,
    InstallProgressPlan,
    ProgressRenderer,
    RemoveProgressPlan,
    visible_length,
)


def test_bar_empty_and_full_plain():
    r = ProgressRenderer(InstallProgressPlan, width=10, color=False, stream=io.StringIO())
    assert r.bar(0.0) == BAR_TRACK * 10
    assert r.bar(1.0) == BAR_FILL * 10


def test_bar_partial_fill_plain():
    r = ProgressRenderer(InstallProgressPlan, width=10, color=False, stream=io.StringIO())
    # 0.5 of 10 => 5 filled
    assert r.bar(0.5) == (BAR_FILL * 5) + (BAR_TRACK * 5)


def test_bar_clamps_progress():
    r = ProgressRenderer(InstallProgressPlan, width=8, color=False, stream=io.StringIO())
    assert r.bar(-1.0) == BAR_TRACK * 8
    assert r.bar(2.0) == BAR_FILL * 8


def test_status_and_step_lines_plain():
    r = ProgressRenderer(InstallProgressPlan, width=10, color=False, stream=io.StringIO())
    status = r.status_line("Preparing install…", 0.0)
    assert BAR_TRACK * 10 in status
    assert "  0%" in status
    assert "Preparing install…" in status

    step = r.step_line("Preparing install…")
    assert step.startswith("> ")
    assert "Preparing install…" in step


def test_phase_progress_from_plan():
    r = ProgressRenderer(InstallProgressPlan, width=10, color=False, stream=io.StringIO())
    assert r.phase_progress("prepare", 0.0) == 0.0
    assert r.phase_progress("prepare", 1.0) == 0.20
    assert r.phase_progress("install", 0.0) == 0.20
    assert r.phase_progress("verify", 1.0) == 1.0


def test_install_and_remove_phase_messages():
    ri = ProgressRenderer(InstallProgressPlan, width=10, color=False, stream=io.StringIO())
    assert "Preparing install…" in ri.render_phase("prepare")
    assert "Installing Windfall (uv tool)…" in ri.render_phase("install")

    rr = ProgressRenderer(RemoveProgressPlan, width=10, color=False, stream=io.StringIO())
    assert "Preparing removal…" in rr.render_phase("prepare")
    assert "Removing Windfall (uv tool)…" in rr.render_phase("uninstall")
    assert "Verifying removal…" in rr.render_phase("verify")


def test_success_and_failure_lines_plain():
    ri = ProgressRenderer(InstallProgressPlan, color=False, stream=io.StringIO())
    assert ri.render_success(InstallProgressPlan.success(".")) == "ok Installed Windfall from ."
    assert ri.render_failure(InstallProgressPlan.failure()) == "error Install failed."

    rr = ProgressRenderer(RemoveProgressPlan, color=False, stream=io.StringIO())
    assert rr.render_success(RemoveProgressPlan.success()) == "ok Removed Windfall."
    assert rr.render_failure(RemoveProgressPlan.failure()) == "error Removal failed."


def test_color_output_includes_ansi_when_enabled():
    r = ProgressRenderer(InstallProgressPlan, width=10, color=True, stream=io.StringIO())
    bar = r.bar(0.5)
    assert "\x1b[" in bar  # ANSI color codes present
    assert BAR_FILL in bar and BAR_TRACK in bar
    # visible characters still contain bar glyphs
    assert visible_length(bar) == 10


def test_tty_mode_renders_status_line():
    r = ProgressRenderer(InstallProgressPlan, width=10, color=False, stream=io.StringIO())
    line = r.render_phase("prepare", fraction=0.0, tty=True)
    assert "Preparing install…" in line
    assert "  0%" in line
    assert BAR_TRACK * 10 in line
