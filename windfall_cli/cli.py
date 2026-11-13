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
import time
from argparse import Namespace
from pathlib import Path

from windfall import __version__
from windfall_cli.progress import InstallProgressPlan, ProgressRenderer, RemoveProgressPlan
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
    _add_shortcut_flags(parser)
    _add_subcommands(parser.add_subparsers(dest="command"))
    return parser


def _add_shortcut_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--create", metavar="NAME", default=None, help="scaffold a new app (alias for `new`)"
    )
    parser.add_argument("--template", default="app", help="template for --create (default: app)")
    parser.add_argument(
        "--dest",
        default=None,
        help="parent directory for --create (default: current dir; creates project/NAME)",
    )
    parser.add_argument(
        "--run", metavar="PATH", default=None, help="run an app file (alias for `run`)"
    )
    parser.add_argument("--demo", action="store_true", help="run the built-in demo (alias for `demo`)")
    parser.add_argument("--menu", action="store_true", help="open the project manager (alias for `menu`)")
    parser.add_argument("--check", action="store_true", help="headless smoke check (alias for `check`)")
    parser.add_argument(
        "--list", metavar="PATH", default=None, help="list scene classes in a file (alias for `list`)"
    )
    parser.add_argument(
        "--example",
        metavar="NAME",
        default=None,
        help="run a bundled example: menu, bouncer, animation, snake",
    )
    parser.add_argument("--examples", action="store_true", help="list the bundled examples")
    parser.add_argument(
        "--headless", action="store_true", help="step without a terminal (with --demo, --example)"
    )
    parser.add_argument("--ticks", type=int, default=None, help="ticks for headless runs")


def _add_subcommands(sub: argparse._SubParsersAction) -> None:
    cmd_new = sub.add_parser("new", help="scaffold a new app from a template")
    cmd_new.add_argument("name")
    cmd_new.add_argument("--template", default="app", help="template to copy (default: app)")
    cmd_new.add_argument(
        "--dest", default=None, help="parent directory (default: current dir; creates project/NAME)"
    )
    cmd_new.add_argument("--yes", action="store_true", help="run the new app immediately without asking")

    cmd_run = sub.add_parser("run", help="run an app file (default: the demo)")
    cmd_run.add_argument("path", nargs="?", default=None, help="python file to run")

    cmd_demo = sub.add_parser("demo", help="run the built-in demo")
    cmd_demo.add_argument("--headless", action="store_true", help="step without a terminal")
    cmd_demo.add_argument("--ticks", type=int, default=120, help="ticks for --headless")

    cmd_menu = sub.add_parser("menu", help="browse, open, archive, and delete projects")
    cmd_menu.add_argument("--dir", default=None, help="parent directory (default: current dir; scans DIR/project)")

    cmd_example = sub.add_parser("example", help="run a bundled example")
    cmd_example.add_argument("name", choices=["menu", "bouncer", "animation", "snake"])
    cmd_example.add_argument("--headless", action="store_true", help="step without a terminal")
    cmd_example.add_argument("--ticks", type=int, default=120, help="ticks for --headless")

    cmd_check = sub.add_parser("check", help="headless smoke check of the demo")
    cmd_check.add_argument("--ticks", type=int, default=60, help="ticks to step")

    cmd_list = sub.add_parser("list", help="list scene classes in an app file")
    cmd_list.add_argument("path", help="python file to inspect")

    cmd_install = sub.add_parser(
        "install",
        help="install Windfall as a uv tool from a source path",
        description=(
            "Install Windfall as a uv tool from SOURCE. By default SOURCE is '.' (the current "
            "directory), intended for use from a Windfall source checkout; pass an explicit "
            "source path when running elsewhere."
        ),
    )
    cmd_install.add_argument(
        "source",
        nargs="?",
        default=".",
        help="source path to install from (default: current directory)",
    )
    cmd_install.add_argument(
        "--force", action="store_true", help="reinstall if already installed"
    )

    sub.add_parser("uninstall", help="remove the installed Windfall uv tool cleanly")
    sub.add_parser("remove", help="remove the installed Windfall uv tool cleanly (alias for uninstall)")
    sub.add_parser("help", help="show this help")


def _cmd_new(args) -> int:
    try:
        target = Scaffolder(TEMPLATES_DIR).create(
            args.name, template=args.template, destination=args.dest
        )
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


class InstallSourceValidator:
    """Validate install source paths before invoking uv."""

    @staticmethod
    def is_valid(source: str) -> bool:
        """Return True if a local source path looks installable by uv/pip."""
        path = Path(source)
        try:
            if not path.exists():
                return False
            if path.is_file():
                return path.name in {"pyproject.toml", "setup.py", "setup.cfg"}
            if path.is_dir():
                return any(
                    (path / name).is_file()
                    for name in ("pyproject.toml", "setup.py", "setup.cfg")
                )
        except OSError:
            return False
        return False


class UvToolRunner:
    """Run uv tool commands with splash-inspired progress reporting."""

    def run(self, command: list[str], renderer: ProgressRenderer, run_phase: str) -> tuple[int, str]:
        stream = renderer.stream
        tty = bool(getattr(stream, "isatty", lambda: False)())
        if not tty:
            return self._run_plain(command, renderer, run_phase)
        return self._run_tty(command, renderer, run_phase)

    def _run_plain(
        self, command: list[str], renderer: ProgressRenderer, run_phase: str
    ) -> tuple[int, str]:
        renderer.emit(renderer.render_phase("prepare", tty=False))
        renderer.emit(renderer.render_phase(run_phase, tty=False))
        proc = subprocess.run(command, check=False, capture_output=True, text=True)
        renderer.emit(renderer.render_phase("verify", tty=False))
        detail = (proc.stderr or proc.stdout or "").strip()
        return proc.returncode, detail

    def _run_tty(
        self, command: list[str], renderer: ProgressRenderer, run_phase: str
    ) -> tuple[int, str]:
        stream = renderer.stream
        renderer.emit(renderer.render_phase("prepare", fraction=1.0, tty=True))
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        start = time.monotonic()
        duration = 2.5  # nominal animation window within the run phase
        while proc.poll() is None:
            elapsed = time.monotonic() - start
            fraction = min(0.95, elapsed / duration)
            line = renderer.render_phase(run_phase, fraction=fraction, tty=True)
            print(f"\r{line}", end="", file=stream, flush=True)
            time.sleep(0.08)
        stdout, stderr = proc.communicate()
        end_line = renderer.render_phase(run_phase, fraction=1.0, tty=True)
        print(f"\r{end_line}", end="", file=stream, flush=True)
        print(file=stream)
        renderer.emit(renderer.render_phase("verify", fraction=1.0, tty=True))
        detail = (stderr or stdout or "").strip()
        return proc.returncode, detail


class WindfallToolCommands:
    """Install/remove Windfall as a uv tool with consistent CLI UX."""

    def __init__(self, runner: UvToolRunner | None = None) -> None:
        self.runner = runner if runner is not None else UvToolRunner()

    def install(self, args) -> int:
        source = getattr(args, "source", ".")
        if not InstallSourceValidator.is_valid(source):
            print(
                f"windfall: install source '{source}' is not an installable Python project "
                "(expected a directory or file with pyproject.toml, setup.py, or setup.cfg). "
                "Run from a Windfall source checkout or pass an explicit source path.",
                file=sys.stderr,
            )
            return 2
        command = ["uv", "tool", "install", source]
        if getattr(args, "force", False):
            command.append("--force")
        renderer = ProgressRenderer(InstallProgressPlan, stream=sys.stdout)
        try:
            code, detail = self.runner.run(command, renderer, "install")
        except FileNotFoundError:
            print(
                "windfall: uv not found; cannot install Windfall (uv tool required).",
                file=sys.stderr,
            )
            return 2
        if code == 0:
            renderer.emit(renderer.render_success(InstallProgressPlan.success(source)))
            return 0
        renderer.emit(renderer.render_failure(InstallProgressPlan.failure()))
        if detail:
            print(detail, file=sys.stderr)
        return code

    def uninstall(self, _args) -> int:
        command = ["uv", "tool", "uninstall", "windfall"]
        renderer = ProgressRenderer(RemoveProgressPlan, stream=sys.stdout)
        try:
            code, detail = self.runner.run(command, renderer, "uninstall")
        except FileNotFoundError:
            print(
                "windfall: uv not found; cannot remove the Windfall tool (uv tool required).",
                file=sys.stderr,
            )
            return 2
        if code == 0:
            renderer.emit(renderer.render_success(RemoveProgressPlan.success()))
            return 0
        renderer.emit(renderer.render_failure(RemoveProgressPlan.failure()))
        if detail:
            print(detail, file=sys.stderr)
        return code


_TOOL_COMMANDS = WindfallToolCommands()


def _install_source_is_valid(source: str) -> bool:
    """Compatibility wrapper for install source validation."""
    return InstallSourceValidator.is_valid(source)


def _run_tool_command(
    command: list[str], renderer: ProgressRenderer, run_phase: str
) -> tuple[int, str]:
    """Compatibility wrapper for uv tool command execution with progress."""
    return _TOOL_COMMANDS.runner.run(command, renderer, run_phase)


def _cmd_install(args) -> int:
    return _TOOL_COMMANDS.install(args)


def _cmd_uninstall(_args) -> int:
    return _TOOL_COMMANDS.uninstall(_args)


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
    "install": _cmd_install,
    "uninstall": _cmd_uninstall,
    "remove": _cmd_uninstall,
    "help": _cmd_help,
}


if __name__ == "__main__":
    raise SystemExit(main())
