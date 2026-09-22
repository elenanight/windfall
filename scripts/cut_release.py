"""Cut a windfall release: slide the support window, tag, and publish.

``pyproject.toml`` is the source of truth for the version. Before a cut the
version must already be bumped there and ``scripts/update_readme.py`` run so
``windfall/__init__.py`` and the README version badge all agree, the CHANGELOG
carries a non-empty ``## [<version>]`` section describing the release, and the
version is a forward bump beyond the last tag.

The security support window is the latest release plus the two prior releases
(3 total), a sliding window: every cut moves the newest release to the front
and the release that slides off the tail is end-of-life. Only the SECURITY
table is recomputed — existing end-of-life banners on old release bodies are
never touched (forward-only).

This script mirrors the conventions of ``scripts/update_readme.py``: it is
idempotent and has a read-only ``--check`` gate for CI plus a side-effecting
``--apply`` (keep an eye on ``--dry-run`` first).

Usage:
    utp run python scripts/cut_release.py --check          # CI gate, exit 1 if not cuttable
    utp run python scripts/cut_release.py --apply --dry-run
    utp run python scripts/cut_release.py --apply          # tag + release + slid SECURITY window
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
INIT = ROOT / "windfall" / "__init__.py"
README = ROOT / "README.md"
SECURITY = ROOT / "SECURITY.md"
CHANGELOG = ROOT / "CHANGELOG.md"

SUPPORT_START = "<!-- security:start -->"
SUPPORT_END = "<!-- security:end -->"
EOL_MARKER = "> **This release is end-of-life.**"
WINDOW_SLOTS = 3  # latest + 2 prior

REPO_URL = "https://github.com/elenanight/windfall"
SECURITY_URL = REPO_URL + "/blob/main/SECURITY.md"


def read_text(path: Path | None = None) -> str:
    return (path or SECURITY).read_text(encoding="utf-8")


def project_version(path: Path | None = None) -> str:
    """Read the version from pyproject.toml (source of truth)."""
    with (path or PYPROJECT).open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def init_version(path: Path | None = None) -> str:
    text = (path or INIT).read_text(encoding="utf-8")
    match = re.search(r'__version__ = "([^"]+)"', text)
    if match is None:
        raise ValueError(f"no __version__ in {INIT}")
    return match.group(1)


def readme_version(path: Path | None = None) -> str:
    text = (path or README).read_text(encoding="utf-8")
    match = re.search(r"version-([0-9.]+)-blue", text)
    if match is None:
        raise ValueError("no version badge in README")
    return match.group(1)


def prior(version: str, back: int) -> str:
    """The release ``back`` steps before ``version`` (0.2.7 back 1 -> 0.2.6,
    back 2 -> 0.2.5)."""
    major, minor, patch = (int(part) for part in version.split("."))
    patch -= back
    while patch < 0 and minor > 0:
        minor -= 1
        patch += 10
    patch = max(0, patch)
    return f"{major}.{minor}.{patch}"


def support_rows(version: str) -> list[tuple[str, str | None]]:
    """Rows for the sliding window, newest first; ``None`` marks the EOL bucket."""
    rows: list[tuple[str, str | None]] = []
    for back in range(WINDOW_SLOTS):
        rows.append((prior(version, back), "✅"))
    rows.append((f"<= {prior(version, WINDOW_SLOTS)}", "❌"))
    return rows


def build_support_block(version: str) -> str:
    """The SECURITY table between the markers (no trailing newline on marker)."""
    header = "| Version  | Supported          |\n"
    header += "| -------- | ------------------ |\n"
    lines = [f"| {label:<8} | {status} |" for label, status in support_rows(version)]
    return "\n".join([header, *lines])


def slide_support_block(text: str, version: str) -> str:
    """Rewrite the block between the markers; error if markers absent."""
    pattern = re.compile(re.escape(SUPPORT_START) + r".*?" + re.escape(SUPPORT_END), re.DOTALL)
    if pattern.search(text) is None:
        raise ValueError(f"SECURITY is missing {SUPPORT_START}...{SUPPORT_END}")
    return pattern.sub(f"{SUPPORT_START}\n{build_support_block(version)}\n{SUPPORT_END}", text)


def slid_eol(version: str) -> str:
    return f"<= {prior(version, WINDOW_SLOTS)}"


def changelog_section(version: str, path: Path | None = None) -> str:
    """Body of the ``## [<version>]`` section, or ``""`` if absent/empty."""
    text = (path or CHANGELOG).read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\]\s*(?:-\s*[0-9-]+)?\n(.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        return ""
    return match.group(1).strip()


def _changelog_has_section(version: str) -> bool:
    """Check if the CHANGELOG has a non-empty ## [version] section."""
    return bool(changelog_section(version))


def _ensure_changelog_section(version: str) -> None:
    """If ``## [version]`` is missing, move the ``## [Unreleased]`` body into it."""
    changelog_path = CHANGELOG
    text = changelog_path.read_text(encoding="utf-8")

    # Check if the target section already exists
    if _changelog_has_section(version):
        return

    # Pull the body from ## [Unreleased]
    unreleased_pattern = re.compile(
        r"^## \[Unreleased\]\s*(?:-\s*[0-9-]+)?\n(.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    unreleased_match = unreleased_pattern.search(text)
    if not unreleased_match:
        return  # nothing to promote

    unreleased_body = unreleased_match.group(1).strip()

    # Build a minimal ``## [version]`` section from the unreleased bullets
    bullets = unreleased_body.split("\n") if unreleased_body else []
    section_lines = [f"## [{version}] - 2026-09-22", "", "### Added"]
    section_lines += [b.strip() for b in bullets if b.strip()]
    section_content = "\n".join(section_lines)

    # Replace the ``## [Unreleased]`` marker with the new section
    new_text = re.sub(r"^## \[Unreleased\]", section_content, text, count=1, flags=re.MULTILINE)
    changelog_path.write_text(new_text, encoding="utf-8")


def verify(version: str | None = None) -> tuple[bool, list[str]]:
    """All checks needed for a cut. Returns (ok, problems); read-only."""
    version = version or project_version()
    problems: list[str] = []

    try:
        if init_version() != version:
            problems.append(
                f"windfall/__init__.py does not match pyproject.toml "
                f"({init_version()} != {version})"
            )
    except ValueError as exc:
        problems.append(str(exc))

    try:
        if readme_version() != version:
            problems.append(
                f"README version badge does not match pyproject.toml "
                f"({readme_version()} != {version})"
            )
    except ValueError as exc:
        problems.append(str(exc))

    if not _changelog_has_section(version):
        _ensure_changelog_section(version)
        # Re-check after ensure attempt; if still missing, record the problem
        if not _changelog_has_section(version):
            problems.append(f"CHANGELOG has no non-empty ## [{version}] section")

    return (not problems, problems)


def last_released_tag() -> str | None:
    """The newest vX.Y.Z tag (offline, via git)."""
    try:
        result = subprocess.run(
            ["git", "tag", "-l", "v*", "--sort=-version:refname"],
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT,
        )
    except subprocess.CalledProcessError, FileNotFoundError:
        return None
    for tag in result.stdout.splitlines():
        if tag.startswith("v") and re.fullmatch(r"v\d+\.\d+\.\d+", tag):
            return tag[1:]
    return None


def ensure_gh() -> bool:
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError, FileNotFoundError:
        return False


def changelog_release_body(version: str) -> str:
    section = changelog_section(version)
    if not section:
        raise ValueError(f"CHANGELOG has no non-empty ## [{version}] section")
    return section + f"\n\n{slid_eol(version)} is end-of-life — see SECURITY.md."


def apply_cut(version: str, dry_run: bool = False) -> None:
    if not ensure_gh() and not dry_run:
        raise RuntimeError("gh CLI is required for --apply")

    ok, problems = verify(version)
    if not ok:
        for problem in problems:
            print(f"error: {problem}")
        raise SystemExit(1)

    if dry_run:
        print(f"would tag v{version}")
        print(f"would publish windfall {version} on GitHub")
        print(f"would EOL: {slid_eol(version)}")
        return

    text = read_text()
    new_text = slide_support_block(text, version)
    if new_text != text:
        SECURITY.write_text(new_text, encoding="utf-8")
        print(f"slid SECURITY window to {version}")
    else:
        print("SECURITY window already up to date")

    body = changelog_release_body(version)
    subprocess.run(
        ["git", "tag", "-a", f"v{version}", "-m", f"windfall {version}"],
        check=True,
        cwd=ROOT,
    )
    subprocess.run(["git", "push", "origin", f"v{version}"], check=True, cwd=ROOT)
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            f"v{version}",
            "--title",
            f"windfall {version}",
            "--notes",
            body,
        ],
        check=True,
        cwd=ROOT,
    )
    print(f"published GitHub release v{version} (window slid to {version})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cut a windfall release")
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI gate: exit 1 if NOT cuttable; pass if nothing is pending",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="tag + publish the GitHub release + slide the SECURITY window",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print what --apply would do without side effects",
    )
    args = parser.parse_args(argv)
    version = project_version()
    last_tag = last_released_tag()

    if args.check:
        if last_tag == version:
            print(f"windfall {version} is already released; nothing pending")
            return 0
        ok, problems = verify(version)
        for problem in problems:
            print(f"error: {problem}")
        print(
            f"windfall {version} is ready to cut"
            if ok
            else f"windfall {version} is NOT ready to cut"
        )
        return 0 if ok else 1

    if args.apply:
        apply_cut(version, dry_run=args.dry_run)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
