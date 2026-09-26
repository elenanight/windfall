# Quickstart

```bash
uv run windfall demo          # interactive demo
uv run windfall menu          # browse projects
uv run windfall menu --help   # show help
uv run python examples/animation.py  # animation showcase
uv run python examples/snake.py       # grid snake game
```

**First app scaffold:**

```bash
uv run windfall new myapp     # create project/ myapp
cd myapp
uv run python app.py          # run your app
```

**Verify:**

```bash
uv run windfall --version   # shows 0.2.x
uv run pytest -q             # run tests
```