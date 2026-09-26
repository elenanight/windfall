# Contributing

Windfall welcomes contributions! Please follow these guidelines:

## Development workflow

1. **Fork the repo** and clone your fork
2. **Create a branch** `feature/X` or `fix/X` from `dev`
3. **Make changes** — follow the code style (see `CONTRIBUTING.md`)
4. **Run tests:** `uv run pytest -q`
5. **Run lint:** `uv run ruff check .`
6. **Commit** with a clear message
7. **Push** to your fork and open a PR against `dev`

## Code style

- Follow [Ruff](https://beta.ruff.format/) style
- Type hints where practical
- Docstrings for all public classes/methods
- `Component` subclasses must implement `draw`, `update`, `handle_event`

**Running tests:**

```bash
uv run pytest -q
```

**Running lint:**

```bash
uv run ruff check .
```

**Running the demo:**

```bash
uv run windfall menu    # project manager
uv run python examples/snake.py    # snake game
```

## Submitting changes

1. Ensure all tests pass (`uv run pytest -q`)
2. Ensure `ruff check .` passes
3. Open a PR against `dev` with a clear description
4. Reference any related issues (`#123`)

**Thank you for contributing!**