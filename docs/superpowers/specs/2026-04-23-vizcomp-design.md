# Design: `vizcomp` — Multi-Case MainResults Comparison Module

**Date:** 2026-04-23  
**Status:** Approved

---

## Overview

Add `src/postgenesis/vizcomp.py` to enable side-by-side visual comparison of multiple Genesis main result files (`MainResults`). This sits between `singlecase.py` (one file) and `cluster.py` / `vizdfscan.py` (mass batch + scan visualization), targeting a curated set of files the user wants to compare directly.

---

## Architecture

### File

`src/postgenesis/vizcomp.py`

Naming follows existing convention (`vizdfscan.py` = viz + df + scan → `vizcomp.py` = viz + comp).

### Module layout

```
vizcomp.py
├── _load_case(x) -> MainResults          # auto-detect: path or object
├── _auto_label(gmr) -> str               # extract label from file_basename
└── class CaseComparison
    ├── __init__(cases, labels=None)       # load + cache all MainResults
    ├── plot_zevo(yattrs, ...)             # z-evolution overlay
    └── plot_zslice(yattrs, z=None, ...)  # z-slice profile overlay
```

Reuses `colmr` (the `ColumnMetaRegistry` instance) from `singlecase.py` for axis labels and unit auto-scaling. No duplication.

---

## Components

### `_load_case(x) -> MainResults`

Accepts `str`, `Path`, or `MainResults`. If a path, constructs `MainResults(x)`. If already a `MainResults`, returns as-is.

### `_auto_label(gmr) -> str`

Extracts a short label from `gmr.file_basename`. For example `g4.seed001.out.h5` → `seed001`. Falls back to the full basename if the pattern doesn't match.

---

## `CaseComparison`

### `__init__`

```python
CaseComparison(
    cases: list[str | Path | MainResults],
    labels: list[str] | None = None,
)
```

- Iterates `cases`, calls `_load_case` on each, stores as `self.cases: list[MainResults]`.
- If `labels` is `None`, calls `_auto_label` for each case.
- Raises `ValueError` if `labels` length does not match `cases` length.
- Stores result as `self.labels: list[str]`.

---

### `plot_zevo`

```python
def plot_zevo(
    self,
    yattrs: list[str],
    *,
    sharex: bool = True,
    sharey: bool = False,
    fig: plt.Figure | None = None,
    axes: np.ndarray | None = None,
    **pltkwargs,
) -> tuple[plt.Figure, np.ndarray]:
```

**Purpose:** Overlay z-evolution curves for multiple cases on shared axes.

**Layout:** `(len(yattrs), 1)` subplots, vertical stack, `sharex='all'` when `sharex=True`.

**x axis:** Fixed to `zplot`. Label and unit come from `colmr`. Auto-scaled with `xtils.get_autoscale`.

**Per subplot:** One line per case (matplotlib default color cycle), legend entries from `self.labels`. `colmr` provides y-axis label, unit, and auto-scaling.

**Returns:** `(fig, axes)` where `axes` has shape `(len(yattrs),)`.

---

### `plot_zslice`

```python
def plot_zslice(
    self,
    yattrs: list[str],
    *,
    z: float | list[float] | None = None,
    xattr: str = 't_from_s',
    sharex: bool = True,
    sharey: bool = False,
    fig: plt.Figure | None = None,
    axes: np.ndarray | None = None,
    **pltkwargs,
) -> tuple[plt.Figure, np.ndarray]:
```

**Purpose:** Overlay z-slice profiles for multiple cases.

**z handling:**
- `None` → uses last z (`zplot[-1]`) for all cases.
- Single float → one figure, layout `(len(yattrs), 1)`.
- List of floats → one figure, layout `(len(yattrs), len(z))`; column titles show the actual z value used (nearest grid point).

**Data extraction:** `gmr.get_data_at_z(yattr, z)` for each case and each z.

**x axis:** `getattr(gmr, xattr)`. Default `'t_from_s'`. Label/unit from `colmr`. Auto-scaled with `xtils.get_autoscale`.

**Per subplot:** One line per case, same color/legend convention as `plot_zevo`.

**Returns:** `(fig, axes)` where `axes` has shape `(len(yattrs),)` for single z, or `(len(yattrs), len(z))` for multiple z.

---

## Data Flow

```
User input: list[path | MainResults], optional labels
        ↓
CaseComparison.__init__
  _load_case  →  list[MainResults] (cached)
  _auto_label →  list[str] (labels)
        ↓
plot_zevo / plot_zslice
  colmr       →  axis labels, units
  get_autoscale → scale + SI prefix
  ax.plot()   →  one line per case
        ↓
(fig, axes)
```

---

## Error Handling

- `_load_case`: raises `TypeError` for unrecognized input types.
- `__init__`: raises `ValueError` if `labels` length mismatches `cases`.
- `plot_zevo`: expects `yattr` to be 1-D over `zplot` (e.g. `zenergy`, `peakpower`). If the attribute shape does not match `len(zplot)`, `get_data_at_z` raises `ValueError` — let it propagate.
- `plot_zslice`: expects `yattr` to be 2-D with shape `[n_z, n_slice]` (e.g. `intfar`, `power`, `bunching`). Passing a 1-D quantity (e.g. `zenergy`) produces a scalar after `get_data_at_z`, which cannot be plotted; `plot_zslice` raises `ValueError` with a clear message if the extracted data is not a 1-D array.
- No silent fallbacks for missing attributes — let `MainResults` raise naturally.

---

## Testing

- Unit test `_load_case` with a path, a `Path`, and a `MainResults` object.
- Unit test `_auto_label` for standard filenames and edge cases.
- Integration test `plot_zevo` with 2 cases, 2 yattrs — verify figure shape and legend count.
- Integration test `plot_zslice` with single z and list z — verify axes shape `(n_yattrs,)` vs `(n_yattrs, n_z)`.
- Use the existing test CSV fixture (`tests/data/001.g4.000.out.h5.csv`) pattern for lightweight test data.
