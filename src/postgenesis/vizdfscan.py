#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 10 21:36:38 2026

@author: duoxup
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Union, IO, Tuple, Sequence, List

import pandas as pd
import numpy as np
from xtils import get_autoscale

import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from math import ceil

Formatter = Callable[[Any], str]
AggFunc = Union[str, Callable[[pd.Series], float]]
PathLike = Union[str, Path]


def _is_na(x: Any) -> bool:
    try:
        return bool(pd.isna(x))
    except Exception:
        return x is None


def _json_friendly_number(x: Any) -> Any:
    """
    Convert numpy / pandas scalar-ish numbers to Python built-ins for JSON.
    """
    if hasattr(x, "item") and callable(getattr(x, "item")):
        try:
            return x.item()
        except Exception:
            return x
    return x


@dataclass(frozen=True)
class ColumnMeta:
    name: str
    axis_label: Optional[str] = None
    alias: Optional[str] = None
    unit: Optional[str] = None
    scale: float = 1.0
    offset: float = 0.0
    digits_show: Optional[int] = None
    fmt: Optional[str] = None
    formatter: Optional[Formatter] = None  # not JSON-serializable by default

    def title_key(self) -> str:
        return self.alias or self.name

    def axis_text(self) -> str:
        base = self.axis_label or self.alias or self.name
        if self.unit:
            return f"{base} [{self.unit}]"
        return base

    def legend_title(self) -> str:
        return self.axis_label or self.alias or self.name

    def transform_value(self, x: Any) -> Any:
        if _is_na(x):
            return np.nan
        try:
            return float(x) * self.scale + self.offset
        except Exception:
            return x

    def format_value(self, x: Any) -> str:
        if self.formatter is not None:
            return self.formatter(x)

        if _is_na(x):
            return "NaN"

        try:
            v = float(x) * self.scale + self.offset
            if self.fmt is not None:
                s = format(v, self.fmt)
            elif self.digits_show is not None:
                s = f"{v:.{self.digits_show}f}"
            else:
                s = f"{v:.6g}"
        except Exception:
            s = str(x)

        if self.unit:
            s += self.unit
        return s

    def to_dict(self, *, include_formatter: bool = False) -> Dict[str, Any]:
        d = asdict(self)

        for k in ("axis_label", "alias", "unit", "fmt"):
            if isinstance(d.get(k), str) and d[k].strip() == "":
                d[k] = None

        d["scale"] = float(_json_friendly_number(d.get("scale", 1.0)))
        d["offset"] = float(_json_friendly_number(d.get("offset", 0.0)))
        if d.get("digits_show", None) is not None:
            try:
                d["digits_show"] = int(_json_friendly_number(d["digits_show"]))
            except Exception:
                d["digits_show"] = None

        if include_formatter:
            raise TypeError(
                "ColumnMeta.formatter is not JSON-serializable. "
                "Store formatting via (scale/offset/digits_show/fmt) or inject formatter at runtime."
            )
        d["formatter"] = None

        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> ColumnMeta:
        allowed = {
            "name", "axis_label", "alias", "unit", "scale", "offset",
            "digits_show", "fmt", "formatter"
        }
        clean: Dict[str, Any] = {k: d[k] for k in d.keys() if k in allowed}

        for k in ("axis_label", "alias", "unit", "fmt"):
            if isinstance(clean.get(k), str) and clean[k].strip() == "":
                clean[k] = None

        if "scale" in clean and clean["scale"] is not None:
            clean["scale"] = float(clean["scale"])
        if "offset" in clean and clean["offset"] is not None:
            clean["offset"] = float(clean["offset"])
        if "digits_show" in clean and clean["digits_show"] is not None:
            clean["digits_show"] = int(clean["digits_show"])

        clean["formatter"] = None

        if "name" not in clean or not isinstance(clean["name"], str) or not clean["name"].strip():
            raise ValueError("ColumnMeta.from_dict: missing or invalid 'name'.")

        return cls(**clean)


class ColumnMetaRegistry:
    """
    Central registry for ColumnMeta.

    JSON schema (versioned):
    {
      "type": "ColumnMetaRegistry",
      "version": 1,
      "metas": {
        "<col>": { ... ColumnMeta dict ... },
        ...
      }
    }
    """
    _TYPE = "ColumnMetaRegistry"
    _VERSION = 1

    def __init__(self, metas: Optional[Mapping[str, ColumnMeta]] = None):
        self._metas: Dict[str, ColumnMeta] = dict(metas or {})

    def add(self, meta: ColumnMeta) -> None:
        self._metas[meta.name] = meta

    def get(self, col: str) -> ColumnMeta:
        return self._metas.get(col, ColumnMeta(name=col))

    def to_dict(self) -> Dict[str, Any]:
        metas_dict = {k: v.to_dict(include_formatter=False) for k, v in self._metas.items()}
        return {
            "type": self._TYPE,
            "version": self._VERSION,
            "metas": metas_dict,
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> ColumnMetaRegistry:
        if d.get("type", None) not in (None, cls._TYPE):
            raise ValueError(f"ColumnMetaRegistry.from_dict: unexpected type={d.get('type')}")

        version = d.get("version", cls._VERSION)
        if version != cls._VERSION:
            raise ValueError(
                f"ColumnMetaRegistry.from_dict: unsupported version={version}. "
                f"Expected version={cls._VERSION}."
            )

        metas_in = d.get("metas", {})
        if not isinstance(metas_in, Mapping):
            raise ValueError("ColumnMetaRegistry.from_dict: 'metas' must be a mapping.")

        metas: Dict[str, ColumnMeta] = {}
        for col, meta_dict in metas_in.items():
            if not isinstance(meta_dict, Mapping):
                continue
            cm = ColumnMeta.from_dict(meta_dict)
            metas[str(col)] = cm

        return cls(metas)

    def to_json(
        self,
        path_or_fp: Union[PathLike, IO[str]],
        *,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> None:
        payload = self.to_dict()

        if hasattr(path_or_fp, "write"):
            json.dump(payload, path_or_fp, indent=indent, ensure_ascii=ensure_ascii)
            return

        path = Path(path_or_fp)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=indent, ensure_ascii=ensure_ascii)

    @classmethod
    def from_json(cls, path_or_fp: Union[PathLike, IO[str]]) -> ColumnMetaRegistry:
        if hasattr(path_or_fp, "read"):
            data = json.load(path_or_fp)
            return ColumnMetaRegistry.from_dict(data)

        path = Path(path_or_fp)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return ColumnMetaRegistry.from_dict(data)


# ----------------------------
# Plotting
# ----------------------------

@dataclass(frozen=True)
class PlotScanConfig:
    # layout
    ncols: int = 3
    figsize_per_ax: Tuple[float, float] = (4.8, 3.6)
    sharex: bool = False
    sharey: bool = False

    # data handling
    sort_x: bool = True
    agg: Optional[AggFunc] = None            # handle duplicate x points
    dropna_facets: bool = False              # drop NA rows when forming facet combos
    apply_meta_transform_to_data: bool = True  # scale x/y plotted values by meta

    # labeling overrides (if None, use meta/col)
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    label_prefer_alias: bool = False         # prefer alias over axis_label in axis labels

    # titles
    title_vars: Optional[Sequence[str]] = None  # default: facet_vars
    title_sep: str = ", "
    title_show_keys: bool = True             # show "key=value"; False shows value only

    # legend (line mode)
    legend: bool = True
    legend_loc: str = "best"

    # hue ordering (line mode)
    hue_order: Optional[Sequence[Any]] = None

    # contour mode options
    contour_levels: Optional[int] = None     # number of contour levels; None -> auto (10)
    contour_filled: bool = True              # True: contourf, False: contour lines only
    contour_labels: bool = False             # annotate contour lines with clabel

    # metadata
    meta: Optional[ColumnMetaRegistry] = None


def _meta_key(col: str) -> str:
    # e.g. "sig_x@z=0.5" -> "sig_x"
    return str(col).split("@", 1)[0]


# ----------------------------
# Convenience helpers
# ----------------------------

def make_registry(spec: Mapping[str, Mapping[str, Any]]) -> ColumnMetaRegistry:
    """
    Build a registry from a simple dict spec.

    Example:
    spec = {
        "Q_total": {"unit": "pC", "axis_label": "Bunch charge", "alias": "Q", "scale": 1e12, "digits_show": 2},
        "sig_z": {"unit": "mm", "axis_label": "Bunch length (rms)", "scale": 1e3, "digits_show": 2},
    }
    """
    reg = ColumnMetaRegistry()
    for col, cfg in spec.items():
        reg.add(ColumnMeta(name=col, **cfg))
    return reg


def plot_scan_facets(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    hue: Optional[str] = None,
    facet_vars: Optional[Sequence[str]] = None,
    config: PlotScanConfig = None,
    mode: str = "line",               # "line", "heatmap", or "contour"
    colorbar: str = "each",           # "each" | "row" | "col" | "all" (heatmap/contour only)
    cmap: Optional[str] = None,
    no_autoscale: Optional[Sequence[str]] = None,
) -> Tuple[plt.Figure, np.ndarray]:
    """
    Faceted plotting for multi-parameter scan results in a pandas DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
    x, y : str
        In line mode: x-axis and y-axis variables.
        In heatmap/contour mode: x-axis variable and z-axis (color) variable respectively.
    hue : str | None
        In line mode: grouping variable (one line per hue value).
        In heatmap/contour mode: y-axis variable of the 2-D grid. Required.
    facet_vars : Sequence[str] | None
        Variables used to create facets (one subplot per unique combination).
    config : PlotScanConfig
        Must be provided.
    mode : str
        "line", "heatmap", or "contour".
    colorbar : str
        Colorbar sharing for heatmap/contour: "each", "row", "col", or "all".
    cmap : str | None
        Colormap name. If None, matplotlib default is used.
    no_autoscale : Sequence[str] | None
        Column names that should not be auto-scaled.

    Returns
    -------
    fig, axes_2d
    """
    if config is None:
        raise ValueError("config must be provided (PlotScanConfig).")

    facet_vars = list(facet_vars or [])

    # ------------------------------------------------------------------ #
    # Local helpers
    # ------------------------------------------------------------------ #
    def _ensure_columns_exist(cols: Sequence[Optional[str]]) -> None:
        cols2 = [c for c in cols if c]
        missing = [c for c in cols2 if c not in df.columns]
        if missing:
            raise KeyError(f"DataFrame is missing columns: {missing}")

    def _unique_facet_combinations(
        facet_vars_: Sequence[str],
        dropna: bool,
    ) -> List[Tuple[Any, ...]]:
        if not facet_vars_:
            return [tuple()]
        sub = df.loc[:, facet_vars_]
        if dropna:
            sub = sub.dropna()
        unique_df = sub.drop_duplicates()
        try:
            unique_df = unique_df.sort_values(by=list(facet_vars_))
        except TypeError:
            pass
        return [tuple(row) for row in unique_df.itertuples(index=False, name=None)]

    def _subset_by_facet(
        facet_vars_: Sequence[str],
        facet_values: Tuple[Any, ...],
    ) -> pd.DataFrame:
        if not facet_vars_:
            return df
        mask = pd.Series(True, index=df.index)
        for vname, vval in zip(facet_vars_, facet_values):
            if pd.isna(vval):
                mask &= df[vname].isna()
            else:
                mask &= (df[vname] == vval)
        return df.loc[mask]

    def _meta(col: str) -> ColumnMeta:
        key = _meta_key(col)
        if config.meta is None:
            return ColumnMeta(name=key)
        return config.meta.get(key)

    def _axis_label(col: str, prefix: str = "") -> str:
        m = _meta(col)
        if config.label_prefer_alias:
            base = m.alias or m.axis_label or m.name
        else:
            base = m.axis_label or m.alias or m.name
        if m.unit:
            return f"{base} [{prefix}{m.unit}]"
        return base

    def _format_value(col: str, value: Any, scale: float, prefix: str) -> str:
        m = _meta(col)
        if value is None or (isinstance(value, float) and np.isnan(value)) or pd.isna(value):
            return "NaN"
        try:
            v = float(value) * scale
            if m.fmt is not None:
                s = format(v, m.fmt)
            elif m.digits_show is not None:
                s = f"{v:.{int(m.digits_show)}f}"
            else:
                s = f"{v:.6g}"
            if m.unit:
                s += f"{prefix}{m.unit}"
            return s
        except Exception:
            return str(value)

    def _title_kv(col: str, value: Any, scale: float, prefix: str) -> str:
        val_str = _format_value(col, value, scale, prefix)
        if config.title_show_keys:
            m = _meta(col)
            return f"{m.alias or m.name}={val_str}"
        return val_str

    def _prepare_xy(d: pd.DataFrame, xcol: str, ycol: str) -> Tuple[pd.Series, pd.Series]:
        dx = d[[xcol, ycol]].dropna()
        if dx.empty:
            return pd.Series(dtype=float), pd.Series(dtype=float)
        if config.agg is None:
            if config.sort_x:
                dx = dx.sort_values(by=xcol)
            return dx[xcol], dx[ycol]
        grouped = dx.groupby(xcol, sort=config.sort_x)[ycol]
        if isinstance(config.agg, str):
            ys = getattr(grouped, config.agg)()
        else:
            ys = grouped.apply(config.agg)
        return pd.Series(ys.index, name=xcol), pd.Series(ys.values, name=ycol)

    # ------------------------------------------------------------------ #
    # Validate inputs
    # ------------------------------------------------------------------ #
    mode = str(mode).lower()
    if mode not in {"line", "heatmap", "contour"}:
        raise ValueError(f"mode must be 'line', 'heatmap', or 'contour', got: {mode}")

    if mode in {"heatmap", "contour"}:
        if hue is None:
            raise ValueError(f"In {mode} mode, 'hue' is required (it becomes the y-axis).")
        colorbar = str(colorbar).lower()
        if colorbar not in {"each", "row", "col", "all"}:
            raise ValueError(f"colorbar must be one of each/row/col/all, got: {colorbar}")

    _ensure_columns_exist([x, y, hue, *facet_vars])

    # ------------------------------------------------------------------ #
    # Global autoscale
    # ------------------------------------------------------------------ #
    autoscale_map: Dict[str, Tuple[float, str]] = {}
    no_autoscale_set = set(no_autoscale or [])
    no_autoscale_key_set = {_meta_key(c) for c in no_autoscale_set}

    def _get_global_scale(col: str) -> Tuple[float, str]:
        if col in autoscale_map:
            return autoscale_map[col]
        key = _meta_key(col)
        if (col in no_autoscale_set) or (key in no_autoscale_key_set):
            autoscale_map[col] = (1.0, "")
            return 1.0, ""
        m = _meta(col)
        u = (m.unit or "").strip()
        if (u == "") or (u.lower() in {"a.u.", "au", "a.u", "arb.", "arb", "arb. unit", "arb units"}):
            autoscale_map[col] = (1.0, "")
            return 1.0, ""
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            scale, prefix = get_autoscale(s.to_numpy())
        else:
            scale, prefix = 1.0, ""
        autoscale_map[col] = (scale, prefix)
        return scale, prefix

    x_scale, x_prefix = _get_global_scale(x)

    if mode == "line":
        y_scale, y_prefix = _get_global_scale(y)
        hue_scale, hue_prefix = (_get_global_scale(hue) if hue is not None else (1.0, ""))
    else:
        hue_scale, hue_prefix = _get_global_scale(hue)
        z_scale, z_prefix = _get_global_scale(y)

    title_vars = list(config.title_vars) if config.title_vars is not None else facet_vars
    for tv in title_vars:
        if tv in df.columns:
            _get_global_scale(tv)

    # ------------------------------------------------------------------ #
    # Facet layout
    # ------------------------------------------------------------------ #
    combos = _unique_facet_combinations(facet_vars, dropna=config.dropna_facets)
    n = len(combos)
    ncols = max(1, int(config.ncols))
    nrows = max(1, int(ceil(n / ncols)))
    figsize = (config.figsize_per_ax[0] * ncols, config.figsize_per_ax[1] * nrows)

    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncols, figsize=figsize,
        sharex=config.sharex, sharey=config.sharey,
        squeeze=False, layout="constrained",
    )
    axes_flat = axes.ravel()

    # Hue order (line mode)
    if mode == "line" and hue is not None:
        hue_values: List[Any] = (
            list(config.hue_order)
            if config.hue_order is not None
            else list(dict.fromkeys(df[hue].dropna().tolist()).keys())
        )
    else:
        hue_values = [None]

    # ------------------------------------------------------------------ #
    # Grid data pre-pass (heatmap / contour)
    # ------------------------------------------------------------------ #
    grid_cache: Dict[int, Dict[str, Any]] = {}
    zmin_raw_per_ax: Dict[int, float] = {}
    zmax_raw_per_ax: Dict[int, float] = {}

    if mode in {"heatmap", "contour"}:
        for i, facet_values in enumerate(combos):
            dsub = _subset_by_facet(facet_vars, facet_values)
            xs_u = np.sort(dsub[x].dropna().unique())
            ys_u = np.sort(dsub[hue].dropna().unique())

            if xs_u.size == 0 or ys_u.size == 0:
                Z = np.full((max(ys_u.size, 0), max(xs_u.size, 0)), np.nan, dtype=float)
            else:
                use_agg = config.agg if config.agg is not None else "mean"
                grp = dsub[[hue, x, y]].dropna().groupby([hue, x])[y]
                pv = (grp.agg(use_agg) if isinstance(use_agg, str) else grp.apply(use_agg)).unstack(x)
                pv = pv.reindex(index=ys_u, columns=xs_u)
                Z = pv.to_numpy(dtype=float)

            valid = Z[~np.isnan(Z)]
            grid_cache[i] = {"xs": xs_u, "ys": ys_u, "Z": Z}
            zmin_raw_per_ax[i] = float(valid.min()) if valid.size else np.nan
            zmax_raw_per_ax[i] = float(valid.max()) if valid.size else np.nan

    def _group_vmin_vmax(i: int) -> Tuple[float, float]:
        def _safe_mm(indices: List[int]) -> Tuple[float, float]:
            mins = [zmin_raw_per_ax[j] for j in indices if not np.isnan(zmin_raw_per_ax[j])]
            maxs = [zmax_raw_per_ax[j] for j in indices if not np.isnan(zmax_raw_per_ax[j])]
            return (float(min(mins)), float(max(maxs))) if (mins and maxs) else (np.nan, np.nan)

        if colorbar == "each":
            return zmin_raw_per_ax[i], zmax_raw_per_ax[i]
        if colorbar == "all":
            return _safe_mm(list(range(n)))
        row, col = i // ncols, i % ncols
        if colorbar == "row":
            return _safe_mm([j for j in range(n) if j // ncols == row])
        return _safe_mm([j for j in range(n) if j % ncols == col])

    # ------------------------------------------------------------------ #
    # Per-axis drawing functions
    # ------------------------------------------------------------------ #
    def _draw_line_ax(ax: plt.Axes, dsub: pd.DataFrame) -> None:
        if hue is not None:
            for hv in hue_values:
                dline = dsub.loc[dsub[hue] == hv]
                xs, ys = _prepare_xy(dline, x, y)
                if config.apply_meta_transform_to_data:
                    xs = xs.astype(float) * x_scale
                    ys = ys.astype(float) * y_scale
                ax.plot(xs.to_numpy(), ys.to_numpy(),
                        label=_format_value(hue, hv, hue_scale, hue_prefix))
        else:
            xs, ys = _prepare_xy(dsub, x, y)
            if config.apply_meta_transform_to_data:
                xs = xs.astype(float) * x_scale
                ys = ys.astype(float) * y_scale
            ax.plot(xs.to_numpy(), ys.to_numpy())

        if hue is not None and config.legend:
            m_hue = _meta(hue)
            ax.legend(
                title=m_hue.axis_label or m_hue.alias or m_hue.name,
                loc=config.legend_loc,
                frameon=True,
            )

    def _draw_heatmap_ax(ax: plt.Axes, i: int) -> Optional[Any]:
        cache = grid_cache.get(i)
        if cache is None:
            ax.axis("off")
            return None

        sc_x = x_scale if config.apply_meta_transform_to_data else 1.0
        sc_y = hue_scale if config.apply_meta_transform_to_data else 1.0
        sc_z = z_scale if config.apply_meta_transform_to_data else 1.0

        xs = cache["xs"].astype(float) * sc_x
        ys = cache["ys"].astype(float) * sc_y
        Z = cache["Z"].astype(float) * sc_z

        vmin_r, vmax_r = _group_vmin_vmax(i)
        vmin = vmin_r * sc_z if not np.isnan(vmin_r) else vmin_r
        vmax = vmax_r * sc_z if not np.isnan(vmax_r) else vmax_r

        return ax.pcolormesh(xs, ys, Z, shading="auto", vmin=vmin, vmax=vmax, cmap=cmap)

    def _draw_contour_ax(ax: plt.Axes, i: int) -> Optional[ScalarMappable]:
        cache = grid_cache.get(i)
        if cache is None:
            ax.axis("off")
            return None

        sc_x = x_scale if config.apply_meta_transform_to_data else 1.0
        sc_y = hue_scale if config.apply_meta_transform_to_data else 1.0
        sc_z = z_scale if config.apply_meta_transform_to_data else 1.0

        xs = cache["xs"].astype(float) * sc_x
        ys = cache["ys"].astype(float) * sc_y
        Z = cache["Z"].astype(float) * sc_z

        vmin_r, vmax_r = _group_vmin_vmax(i)
        have_range = not (np.isnan(vmin_r) or np.isnan(vmax_r))
        vmin = vmin_r * sc_z if have_range else None
        vmax = vmax_r * sc_z if have_range else None

        n_levels = config.contour_levels or 10
        levels_arg: Any = np.linspace(vmin, vmax, n_levels + 1) if have_range else n_levels

        if config.contour_filled:
            cs = ax.contourf(xs, ys, Z, levels=levels_arg, cmap=cmap, extend="both")
        else:
            cs = ax.contour(xs, ys, Z, levels=levels_arg, cmap=cmap)

        if config.contour_labels:
            ax.clabel(cs, inline=True, fontsize=8)

        sm = ScalarMappable(norm=Normalize(vmin=vmin, vmax=vmax), cmap=cmap or cs.cmap)
        sm.set_array([])
        return sm

    def _set_ax_labels(ax: plt.Axes, i: int, x_lbl: str, y_lbl: str) -> None:
        # When axes are shared, label only the outer edges to avoid redundancy.
        # An axis is the "bottom" of its column if no valid plot exists below it.
        if not config.sharex or (i + ncols >= n):
            ax.set_xlabel(x_lbl)
        if not config.sharey or (i % ncols == 0):
            ax.set_ylabel(y_lbl)

    # ------------------------------------------------------------------ #
    # Plot loop
    # ------------------------------------------------------------------ #
    mappables: Dict[int, Any] = {}

    for i, facet_values in enumerate(combos):
        ax = axes_flat[i]
        dsub = _subset_by_facet(facet_vars, facet_values)

        # Title
        if title_vars:
            facet_map = dict(zip(facet_vars, facet_values))
            parts: List[str] = [
                _title_kv(tv, facet_map[tv], *autoscale_map.get(tv, (1.0, "")))
                for tv in title_vars if tv in facet_map
            ]
            ax.set_title(config.title_sep.join(parts))

        if mode == "line":
            _draw_line_ax(ax, dsub)
            x_lbl = config.xlabel or _axis_label(x, x_prefix)
            y_lbl = config.ylabel or _axis_label(y, y_prefix)
        elif mode == "heatmap":
            pc = _draw_heatmap_ax(ax, i)
            if pc is not None:
                mappables[i] = pc
            x_lbl = config.xlabel or _axis_label(x, x_prefix)
            y_lbl = config.ylabel or _axis_label(hue, hue_prefix)
        else:  # contour
            sm = _draw_contour_ax(ax, i)
            if sm is not None:
                mappables[i] = sm
            x_lbl = config.xlabel or _axis_label(x, x_prefix)
            y_lbl = config.ylabel or _axis_label(hue, hue_prefix)

        _set_ax_labels(ax, i, x_lbl, y_lbl)

    # Hide unused axes
    for j in range(n, len(axes_flat)):
        axes_flat[j].axis("off")

    # ------------------------------------------------------------------ #
    # Colorbars (heatmap / contour)
    # ------------------------------------------------------------------ #
    if mode in {"heatmap", "contour"}:
        cbar_label = _axis_label(y, z_prefix)

        def _axs_in_row(r: int) -> List[plt.Axes]:
            return [axes_flat[k] for k in range(n) if k // ncols == r and k in mappables]

        def _axs_in_col(c: int) -> List[plt.Axes]:
            return [axes_flat[k] for k in range(n) if k % ncols == c and k in mappables]

        if colorbar == "each":
            for i, mp in mappables.items():
                fig.colorbar(mp, ax=axes_flat[i]).set_label(cbar_label)

        elif colorbar == "all":
            if mappables:
                mp = mappables[next(iter(mappables))]
                fig.colorbar(mp, ax=[axes_flat[i] for i in mappables]).set_label(cbar_label)

        elif colorbar == "row":
            for r in range(nrows):
                axs = _axs_in_row(r)
                if not axs:
                    continue
                idxs = [k for k in mappables if k // ncols == r]
                fig.colorbar(mappables[idxs[0]], ax=axs).set_label(cbar_label)

        elif colorbar == "col":
            for c in range(ncols):
                axs = _axs_in_col(c)
                if not axs:
                    continue
                idxs = [k for k in mappables if k % ncols == c]
                fig.colorbar(mappables[idxs[0]], ax=axs).set_label(cbar_label)

    return fig, axes
