# Examples

```bash
uv run python examples/animation.py    # animation showcase
uv run python examples/snake.py       # grid snake game
uv run python examples/bouncer.py     # bouncer simulation
```

## Built-in examples

| Example | Description |
|---------|-------------|
| `animation` | Three dots racing under different easing and a yellow orbiter |
| `snake` | Clean grid game: steer with arrows, grow on food, restart with Enter |
| `bouncer` | Bouncing ball simulation with physics |

**Running via CLI:**

```bash
uv run windfall example animation    # or snake or bouncer
uv run windfall example --help       # show help
```

**CLI flags:**

```bash
uv run windfall example --headless    # headless mode
uv run windfall example --ticks N    # run for N ticks then exit
```