# Windfall Widget Guide

Welcome to the Windfall widget documentation. This page lists all available widgets you can use in your project editor, along with their purpose and basic usage, and serves as the landing page for the wiki.

## Available Widgets

The following widgets are available for use in scaffolded apps via the project editor's Add palette:

### Labels & Inputs

- **Label** — Displays static text. Can be colored and styled.
- **TextInput** — Single-line text input field with focus support.
- **Header** — A bordered header bar typically placed at the top of an app.
- **Footer** — A mirrored footer bar placed at the bottom of an app.

### Buttons & Controls

- **Button** — Clickable button with Save/Cancel or custom labels. Wired to `engine.stop` or custom hotkeys.
- **Hotkey** — Displays a keyboard shortcut indicator (e.g., `A`/`E`/`Q`).

### Lists & Views

- **ListView** — A scrollable list of items. Items can be focused, activated with Enter, and support hotkey navigation.
- **HeaderEditor** — Panel containing a `Header` widget with `TextInput` + `ListView` for header bar editing, including Save/Cancel buttons.
- **FooterEditor** — Panel for footer bar editing (similar structure to HeaderEditor).

### Layout & Containers

- **Panel** — A bordered container box that groups widgets together.
- **Center** — Centers its child widget with optional left/center/right alignment.
- **Row** — Lays out children horizontally with optional fill weights.
- **Column** — Lays out children vertically.
- **Stack** — Positions children stacked on top of each other.
- **Container** — Base class for layout containers (`Column`, `Row`, `Stack`, `Center`).

### Scaffold & Project Management

- **AddWidget** — Palette widget for adding new widgets to the project content area. Supports placement options (left/center/right/full/sidebar) and persistence to config.
- **RemoveWidget** — Panel for listing and deleting placed widgets.
- **EditMenu** — Menu with shortcuts: `W` add, `R` remove, `E` edit, `Q` quit.

## How to Use

1. Run `windfall menu` to open the project manager.
2. Use the **Add** (`W`) button in the editor to open the widget palette.
3. Select a widget type — it will be placed in the content area and persisted to `.windfallrc.json`.
4. Use **Edit** (`E`) to modify placed widgets' properties (visibility, alignment, etc.).
5. Use **Remove** (`R`) to delete a widget from the project.

## Adding a New Widget

If you want to add a custom widget:

1. Subclass `Component` in `windfall/widgets.py` (or your app's module).
2. Implement `draw()`, `update(dt)`, and optional `handle_event()`.
3. Add the widget to the Add palette by editing the scaffold config or creating a new scaffold template.
4. The widget will appear in the Add palette's widget list automatically.

## Documentation

Full documentation is available in the wiki:

- **[Getting Started](wiki/getting-started/installation.md)** — Installation, quickstart, project manager
- **[Core Concepts](wiki/core-concepts/architecture.md)** — Architecture, components, layouts, animations, focus
- **[Guides](wiki/guides/)** — Custom widgets, theming, keybindings, scaffolding, testing
- **[Examples](wiki/examples.md)** — Built-in examples: animation, snake, bouncer
- **[Recipes](wiki/examples/recipes.md)** — Modal dialog, focus cycle, form validation
- **[Contributing](wiki/contributing.md)** — How to contribute, code style, test runner
- **[Roadmap](wiki/roadmap.md)** — What's shipped, what's planned

---

*This guide lives in the [wiki on GitHub](https://github.com/elenanight/windfall/wiki).*