# Scaffolding

## `windfall new`

```bash
uv run windfall new myapp   # create project/ myapp interactively
uv run windfall new myapp --yes  # skip the yes prompt
```

**What gets created:**

- `project/myapp/` — project directory
- `project/myapp/app.py` — entry point with `Engine.make_header()` + `Engine.make_footer()`
- `project/myapp/.windfallrc.json` — persisted config (widget placement, themes)
- `project/myapp/README.md` — auto-generated docs

**Scaffold config** (`scaffold/config.json`):

```json
{
  "widgets": ["Label", "Button", "TextInput", "ListView", "Header", "Footer"],
  "theme": "default",
  "keys": {
    "add": "W",
    "remove": "R",
    "edit": "E",
    "quit": "Q"
  }
}
```

**Adding a custom widget** — edit the `widgets` list or create a new scaffold template.

**Running the app:**

```bash
cd project/myapp
uv run python app.py
```

**Verify:**

```bash
uv run windfall menu    # browse your new app
uv run python app.py    # run your app directly
```