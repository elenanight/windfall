"""Interactive project manager: browse, open, archive, and delete apps.

Lists the scaffolded apps under ``<base>/project`` (default: the current
directory) and offers one-key actions per project. Deleting asks for
confirmation inline; archiving moves the app aside under ``.archive``.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from windfall import (
    Button,
    Center,
    Column,
    Engine,
    Label,
    ListView,
    Panel,
    Row,
    Scene,
    TextInput,
)
from windfall.scene import focusables
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
    root_path = Path(base) if base is not None else Path.cwd()
    state: dict = {"projects": find_projects(root_path)}
    status = Label("Press New to scaffold your first app." if not state["projects"] else "")
    view = ListView(items=_names(state["projects"]))
    view.focus(True)
    actions = Row()
    body = Column()
    body.add(status)
    body.add(view)
    body.add(actions)
    dialog = Panel(body, title="Windfall - Projects", padding=1)
    root = Center()
    root.add(dialog)
    scene = Scene(name="menu", root=root)

    def refresh(message: str = "") -> None:
        state["projects"] = find_projects(base)
        view.set_items(_names(state["projects"]))
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

    def do_open() -> None:
        restore_actions()
        target = selected()
        if target is None:
            status.set_text("Nothing to open.")
            return
        print(f"Starting {target.name} ...")
        try:
            subprocess.run(["uv", "run", "python", "app.py"], cwd=target, check=False)
        except FileNotFoundError:
            status.set_text("`uv` not found; start the app manually.")
            return
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
    return scene


def main(root=None) -> int:
    """Run the project manager interactively for ``<root>/project``."""
    engine = Engine()
    engine.use_scene(build_menu(engine, root))
    engine.run()
    return 0
