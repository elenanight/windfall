# Architecture

## High-level overview

```text
┌──────────────────────────────────────────────────────────────┐
│                    Windfall Engine                         │
│  ┌───────────────┐  ┌────────────────────────────────────┐ │
│  │  Engine       │  │  Scene / Frame / FrameStack        │ │
│  └──────┬────────┘  └────────────────────────────────────┘ │
│           │                           │                 │
│           ▼                           ▼                 ▼
│    ┌───────┐                   ┌─────────────┐      ┌─────────┐
│    │ Engine  │                   │  Engine     │      │   Engine  │
│    │ loop    │                   │  loop       │      │  loop     │
│    └────┬────┘                   └──────┬──────┘      └──────┬────┘
│           │                           │                 │
│    ───────▼──────────────────────►──────────────────────►──────────►
│           │                           │                 │
│  events   │  ticks              │  focus      │  rendering
│           │                           │                 │
└──────────────────────────────────────────────────────────────┘
```

**Key concepts:**

- **Engine** — Owns raw mode, event loop (`Live`), tick-based advance (`step(dt)`)
- **Scene / Frame / FrameStack** — Tree navigation, focus cycling, history/undo
- **Component** — Base class: `draw()`, `update(dt)`, `handle_event()`
- **Widget** — `Component` subclass with `draw` + `rich` rendering
- **Layout** — `Container`, `Row`, `Column`, `Stack`, `Center` for positioning

**Tick-based model:**

```python
while self.alive:
    self._timer += dt
    while self._timer >= _TICK:
        self._timer -= _TICK
        self._move()          # e.g. snake, animatordraw()
```