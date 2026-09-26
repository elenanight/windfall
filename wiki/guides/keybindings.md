# Keybindings

## Default keyboard shortcuts

| Key | Action |
|-----|--------|
| `Up` / `Down` | Navigate focus up/down |
| `Left` / `Right` | Navigate focus left/right |
| `Enter` | Activate focused widget |
| `Esc` | Exit focus scope, restore prior focus |
| `W` | Add a new widget (project editor) |
| `R` | Remove a placed widget |
| `E` | Edit a placed widget |
| `Q` | Quit the editor / scaffold app |

**Custom hotkeys** — redefine in scaffold config or via `engine.bind()`:

```python
engine.bind("a", "add_widget")
engine.bind("r", "remove_widget")
```

**Scaffold config** (`.windfallrc.json`):

```json
{
  "keys": {
    "add": "W",
    "remove": "R",
    "edit": "E",
    "quit": "Q"
  }
}
```

**Default bindings** are defined in `engine.py` and can be overridden per-project.