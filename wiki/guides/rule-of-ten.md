# Rule of Ten

Every class may define at most 10 methods (excluding `__init__`).

## Enforcement

The test suite enforces the budget with an `ast`-based audit
(`tests/budget.py`):

| Methods | Result |
| --- | --- |
| More than 10 | `[BUDGET-ERROR]` and the test fails |
| 9–10 | `[BUDGET-WARNING]` naming the class and methods |

## Staying inside the budget

- Split responsibilities: extract a helper class instead of adding an
  eleventh method.
- Prefer composition (a `Panel` holding widgets) over subclassing with
  more behavior.
- Run `uv run pytest -q` before pushing — the audit runs with the suite.
