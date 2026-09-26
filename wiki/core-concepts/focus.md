# Focus

## Focus scopes

`set_focus_scope(scope)` / `clear_focus_scope()` — trap arrow-key focus inside an open editor panel and restore prior focus.

**Behavior:**

- When an editor panel opens, focus is trapped within its bounds
- Arrow keys navigate between widgets
- `Esc` or closing the panel restores prior focus
- Focus ring visuals appear on the focused widget

## Key bindings

| Key | Action |
|-----|--------|
| `Up` / `Down` | Navigate focus up/down |
| `Left` / `Right` | Navigate focus left/right (within scope) |
| `Enter` | Activate focused widget |
| `Esc` | Exit focus scope, restore prior focus |

**Default bindings** are defined in `engine.py` and can be customized via the scaffold config.

**Example:** Focus traps within `HeaderEditor` panel, allowing `Tab`/`Shift-Tab` to cycle between `TextInput` and `ListView`.