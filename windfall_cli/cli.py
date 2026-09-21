"""Command-line interface: scaffold, run, demo, check, and list.

Every subcommand has a shortcut flag: ``--create``, ``--run``, ``--demo``,
``--menu``, ``--check``, ``--list``, plus ``--example``/``--examples`` to run or browse the
bundled example apps, and ``help``.
"""

from __future__ import annotations

import argparse
import runpy
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from windfall import __version__
from windfall_cli.scaffold import Scaffolder

TEMPLATES_DIR = Path(__file__).parent / "templates"


def main(argv: list[str] | None = None) -> int:
    """Parse argv and dispatch to a subcommand or shortcut flag."""
    parser = build_parser()
    args = parser.parse_args(argv)
    alias = _alias_action(args)
    if alias is not None:
        handler, namespace = alias
        return handler(namespace)
    if args.command == "help" or args.command is None:
        parser.print_help()
        return 0
    return _HANDLERS[args.command](args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="windfall",
        description="Windfall: a class-based TUI compositor and engine.",
    )
    parser.add_argument("--version", action="version", version=f"windfall {__version__}")

    parser.add_argument("--create", metavar="NAME", default=None, help="scaffold a new app (alias for `new`)")
    parser.add_argument("--template", default="app", help="template for --create (default: app)")
    parser.add_argument("--dest", default=None, help="parent directory for --create (default: current dir; creates project/NAME)")
    parser.add_argument("--run", metavar="PATH", default=None, help="run an app file (alias for `run`)")
    parser.add_argument("--demo", action="store_true", help="run the built-in demo (alias for `demo`)")
    parser.add_argument("--menu", action="store_true", help="open the project manager (alias for `menu`)")
    parser.add_argument("--check", action="store_true", help="headless smoke check (alias for `check`)")
    parser.add_argument("--list", metavar="PATH", default=None, help="list scene classes in a file (alias for `list`)")
    parser.add_argument("--example", metavar="NAME", default=None, help="run a bundled example: menu, bouncer, snake")
    parser.add_argument("--examples", action="store_true", help="list the bundled examples")
    parser.add_argument("--headless", action="store_true", help="step without a terminal (with --demo, --example)")
    parser.add_argument("--ticks", type=int, default=None, help="ticks for headless runs")

    sub = parser.add_subparsers(dest="command")

    cmd_new = sub.add_parser("new", help="scaffold a new app from a template")
    cmd_new.add_argument("name")
    cmd_new.add_argument("--template", default="app", help="template to copy (default: app)")
    cmd_new.add_argument("--dest", default=None, help="parent directory (default: current dir; creates project/NAME)")
    cmd_new.add_argument(
        "--yes",
        action="store_true",
        help="run the new app immediately without asking",
    )

    cmd_run = sub.add_parser("run", help="run an app file (default: the demo)")
    cmd_run.add_argument("path", nargs="?", default=None, help="python file to run")

    cmd_demo = sub.add_parser("demo", help="run the built-in demo")
    cmd_demo.add_argument("--headless", action="store_true", help="step without a terminal")
    cmd_demo.add_argument("--ticks", type=int, default=120, help="ticks for --headless")

    cmd_menu = sub.add_parser("menu", help="browse, open, archive, and delete projects")
    cmd_menu.add_argument("--dir", default=None, help="parent directory (default: current dir; scans DIR/project)")

    cmd_example = sub.add_parser("example", help="run a bundled example")
    cmd_example.add_argument("name", choices=["menu", "bouncer", "snake"])
    cmd_example.add_argument("--headless", action="store_true", help="step without a terminal")
    cmd_example.add_argument("--ticks", type=int, default=120, help="ticks for --headless")

    cmd_check = sub.add_parser("check", help="headless smoke check of the demo")
    cmd_check.add_argument("--ticks", type=int, default=60, help="ticks to step")

    cmd_list = sub.add_parser("list", help="list scene classes in an app file")
    cmd_list.add_argument("path", help="python file to inspect")

    sub.add_parser("help", help="show this help")

    return parser


def _cmd_new(args) -> int:
    try:
        target = Scaffolder(TEMPLATES_DIR).create(args.name, template=args.template, destination=args.dest)
    except (ValueError, FileExistsError, FileNotFoundError) as error:
        print(f"windfall: {error}", file=sys.stderr)
        return 2
    display = _display_path(target)
    print(f"Created {display} (template {args.template}).")
    if getattr(args, "yes", False):
        return _run_scaffolded(target)
    if sys.stdin.isatty():
        try:
            answer = input(f"Run '{args.name}' now? [y/N]: ")
        except EOFError:
            return 0
        if answer.strip().lower() in ("y", "yes"):
            return _run_scaffolded(target)
    return 0


def _run_scaffolded(target: Path) -> int:
    """Launch a freshly scaffolded app inside its own directory."""
    print(f"Starting {target.name} ...")
    try:
        proc = subprocess.run(["uv", "run", "python", "app.py"], cwd=target, check=False)
    except FileNotFoundError:
        print("windfall: `uv` not found; start the app manually.", file=sys.stderr)
        return 2
    return proc.returncode


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _cmd_run(args) -> int:
    if args.path is None:
        from windfall_cli.demo import main as demo_main

        return demo_main(headless=False, ticks=120)
    path = Path(args.path)
    if not path.is_file():
        print(f"windfall: no such file: {path}", file=sys.stderr)
        return 2
    runpy.run_path(str(path), run_name="__main__")
    return 0


def _cmd_demo(args) -> int:
    from windfall_cli.demo import main as demo_main

    return demo_main(headless=args.headless, ticks=args.ticks)


def _cmd_menu(args) -> int:
    from windfall_cli.menu import main as menu_main

    return menu_main(root=getattr(args, "dir", None))


def _cmd_check(args) -> int:
    from windfall_cli.check import run_check

    return run_check(ticks=args.ticks)


def _cmd_list(args) -> int:
    from windfall_cli.inspect import scenes_in

    path = Path(args.path)
    if not path.is_file():
        print(f"windfall: no such file: {path}", file=sys.stderr)
        return 2
    names = scenes_in(path)
    if not names:
        print("(no scenes found)")
    for name in names:
        print(name)
    return 0


def _cmd_example(args) -> int:
    from windfall_cli.examples import run_example

    try:
        return run_example(args.name, headless=args.headless, ticks=args.ticks)
    except FileNotFoundError as error:
        print(f"windfall: {error}", file=sys.stderr)
        return 2


def _cmd_examples(_args) -> int:
    from windfall_cli.examples import list_examples

    list_examples()
    return 0


def _cmd_help(args) -> int:
    build_parser().print_help()
    return 0


def _alias_action(args):
    """Map shortcut flags to a handler plus a Namespace shaped like the subcommand."""
    if args.create is not None:
        return _cmd_new, Namespace(name=args.create, template=args.template, dest=args.dest)
    if args.demo:
        ticks = args.ticks if args.ticks is not None else 120
        return _cmd_demo, Namespace(headless=args.headless, ticks=ticks)
    if args.menu:
        return _cmd_menu, Namespace(dir=None)
    if args.check:
        ticks = args.ticks if args.ticks is not None else 60
        return _cmd_check, Namespace(ticks=ticks)
    if args.run is not None:
        return _cmd_run, Namespace(path=args.run)
    if args.list is not None:
        return _cmd_list, Namespace(path=args.list)
    if args.example is not None:
        ticks = args.ticks if args.ticks is not None else 120
        return _cmd_example, Namespace(name=args.example, headless=args.headless, ticks=ticks)
    if args.examples:
        return _cmd_examples, Namespace()
    return None


_HANDLERS = {
    "new": _cmd_new,
    "run": _cmd_run,
    "demo": _cmd_demo,
    "menu": _cmd_menu,
    "check": _cmd_check,
    "list": _cmd_list,
    "example": _cmd_example,
    "examples": _cmd_examples,
    "help": _cmd_help,
}


if __name__ == "__main__":
    raise SystemExit(main())