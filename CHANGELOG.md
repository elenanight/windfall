# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- None yet.

## [0.2.0] - 2026-09-21

### Added

- In-place header editor: `HeaderEditor` panel (`TextInput` + curated-color
  `ListView`s + Save/Cancel) assembled from primitives and widgets.
- `Header` widget and `Engine.make_header()` assembling a header bar from a
  bordered box and a styled label.
- `Config` JSON store so apps persist user settings with defaults fallback.
- `Scene` focus scopes (`set_focus_scope`/`clear_focus_scope`) trapping
  arrow-key focus inside an open editor panel and restoring prior focus.
- Scaffolded apps open the header editor on first run and keep an
  “Edit header bar” button for later re-edits, persisting to
  `.windfallrc.json`.

### Changed

- Method budget relaxed from the rule of seven to the rule of ten
  (10 methods max excluding `__init__`; warnings at 9-10).

## [0.1.0] - 2026-09-20

### Added

- Class-based TUI compositor and engine built on `rich` and `readchar`.
- Primitives: `Text`, `Spacer`, `Divider`, `Border`, `Box` drawing into a
  cell-grid `Canvas`.
- Widgets: `Label`, `Button`, `Panel`, `TextInput`, `ListView` — primitives
  that tick, handle events, and take focus.
- Layouts: `Container`, `Row`, `Column`, `Stack`, and `Center` for positioning
  and centering children.
- Animation: `Tween`, `Animation`, `Timeline`, and `Clock` with deterministic,
  explicitly-advanced time.
- Views: `Scene`, `Frame`, and `FrameStack` for trees, focus cycling, and
  navigation.
- Engine loop over `rich.Live`, runnable interactively or one
  `step(dt)` at a time.
- CLI: `windfall new/run/demo/example/check/list` plus shortcut flags.
- Scaffolder that creates `project/NAME` apps and installs windfall as an
  editable path dependency via `[tool.uv.sources]`.
- Headless testability: scripted input, stubbed `rich.Live`, no wall-clock
  sleeps.
- Rule-of-seven method budget enforced by an AST audit.
- Release tooling: README version badge block and
  `scripts/update_readme.py` to keep `README.md` and `__version__` in sync.
- MIT license, README badges.

### Changed

- Scaffolds install windfall as an editable path dependency instead of
  copying a wheel, so app venvs always run the current source.

### Fixed

- Enter not activating focused widgets: both `\r` and `\n` now map to the
  activate event.
- Ctrl+C leaving the terminal broken: the engine owns raw mode with `ISIG`
  off, so `\x03` is read as a byte and the terminal is always restored.
- Renderer output post-processing re-enabled (`OPOST`/`ONLCR`) so `rich.Live`
  repaints no longer scatter fragments across the screen.
- Event, focus, and tick traversal now descends through `Panel`/`Box`
  single-child containers.
- Compositor is sized to the real terminal (and resized on `SIGWINCH`) and
  renders in the alternate screen buffer.