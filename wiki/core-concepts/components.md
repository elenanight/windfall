# Component

## Lifecycle

```python
class MyWidget(Component):
    def draw(self, canvas, rect):        # render into rich Cell
        pass

    def update(self, dt):                # called every tick
        self._timer += dt
        while self._timer >= _TICK:
            self._timer -= _TICK
            self._move()

    def handle_event(self, event):       # key, mouse, control
        pass
```

**`Component.__init__`** — sets up `id`, `rect`, `rect`, `rect`.

**`Component.rect`** — `Vec2` (width, height) of the widget.

**`Component.id`** — unique identifier for focus/selection.

## Widget Catalog

| Widget | Purpose | Key methods |
|--------|---------|-------------|
| `Label` | Static text | `draw(rect, style)` |
| `TextInput` | Single-line input | `draw()`, `handle_event()` |
| `Button` | Save/Cancel, custom labels | `draw()`, `handle_event()` |
| `Hotkey` | Keyboard shortcut indicator | `draw(rect, style)` |
| `Header` | Bordered header bar | `draw()`, `handle_event()` |
| `Footer` | Mirrored footer bar | `draw()` |
| `ListView` | Scrollable list with focus | `draw()`, `handle_event()` |
| `HeaderEditor` | Panel with `TextInput` + `ListView` + Save/Cancel | `draw()` |
| `FooterEditor` | Panel for footer editing | `draw()` |
| `Panel` | Bordered container | `draw()` |
| `Center` | Centers child with alignment | `draw()` |
| `Row` | Horizontal layout with fill weights | `draw()` |
| `Column` | Vertical layout | `draw()` |
| `Stack` | Stacked children | `draw()` |
| `Container` | Base class for layout containers | `draw()` |

**`Component` base class** — located in `windfall/component.py`.

**`Widget`** — subclass of `Component` with rendering via `rich`.