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

## Quick start

```bash
uv sync
uv run windfall demo                  # interactive demo
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
| Widgets | `Label`, `Button`, `Panel`, `TextInput`, `ListView`, `Header`, `Footer`, `HeaderEditor`, `FooterEditor`, `Hotkey` | interactive primitives |
| Layout | `Container`, `Row`, `Column`, `Stack`, `Center` | position children |
| Animation | `Tween`, `Animation`, `Timeline`, `Clock` | deterministic motion |
| Views | `Scene`, `Frame`, `FrameStack` | trees, focus, navigation |
| Engine | `Engine`, `Compositor` | input -> events -> tick -> `rich.Live` |
| Settings | `Config` | JSON settings with defaults fallback |

## Scaffolded apps

`windfall new myapp` scaffolds more than a blank scene. Every app ships
with a header bar, a footer bar, and a menu wired with node-style
connectors:

- **In-place editors** — open the header or footer editor from the menu,
  pick text plus curated border/text colors, and save. Choices persist to
  `.windfallrc.json`, so later runs rebuild the bars automatically.
- **Hotkeys** — `A` focuses the Add widget slot, `E` focuses the first
  menu action, `Q` quits. Arrow keys move focus, Enter activates.
- **Content section** — a labeled panel marking where your own widgets go.

## CLI

```
windfall new NAME [--template app] [--dest DIR] [--yes]   scaffold into DIR/project/NAME; asks to run it on a terminal (--yes skips that)
windfall run [app.py]                             run a file (default: the demo)
windfall demo [--headless] [--ticks N]            run the built-in demo
windfall example NAME [--headless] [--ticks N]    run a bundled example (menu/bouncer/snake)
windfall check [--ticks N]                        headless smoke check (exit 0/1)
windfall list app.py                              list Scene/Component subclasses (AST)
windfall help | --help | --version
```

Every subcommand also has a shortcut flag (`--create`, `--run`, `--demo`,
`--example`, `--check`, `--list`, plus `--examples` to list examples).
`demo`, `check`, and every run share the same `Engine.step` code path, so a
`--headless` pass is equivalent to a real terminal session.

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

### Releasing

`pyproject.toml` holds the released version. After bumping it, run the sync
script to refresh the README version badge and `__version__` together:

```bash
uv run python scripts/update_readme.py            # update badges + __version__
uv run python scripts/update_readme.py --check    # verify they are in sync (CI-friendly)
```
