# Theming

## `Style` class

```python
from rich.style import Style

# Basic styling
s = Style(fg="green", bg="black", bold=True)

# Apply to rendering
canvas.print(x, y, "Hello", style=s)
```

**Predefined styles** (via `windfall.style`):

| Style | Used by |
|-------|---------|
| `Style.link` | Hyperlink-capable rendering |
| `Style.error` | Error messages |
| `Style.success` | Success states |

**Custom themes** — define your own `Style` objects and pass them to widgets via the scaffold config or `Style.link` for hyperlinks.

**Borders & borders:**

| Border style | Appearance |
|-------------|------------|
| `Style.border` | Standard box drawing |
| `Style.corner` | Corner characters |

**Background & foreground:**

| Role | Typical color |
|------|-------------|
| `fg="green"` | Widget text / labels |
| `bg="black"` | Background panel |
| `fg="yellow"` | Focus highlight / active state |