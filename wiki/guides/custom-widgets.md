# Custom Widgets

## Subclassing `Component`

```python
class MyWidget(Component):
    def __init__(self, x, y, width, height, label=""):
        super().__init__()
        self.rect = Vec2(width, height)
        self.label = label
        self.pos = Vec2(x, y)

    def draw(self, canvas, rect):
        # render into rich Cell
        canvas.print(rect.x, rect.y, self.label, style=Style(bold=True))

    def update(self, dt):
        # tick-based logic
        pass

    def handle_event(self, event):
        # keyboard / mouse events
        pass
```

**Tips:**

- `Component` provides `id`, `rect`, `rect` (position/size)
- `rich` styling via `Style(fg="green", bold=True)`
- `handle_event` receives events from `engine.handle_event()`

**Adding to Add palette:**

Edit the scaffold config or create a new scaffold template. The widget will appear automatically in the Add palette's widget list.