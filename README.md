# Windfall

<!-- badges:start -->
[![version](https://img.shields.io/badge/version-0.3.0-blue)](https://github.com/elenanight/windfall)
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

## Roadmap

A teaser of what's coming. Full detail for each item will live in the
wiki once it exists.

- **Project manager TUI** *(in progress)* — browse, open, archive, and
  delete apps without leaving the terminal.
- **Boot splash** *(planned)* — ASCII-art logo fade-in with a progress
  bar that lands in the project menu.
- **Animation release** *(planned)* — motion primitives and scripted
  transitions built on the deterministic clock.
- **Widget guides** *(planned)* — per-widget usage docs in the wiki.
- **Vember OS** *(long term)* — a node-based OS rendering through
  Windfall as an imported package.

## Quick start

```bash
uv sync
uv run windfall demo                  # interactive demo
uv run windfall menu                  # browse, open, and manage projects
uv run windfall new myapp             # scaffold a new app into project/myapp
cd project/myapp && uv run python app.py   # run it
uv run python examples/snake.py       # or play a game
```

## What's inside

Everything is a `Primitive` (a `size()` and a `draw(canvas, rect)`), so
layers compose freely:

| Layer | Types | Role |
| --- | --- | --- |
| Primitives | `Text`, `Spacer`, `Divider`, `Border`, `Box`, `Connector` | draw into a canvas |
| Widgets | `Label`, `Button`, `Panel`, `TextInput`, `ListView`, `Header`, `Footer`, `HeaderEditor`, `FooterEditor`, `Hotkey`, `AddWidget`, `RemoveWidget`, `EditMenu` | interactive primitives |
| Layout | `Container`, `Row`, `Column`, `Stack`, `Center` | position children (`Row` fills and weights available space on request) |
| Animation | `Tween`, `Animation`, `Timeline`, `Clock` | deterministic motion |
| Views | `Scene`, `Frame`, `FrameStack` | trees, focus, navigation |
| Engine | `Engine`, `Compositor` | input -> events -> tick -> `rich.Live`; assembles bars and widgets |
| Settings | `Config` | JSON settings with defaults fallback |

## Scaffolded apps

`windfall new myapp` scaffolds more than a blank scene. Every app ships
with a header bar, a footer bar, and a menu wired with node-style
connectors:

- **Editors** — one Edit button drills into header, footer, and placed
  widgets. Bars offer text, curated colors, and visible flags; widgets
  offer kind, placement, and stretch. Everything persists to
  `.windfallrc.json` and rebuilds on launch.
- **Hotkeys** — `W` add, `E` edit, `R` remove, `Q` back. Arrow keys move
  focus, Enter activates.
- **Content section** — add widgets by palette, place them left, center,
  right, full width, or sidebar, and remove them the same way.

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
- **Hotkeys** — `N` new, `O` open, `D` delete, `A` archive, `X` quit.
  Arrow keys move focus, Enter activates.

With no projects yet, the list says so and the status line points at
`New`. Every action narrates itself in the status line, and the sidebar
keeps a live project count.

## Examples

- `examples/menu.py` — `ListView` navigation inside a `Column` layout.
- `examples/bouncer.py` — a custom `Ball` component animated by scene
  tweens that bounce back and forth.
- `examples/snake.py` — a tiny grid game with deterministic `update(dt)`
  movement, arrow steering, and Enter to restart.

Run any example headless for N fixed ticks by posting events and calling
`engine.step(dt)` — see `tests/test_examples.py`.

## Development

### Testing

The suite is entirely headless: input is scripted, `rich.Live` is stubbed,
and time is advanced by explicit `dt`, never wall-clock sleeps.

```bash
uv run pytest -q
uv run ruff check .
```

### Rule of ten

Every class may define at most 10 methods (excluding `__init__`). The test
suite enforces this with an `ast`-based audit (`tests/budget.py`):

- more than 10 methods -> `[BUDGET-ERROR]` and the test fails
- 9-10 methods -> `[BUDGET-WARNING]` naming the class and methods

