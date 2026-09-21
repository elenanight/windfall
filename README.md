# Windfall

<!-- badges:start -->
[![version](https://img.shields.io/badge/version-0.2.4-blue)](https://github.com/elenanight/windfall)
[![stable](https://img.shields.io/github/actions/workflow/status/elenanight/windfall/ci.yml?branch=main&label=stable)](https://github.com/elenanight/windfall/actions)
[![dev](https://img.shields.io/github/actions/workflow/status/elenanight/windfall/ci.yml?branch=dev&label=dev)](https://github.com/elenanight/windfall/actions)
[![changelog](https://img.shields.io/badge/latest-changelog-orange)](https://github.com/elenanight/windfall/blob/main/CHANGELOG.md)

[![python](https://img.shields.io/badge/python-3.14-3776AB)](https://github.com/elenanight/windfall)
[![dependencies](https://img.shields.io/badge/dependencies-up%20to%20date-green)](https://github.com/elenanight/windfall/security/dependabot)
[![last commit](https://img.shields.io/github/last-commit/elenanight/windfall)](https://github.com/elenanight/windfall)
<!-- badges:end -->

A class-based TUI compositor and engine for building terminal apps and games
with `rich` and `readchar`. Assemble reusable components and widgets from
primitives, compose them into scenes and frames, animate them with a shared,
explicitly-advanced clock, and drive the whole thing from one engine loop —
headless and interactive alike.

## Status

Phase 7 — complete. The full pipeline is built and tested:

- **Primitives** (`Text`, `Spacer`, `Divider`, `Border`, `Box`) draw into a
  cell-grid `Canvas` and expose a `rich` renderable for the live display.
- **Widgets** (`Label`, `Button`, `Panel`, `TextInput`, `ListView`) are
  primitives that also tick, handle events, and take focus.
- **Scenes** (`Scene`, `Frame`, `FrameStack`) compose widget trees, cycle
  focus, and animate via `Tween`, `Animation`, `Timeline`, and `Clock`.
- **Engine** (`Engine`, `Compositor`) runs the loop over `rich.Live` —
  interactively or one deterministic `step(dt)` at a time.
- **CLI** scaffolds, runs, demos, checks, and inspects apps.

## Quick start

```bash
uv sync
uv run windfall demo                  # interactive demo
uv run windfall new myapp             # scaffold a new app into project/myapp
cd project/myapp && uv run python app.py   # run it
uv run python examples/snake.py       # or play a game
```

## Layers

Everything is a `Primitive` (a `size()` and a `draw(canvas, rect)`), so layers
compose freely:

| Layer | Types | Role |
| --- | --- | --- |
| Primitives | `Text`, `Spacer`, `Divider`, `Border`, `Box`, `Connector` | draw into a canvas |
| Widgets | `Label`, `Button`, `Panel`, `TextInput`, `ListView`, `Header`, `Footer`, `HeaderEditor`, `FooterEditor`, `Hotkey`, `AddWidget`, `RemoveWidget`, `EditMenu` | interactive primitives |
| Layout | `Container`, `Row`, `Column`, `Stack`, `Center` | position children (`Row` fills and weights available space on request) |
| Animation | `Tween`, `Animation`, `Timeline`, `Clock` | deterministic motion |
| Views | `Scene`, `Frame`, `FrameStack` | trees, focus, navigation |
| Engine | `Engine`, `Compositor` | input -> events -> tick -> `rich.Live`; assembles bars and widgets |
| Settings | `Config` | JSON settings with defaults fallback |

## CLI

```
windfall new NAME [--template app] [--dest DIR] [--yes]   scaffold into DIR/project/NAME; asks to run it on a terminal (--yes skips that)
windfall run [app.py]                             run a file (default: the demo)
windfall demo [--headless] [--ticks N]            run the built-in demo
windfall menu [--dir DIR]                         browse, open, archive, and delete projects
windfall example NAME [--headless] [--ticks N]    run a bundled example (menu/bouncer/snake)
windfall check [--ticks N]                        headless smoke check (exit 0/1)
windfall list app.py                              list Scene/Component subclasses (AST)
windfall help | --help | --version
```

Every subcommand also has a shortcut flag:

```
windfall --create NAME [--template] [--dest]      ≡ windfall new
windfall --run PATH                               ≡ windfall run
windfall --demo [--headless] [--ticks]            ≡ windfall demo
windfall --menu                                     ≡ windfall menu
windfall --example NAME [--headless] [--ticks]    ≡ windfall example
windfall --check [--ticks]                        ≡ windfall check
windfall --list PATH                              ≡ windfall list
windfall --examples                               list the bundled examples
```

`demo`, `check`, and every run share the same `Engine.step` code path, so a
`--headless` pass is equivalent to a real terminal session.

## Project manager

`windfall menu` (or `windfall --menu`) opens an interactive project
manager built from the same widgets apps use — a header bar, a project
list with an info sidebar, action buttons, and a footer with credits.
Point it elsewhere with `windfall menu --dir DIR` (it scans
`DIR/project`).

- **New** — inline name form; scaffolds straight into the list.
- **Open** — runs the selected app in its own folder, then returns.
- **Delete** — asks inline first (`Yes`/`No`); only `Yes` removes it.
- **Archive** — moves the app to `project/.archive/<name>-<timestamp>/`.
- **Quit** — leaves with a farewell line once the terminal restores.

With no projects yet, the list says so and the status line points at
`New`. Every action narrates itself in the status line, and the sidebar
keeps a live project count.

## Examples

- `examples/menu.py` — ListView navigation inside a `Column` layout.
- `examples/bouncer.py` — a custom `Ball` component animated across a track by
  scene tweens that bounce back and forth.
- `examples/snake.py` — a tiny grid game: a custom `Component` with
  deterministic `update(dt)` movement, arrow steering, and Enter to restart.

Run any example headless for N fixed ticks by posting events and calling
`engine.step(dt)` — see `tests/test_examples.py`.

## Testing

The suite is entirely headless: input is scripted, `rich.Live` is stubbed, and
time is advanced by explicit `dt`, never wall-clock sleeps.

```bash
uv run pytest -q
uv run ruff check .
```

## Rule of ten

Every class may define at most 10 methods (excluding `__init__`). The test
suite enforces this with an `ast`-based audit (`tests/budget.py`):

- more than 10 methods -> `[BUDGET-ERROR]` and the test fails
- 9-10 methods -> `[BUDGET-WARNING]` naming the class and methods

## Releasing

`pyproject.toml` holds the released version. After bumping it, run the sync
script to refresh the README version badge and `__version__` together:

```bash
uv run python scripts/update_readme.py            # update badges + __version__
uv run python scripts/update_readme.py --check    # verify they are in sync (CI-friendly)
```