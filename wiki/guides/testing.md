# Testing

## Headless mode

```bash
uv run pytest -q           # run test suite
uv run python -m pytest tests/  # alternative
```

**Engine step API:**

```python
engine = Engine()
engine.use_scene(scene)
engine.step(dt)              # advance by dt seconds
engine.post_event(event)     # inject custom event
```

**Example: scripted input**

```python
from engine import Engine
from scene import Scene
from widgets import Label

scene = Scene(Label("Hello"))
engine = Engine()
engine.use_scene(scene)

# 5 ticks, each 0.1s
for _ in range(5):
    engine.step(0.1)
```

**Headless runner** — see `tests/runner.py` for a minimal scripted runner.

## Integration tests

- Run `uv run pytest -q` to verify all widgets render without errors
- Run `uv run windfall menu` to verify the project manager UI
- Run `uv run python examples/snake.py` to verify the snake game