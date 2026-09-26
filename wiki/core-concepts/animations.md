# Animations

## Primitives

| Primitive | Description |
|-----------|-------------|
| `Tween` | Interpolates a value between two endpoints over time |
| `Motion` | `Vec2` movement along a path |
| `Sequence` | Chained-step animation (step-by-step) |
| `Clock` | Deterministic, explicitly-advanced time |

## Usage

```python
from windfall.anim import Tween, Sequence, Clock

# Tween a value from 0 to 1 over 60 ticks
tween = Tween(0, 1, 60)

# Sequence of steps
seq = Sequence(
    Motion((0, 0), (10, 0), 10),   # move right 10 cells
    Motion((10, 0), (10, 10), 10), # move down 10 cells
)

# Clock for deterministic advancement
clock = Clock(fixed_dt=1/60)  # 60 FPS
while clock.advance():
    # update game state
```

## Timeline

A `Timeline` groups multiple `Motion`/`Tween` objects and advances them in sync with the engine tick.

**Example:** Animated windmill logo in boot splash uses `Tween` for color fade and `Timeline` for timing.