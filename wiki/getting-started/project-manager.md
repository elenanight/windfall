# Project Manager (windfall menu)

```bash
uv run windfall menu               # open project TUI
uv run windfall menu --dir /path   # specify directory
uv run windfall menu --help        # show help
```

**Available actions:**

| Key | Action |
|-----|--------|
| `W` | Add a new widget |
| `R` | Remove a widget |
| `E` | Edit a placed widget |
| `Q` | Quit the editor |

**Project structure:**

```text
project/myapp/
├── .windfallrc.json   # persisted config
├── app.py               # app entry point
├── assets/            # images/icons
└── data/              # persistent state
```