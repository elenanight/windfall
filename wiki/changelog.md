# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.9] - 2026-09-XX

### Added

- Widget guide: comprehensive reference for all Windfall widgets
- New `windfall example` CLI commands
- Auto-generated API reference in wiki/api/

### Changed

- Wiki restructured: all pages moved to `wiki/` directory
- CI: docs-check job added to verify auto-generated API docs

### Fixed

- Wiki repo sync: main repo `wiki/` is now source of truth
- Separate `windfall.wiki.git` repo archived

## [0.2.8] - 2026-09-14

### Added

- Boot splash: ASCII windmill logo fade-in with progress bar
- Snake rewrite: clean grid game (green snake / yellow food)
- Security window policy: sliding 3-release EOL window

### Changed

- CI workflow: Option A (`test → promote → release`)
- Security table: emoji ✅/❌, vertical rendering
- CHANGELOG: auto-promotion from `## [Unreleased]`

### Fixed

- Nested containers no longer tick widgets twice per frame
- Security window slide on every cut

## [0.2.7] - 2026-09-22

### Added

- Boot splash: ASCII windmill logo fade-in with progress bar
- Snake rewrite: clean grid game

### Fixed

- Nested containers no longer tick their widgets twice per frame

---

*Auto-generated from the CHANGELOG.md at the root of the repository.*