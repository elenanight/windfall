# Installation

```bash
uv sync           # install dependencies
uv run windfall new myapp  # scaffold a new app
cd myapp && uv run python app.py  # run your app
```

**Requirements:**

- Python **3.14** (via `pyproject.toml`)
- Runtime dependencies: `rich`, `readchar`

**Optional:** `uv` for tooling, `gh` CLI for release cutting.