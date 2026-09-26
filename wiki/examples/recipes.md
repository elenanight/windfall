# Recipes

## Modal dialog

```python
from widgets import Button, Label
from engine import Engine

def show_modal():
    btn = Button("OK", on_press=lambda: engine.stop())
    engine.run(modal=True)  # modal blocks until engine.stop()
```

## Focus cycle

```python
# Cycle focus between widgets
focused = engine.focused
next_focus = engine.focus_next()
engine.focus = next_focus
```

**Example: form validation**

```python
from widgets import TextInput, Button, Label

def validate_form():
    name = TextInput("Enter name")
    submit = Button("Submit", on_press=lambda: engine.stop())
    engine.run(modal=True)
```