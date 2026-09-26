# Layouts

## Container / Base class

```python
class Container(Component):
    def __init__(self, *children, **kwargs):
        super().__init__(**kwargs)
        self.children = list(children)
```

## Row

Lays out children horizontally with optional fill weights.

```python
Row(widget1, widget2, widget3, fill=[1, 2, 0])
```

**`fill`** — per-child weights for granular stretching.

## Column

Lays out children vertically.

```python
Column(widget1, widget2, widget3)
```

## Stack

Positions children stacked on top of each other.

```python
Stack(widget1, widget2, widget3)
```

## Center

 Centers its child widget with optional left/center/right alignment.

```python
Center(widget, align="center")  # "left" | "center" | "right"
```

## Comparison

| Layout | Direction | `fill` support | Typical use |
|--------|-----------|----------------|-------------|
| `Row` | Horizontal | Yes (per-child weights) | toolbar, button bar |
| `Column` | Vertical | No | forms, lists |
| `Stack` | Z-order | No | modals, overlays |
| `Center` | Centering | No | headers, footers |