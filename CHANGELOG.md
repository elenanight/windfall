# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `windfall example snake`: the bundled grid game returns as a clean
  rewrite — steer with the arrows, grow on food, and restart after a crash.

### Fixed

- Nested containers no longer tick their widgets twice per frame, so
  components inside a `Stack`, `Center`, or similar update exactly once.

### Removed

- None.

## [0.2.6] - 2026-09-22

### Added

- `id` and `text` fields for placed widgets in the Add palette, reseeding
  the editor on reopen and persisting both to config for restoration on
  boot.
- `Motion` (Vec2) and `Sequence` (chained-step) animation primitives on
  the deterministic clock, for eased, scripted motion.
- `windfall example animation`: an easing and motion showcase scene.
- Project count and total-size readout in the project menu sidebar.
- Guide labels in scaffolded apps hide once widgets are placed.
- `N`/`O`/`D`/`A`/`X` hotkeys for project menu actions.
- Dependabot tracking for GitHub Actions alongside Python dependencies.

### Changed

- Scaffolded app shortcuts reworked to a QWER cluster: `W` add, `R`
  remove, `E` edit, `Q` quit.
- Project menu slimmed to fit with the size readout alongside.
- Scaffold README keys line refreshed to match the new hotkeys.
- Tests grouped by area and converted to class-based suites.
- CI actions modernized to current majors on a pinned `ubuntu-24.04`
  runner.

## [0.2.5] - 2026-09-21

### Added

- Project manager TUI (`windfall menu [--dir]`): browse scaffolded apps
  with a header bar, info sidebar, and credits footer; New with an inline
  name form, Open in place, Archive to timestamped `.archive` dirs,
  Delete with inline confirmation, and a farewell shutdown line.
- Hyperlink-capable `Style.link` rendering through rich.
- Robust input: SS3 arrow bindings, slow-terminal escape assembly, an
  exclusive terminal handoff to child apps, and ListView edge focus
  release.
- CI with dev-to-main auto-promotion, grouped Dependabot on dev, security
  policy with private reporting, and channel health badges.

### Changed

- README gains Roadmap and Project manager sections; releasing docs
  moved into the sync script.

## [0.2.4] - 2026-09-20

### Added

- `Row(fill)` layout flag with per-child weights for granular stretching.
- Stretch option and content-width space guard in the Add-widget palette.
- `R` hotkey focusing Remove; single Edit button drilling into header,
  footer, and placed widgets, with in-place widget editing.
- Visible Yes/No flags for the header and footer bars.
- `windfall new` stays quiet; the run prompt handles launching.

### Changed

- Menu buttons centered to match the helper text.
- Bar editors and Add palette use even thirds; content stretches with a
  natural-width sidebar aside.

## [0.2.3] - 2026-09-20

### Added

- Add-widget palette: drop Label/Button/TextInput/ListView/Divider into the
  content section with left/center/right/full/sidebar placement, persisted
  to config and restored on boot.
- Remove-widget palette listing placed widgets for deletion.
- `windfall new` asks to run the fresh app immediately (`--yes` skips).
- Quitting a scaffolded app prints the `cd` back to the Windfall checkout.

### Changed

- Header/footer editors restyled: full-width input, 50/50 border/text
  split, Update/Cancel buttons, resting inline under the menu.
- `Center` layout accepts left/center/right alignment; app menu is
  full-width above the header with a content section below.

## [0.2.2] - 2026-09-20

### Added

- Footer bar mirroring the header: `Footer` widget, `FooterEditor` panel,
  `Engine.make_footer()`, and footer keys in the scaffold config.
- `Hotkey` widget with `A`/`E`/`Q` menu shortcuts in scaffolded apps.
- State-colored `Connector` shafts (`available`/`unavailable`/`unlockable`/
  `active`) linking menu boxes and editor fields.
- Content body section in the scaffolded app template.
- Horizontal `align` option on the `Center` layout.

### Changed

- Scaffolded apps open header/footer editors from the menu instead of on
  first run.
- App menu moved above the header bar with compact spacing; editors stay
  left-docked.
- Focused button and text-input text paints with the highlight background
  so focus stays visible at any padding.

## [0.2.1] - 2026-09-20

### Added

- Quit button in scaffolded apps, wired to `engine.stop`.

### Changed

- Header editor overlay docks to the left edge instead of the center.
- Quit hint no longer advertises Ctrl+C.

## [0.2.0] - 2026-09-20

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