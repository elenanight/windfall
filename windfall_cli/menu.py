"""Interactive project manager: browse, open, archive, and delete apps.

Lists the scaffolded apps under ``<base>/project`` (default: the current
directory) and offers one-key actions per project. Deleting asks for
confirmation inline; archiving moves the app aside under ``.archive``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import termios
import time
from pathlib import Path

from windfall import Button, Column, Engine, Hotkey, Label, ListView, Panel, Row, Scene, TextInput
from windfall.primitives import Box
from windfall.scene import focusables
from windfall.style import Style
from windfall_cli.scaffold import Scaffolder

TEMPLATES_DIR = Path(__file__).parent / "templates"
ARCHIVE_DIR = ".archive"
EMPTY = "(no projects yet)"


def find_projects(base=None) -> list[Path]:
    """Return scaffolded app dirs under ``<base>/project``, sorted by name."""
    root = Path(base) if base is not None else Path.cwd()
    root = root / "project"
    if not root.is_dir():
        return []
    return sorted(
        (
            path
            for path in root.iterdir()
            if path.is_dir() and not path.name.startswith(".") and (path / "app.py").is_file()
        ),
        key=lambda path: path.name,
    )


def _names(projects: list[Path]) -> list[str]:
    return [project.name for project in projects] or [EMPTY]


def build_menu(engine: Engine, base=None) -> Scene:
    """Assemble the project manager scene for ``<base>/project``."""
    from windfall import __version__

    root_path = Path(base) if base is not None else Path.cwd()
    state: dict = {"projects": find_projects(root_path)}
    header = engine.make_header("Windfall - Projects", border="cyan", fg="bright_white")
    status = Label("Press New to scaffold your first app." if not state["projects"] else "")
    view = ListView(items=_names(state["projects"]))
    view.focus(True)
    actions = Row()
    main = Column()
    main.add(status)
    main.add(view)
    main.add(actions)
    main.add(Label("N new · O open · D delete · A archive · X quit · arrows move · Enter activate", align="center"))
    info = Column()
    info.add(Label(f"Windfall {__version__}", align="center"))
    info_count = Label("", align="center")
    info.add(info_count)
    count = len(state["projects"])
    info_count.set_text(f"{count} project" + ("" if count == 1 else "s"))
    aside = Column()
    aside.add(Panel(info, title="Info", padding=1))
    body = Row(fill=True, weights=[1, 0])
    body.add(main)
    body.add(aside)
    credit = Row()
    credit.add(Label("Built with Windfall by Elena Burt · "))
    credit.add(
        Label(
            "github.com/elenanight/windfall",
            style=Style(
                fg="cyan",
                underline=True,
                link="https://github.com/elenanight/windfall",
            ),
        )
    )
    footer = Box(credit, border_style=Style(fg="cyan"), padding=0)
    root = Column()
    root.add(header)
    root.add(body)
    root.add(footer)
    scene = Scene(name="menu", root=root)

    def refresh(message: str = "") -> None:
        state["projects"] = find_projects(root_path)
        view.set_items(_names(state["projects"]))
        count = len(state["projects"])
        info_count.set_text(f"{count} project" + ("" if count == 1 else "s"))
        status.set_text(message)

    def selected() -> Path | None:
        projects = state["projects"]
        index = view.selection
        if not projects or index >= len(projects):
            return None
        return projects[index]

    def restore_actions() -> None:
        if state.get("form") is not None:
            body.remove(state["form"])
            state["form"] = None
        actions.clear()
        for child in action_buttons:
            child.focus(False)
            actions.add(child)

    def show_new_form() -> None:
        restore_actions()
        field = TextInput()
        create = Button("Create", on_activate=lambda: do_create(field))
        cancel = Button("Cancel", on_activate=restore_actions)
        form = Column()
        namerow = Row(fill=True, weights=[0, 1])
        namerow.add(Label("Name:"))
        namerow.add(field)
        btnrow = Row()
        btnrow.add(create)
        btnrow.add(cancel)
        form.add(namerow)
        form.add(btnrow)
        state["form"] = form
        body.add(form)
        for widget in focusables(scene.root):
            widget.focus(False)
        field.focus(True)

    def do_create(field: TextInput) -> None:
        name = field.value.strip()
        try:
            Scaffolder(TEMPLATES_DIR).create(name, destination=root_path)
        except (ValueError, FileExistsError, FileNotFoundError) as error:
            status.set_text(f"Could not create: {error}")
            return
        refresh(f"Created {name}.")
        restore_actions()

    def show_confirm(target: Path) -> None:
        actions.clear()
        actions.add(Label(f"Delete {target.name}?"))
        yes = Button("Yes", on_activate=lambda: do_delete(target))
        no = Button("No", on_activate=restore_actions)
        actions.add(yes)
        actions.add(no)
        for widget in focusables(scene.root):
            widget.focus(False)
        yes.focus(True)

    def _detach_stdin() -> int | None:
        """Hand the terminal to the child app exclusively.

        Points our stdin at /dev/null so our blocked pump thread exits on
        EOF instead of racing the child's reader for keystrokes. Returns a
        dup of the real terminal that the child must inherit explicitly via
        ``stdin=`` (it must NOT rely on inheriting fd 0). Returns None
        when stdin is not a terminal.
        """
        try:
            if not os.isatty(0):
                return None
            saved = os.dup(0)
        except OSError:
            return None
        try:
            null = os.open(os.devnull, os.O_RDONLY)
        except OSError:
            os.close(saved)
            return None
        try:
            os.dup2(null, 0)
        finally:
            os.close(null)
        engine.input.close()
        return saved

    def _restore_stdin(saved: int | None) -> None:
        """Take the terminal back: restore stdin, flush type-ahead, resume."""
        if saved is None:
            return
        try:
            os.dup2(saved, 0)
        finally:
            os.close(saved)
        try:
            termios.tcflush(0, termios.TCIFLUSH)
        except OSError:
            pass
        engine.input.open()

    def do_open() -> None:
        restore_actions()
        target = selected()
        if target is None:
            status.set_text("Nothing to open.")
            return
        print(f"Starting {target.name} ...")
        saved = _detach_stdin()
        try:
            proc = subprocess.Popen(
                ["uv", "run", "python", "app.py"],
                stdin=saved if saved is not None else None,
                cwd=target,
            )
            proc.wait()
        except FileNotFoundError:
            status.set_text("`uv` not found; start the app manually.")
            return
        finally:
            _restore_stdin(saved)
        refresh(f"Back from {target.name}.")

    def request_delete() -> None:
        restore_actions()
        target = selected()
        if target is None:
            status.set_text("Nothing to delete.")
            return
        show_confirm(target)

    def do_archive() -> None:
        restore_actions()
        target = selected()
        if target is None:
            status.set_text("Nothing to archive.")
            return
        archive = target.parent / ARCHIVE_DIR
        archive.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        dest = archive / f"{target.name}-{stamp}"
        counter = 1
        while dest.exists():
            counter += 1
            dest = archive / f"{target.name}-{stamp}-{counter}"
        try:
            shutil.move(str(target), str(dest))
        except OSError as error:
            status.set_text(f"Could not archive {target.name}: {error}")
            return
        refresh(f"Archived {target.name}.")

    def do_delete(target: Path) -> None:
        try:
            shutil.rmtree(target)
        except OSError as error:
            status.set_text(f"Could not delete {target.name}: {error}")
            restore_actions()
            return
        refresh(f"Deleted {target.name}.")
        restore_actions()

    new_btn = Button("New", on_activate=show_new_form)
    open_btn = Button("Open", on_activate=do_open)
    delete_btn = Button("Delete", on_activate=request_delete)
    archive_btn = Button("Archive", on_activate=do_archive)
    quit_btn = Button("Quit", on_activate=engine.stop)
    action_buttons = [new_btn, open_btn, delete_btn, archive_btn, quit_btn]
    restore_actions()

    def focus_button(target) -> None:
        for widget in focusables(scene.root):
            widget.focus(False)
        target.focus(True)

    root.add(Hotkey("n", on_press=lambda: focus_button(new_btn)))
    root.add(Hotkey("o", on_press=lambda: focus_button(open_btn)))
    root.add(Hotkey("d", on_press=lambda: focus_button(delete_btn)))
    root.add(Hotkey("a", on_press=lambda: focus_button(archive_btn)))
    root.add(Hotkey("x", on_press=engine.stop))
    return scene


def main(root=None) -> int:
    """Run the project manager interactively for ``<root>/project``."""
    engine = Engine()
    engine.use_scene(build_menu(engine, root))
    engine.run()
    farewell()
    return 0


def farewell() -> None:
    """Clear the screen, then print the shutdown line on the fresh terminal."""
    print("\033[2J\033[H", end="")
    print("Thanks for using Windfall. Goodbye!")
