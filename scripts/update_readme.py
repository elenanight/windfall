"""Keep the README version badges and roadmap in sync.

``pyproject.toml`` is the source of truth for the version. This script
regenerates the badge block between ``<!-- badges:start -->`` and
``<!-- badges:end -->`` in ``README.md`` so the version indicator always
matches, rewrites ``__version__`` in ``windfall/__init__.py`` to match,
and embeds the body of ``wiki/roadmap.md`` (the roadmap source of truth)
between ``<!-- roadmap:start -->`` and ``<!-- roadmap:end -->``.

Releasing:
    Bump the version in ``pyproject.toml`` and the ``[Unreleased]`` section
    in ``CHANGELOG.md``, then run this script (plus ``--check`` to verify):

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
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
README = ROOT / "README.md"
INIT = ROOT / "windfall" / "__init__.py"
ROADMAP = ROOT / "wiki" / "roadmap.md"

BADGES_START = "<!-- badges:start -->"
BADGES_END = "<!-- badges:end -->"
ROADMAP_START = "<!-- roadmap:start -->"
ROADMAP_END = "<!-- roadmap:end -->"

DEFAULT_SLUG = "elenanight/windfall"
REPO_URL = "https://github.com/elenanight/windfall"
RELEASES_URL = REPO_URL + "/releases"
COMMITS_URL = REPO_URL + "/commits"
PYTHON_DOWNLOADS = "https://www.python.org/downloads/"
CHANGELOG_URL = REPO_URL + "/blob/main/CHANGELOG.md"
ACTIONS_URL = REPO_URL + "/actions"
WORKFLOW_URL = REPO_URL + "/actions/workflows/ci.yml"
DEPENDABOT_URL = REPO_URL + "/security/dependabot"


def project_version(path: Path | None = None) -> str:
    """Read the released version from pyproject.toml."""
    with (path or PYPROJECT).open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def build_badges(slug: str, version: str) -> str:
    """Render the badge block for a repo slug and version.

    Badges flow left to right over two lines: identity and channel health
    first, then toolchain metadata with python next to dependencies.
    """
    first = [
        f"[![version](https://img.shields.io/badge/version-{version}-blue)]({RELEASES_URL})",
        f"[![stable](https://img.shields.io/github/actions/workflow/status/{slug}/ci.yml?branch=main&label=stable)]({WORKFLOW_URL}?query=branch%3Amain)",
        f"[![dev](https://img.shields.io/github/actions/workflow/status/{slug}/ci.yml?branch=dev&label=dev)]({WORKFLOW_URL}?query=branch%3Adev)",
        f"[![changelog](https://img.shields.io/badge/latest-changelog-orange)]({CHANGELOG_URL})",
    ]
    second = [
        f"[![python](https://img.shields.io/badge/python-3.14-3776AB)]({PYTHON_DOWNLOADS})",
        f"[![dependencies](https://img.shields.io/badge/dependencies-up%20to%20date-green)]({DEPENDABOT_URL})",
        f"[![last commit](https://img.shields.io/github/last-commit/{slug})]({COMMITS_URL})",
    ]
    body = "\n".join(first) + "\n\n" + "\n".join(second)
    return BADGES_START + "\n" + body + "\n" + BADGES_END


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


def roadmap_body(path: Path | None = None) -> str:
    """Body of ``wiki/roadmap.md`` minus its ``# Roadmap`` title line."""
    lines = (path or ROADMAP).read_text(encoding="utf-8").splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip("\n")


def update_roadmap(readme_path: Path | None = None, roadmap_path: Path | None = None) -> bool:
    """Embed the wiki roadmap body in README; return True if it changed."""
    readme = readme_path or README
    text = readme.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(ROADMAP_START) + r".*?" + re.escape(ROADMAP_END), re.DOTALL
    )
    if pattern.search(text) is None:
        raise ValueError(f"README is missing {ROADMAP_START}…{ROADMAP_END}")
    block = ROADMAP_START + "\n" + roadmap_body(roadmap_path) + "\n" + ROADMAP_END
    new_text = pattern.sub(block, text)
    if new_text == text:
        return False
    readme.write_text(new_text, encoding="utf-8")
    return True


def repo_slug() -> str:
    """Derive the owner/repo slug from the origin remote, if present.

    Only exact ``github.com`` hosts with an ``owner/repo`` path are
    accepted; anything else falls back to the default slug so a hostile
    remote URL can never leak into generated badge links.
    """
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
        host, _, path = url[4:].partition(":")
        if host != "github.com":
            return DEFAULT_SLUG
        slug = path
    else:
        try:
            parsed = urlparse(url if "://" in url else f"https://{url}")
        except ValueError:
            return DEFAULT_SLUG
        if parsed.hostname != "github.com":
            return DEFAULT_SLUG
        slug = parsed.path
    slug = slug.removesuffix(".git").strip("/")
    owner, _, repo = slug.partition("/")
    if not owner or not repo or "/" in repo:
        return DEFAULT_SLUG
    return f"{owner}/{repo}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync README badges and roadmap")
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
    roadmap_changed = update_roadmap()
    if readme_changed or init_changed or roadmap_changed:
        if args.check:
            print("README badges, __version__, or roadmap are out of date — run scripts/update_readme.py")
            return 1
        print(f"updated README badges, __version__, and roadmap to windfall {version}")
    else:
        print(f"README badges, __version__, and roadmap already match windfall {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())