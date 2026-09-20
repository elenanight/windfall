"""Keep the README version badges in sync with the released version.

``pyproject.toml`` is the source of truth for the version. This script
regenerates the badge block between ``<!-- badges:start -->`` and
``<!-- badges:end -->`` in ``README.md`` so the version indicator always
matches, and rewrites ``__version__`` in ``windfall/__init__.py`` to match.

Usage:
    uv run python scripts/update_readme.py            # apply changes
    uv run python scripts/update_readme.py --check    # exit 1 if changes are needed
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
README = ROOT / "README.md"
INIT = ROOT / "windfall" / "__init__.py"

BADGES_START = "<!-- badges:start -->"
BADGES_END = "<!-- badges:end -->"

DEFAULT_SLUG = "elenanight/windfall"
REPO_URL = "https://github.com/elenanight/windfall"


def project_version(path: Path | None = None) -> str:
    """Read the released version from pyproject.toml."""
    with (path or PYPROJECT).open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def build_badges(slug: str, version: str) -> str:
    """Render the badge block for a repo slug and version."""
    lines = [
        f"[![version](https://img.shields.io/badge/version-{version}-blue)]({REPO_URL})",
        f"[![license](https://img.shields.io/badge/license-MIT-green)]({REPO_URL})",
        f"[![python](https://img.shields.io/badge/python-3.14-3776AB)]({REPO_URL})",
        f"[![last commit](https://img.shields.io/github/last-commit/{slug})]({REPO_URL})",
        f"[![stars](https://img.shields.io/github/stars/{slug})]({REPO_URL})",
    ]
    return BADGES_START + "\n" + "\n".join(lines) + "\n" + BADGES_END


def update_readme(version: str, slug: str, path: Path | None = None) -> bool:
    """Rewrite the README badge block; return True if the file changed."""
    readme = path or README
    text = readme.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(BADGES_START) + r".*?" + re.escape(BADGES_END), re.DOTALL
    )
    if pattern.search(text) is None:
        raise ValueError(f"README is missing {BADGES_START}…{BADGES_END}")
    new_text = pattern.sub(build_badges(slug, version), text)
    if new_text == text:
        return False
    readme.write_text(new_text, encoding="utf-8")
    return True


def sync_init_version(version: str, path: Path | None = None) -> bool:
    """Align ``__version__`` in windfall/__init__.py; return True if it changed."""
    init = path or INIT
    text = init.read_text(encoding="utf-8")
    new_text, count = re.subn(
        r'__version__ = ".*?"', f'__version__ = "{version}"', text, count=1
    )
    if count == 0:
        raise ValueError(f"no __version__ assignment found in {init}")
    if new_text == text:
        return False
    init.write_text(new_text, encoding="utf-8")
    return True


def repo_slug() -> str:
    """Derive the owner/repo slug from the origin remote, if present."""
    try:
        url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return DEFAULT_SLUG
    if url.startswith("git@"):
        url = url.split(":", 1)[-1]
    slug = url.removesuffix(".git")
    if "github.com/" in slug:
        return slug.split("github.com/", 1)[-1].rstrip("/")
    return slug.rstrip("/")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync README badges with the released version")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report staleness and exit 1 instead of editing files",
    )
    args = parser.parse_args(argv)
    version = project_version()
    slug = repo_slug()
    readme_changed = update_readme(version, slug)
    init_changed = sync_init_version(version)
    if readme_changed or init_changed:
        if args.check:
            print("README badges or __version__ are out of date — run scripts/update_readme.py")
            return 1
        print(f"updated README badges and __version__ to windfall {version}")
    else:
        print(f"README badges and __version__ already match windfall {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())