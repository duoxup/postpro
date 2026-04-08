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
    # pandas / numpy scalars usually have .item()
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

        # Normalize empty strings to None for compactness/consistency
        for k in ("axis_label", "alias", "unit", "fmt"):
            if isinstance(d.get(k), str) and d[k].strip() == "":
                d[k] = None

        # Make numeric fields JSON-friendly
        d["scale"] = float(_json_friendly_number(d.get("scale", 1.0)))
        d["offset"] = float(_json_friendly_number(d.get("offset", 0.0)))
        if d.get("digits_show", None) is not None:
            try:
                d["digits_show"] = int(_json_friendly_number(d["digits_show"]))
            except Exception:
                d["digits_show"] = None

        # Formatter handling
        if include_formatter:
            # You may choose to store a string identifier here instead,
            # but storing arbitrary callables in JSON is not reliable.
            raise TypeError(
                "ColumnMeta.formatter is not JSON-serializable. "
                "Store formatting via (scale/offset/digits_show/fmt) or inject formatter at runtime."
            )
        d["formatter"] = None

        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> ColumnMeta:
        # Forward-compatible: ignore unknown keys
        allowed = {
            "name", "axis_label", "alias", "unit", "scale", "offset",
            "digits_show", "fmt", "formatter"
        }
        clean: Dict[str, Any] = {k: d[k] for k in d.keys() if k in allowed}

        # Normalize empty strings
        for k in ("axis_label", "alias", "unit", "fmt"):
            if isinstance(clean.get(k), str) and clean[k].strip() == "":
                clean[k] = None

        # Enforce numeric types
        if "scale" in clean and clean["scale"] is not None:
            clean["scale"] = float(clean["scale"])
        if "offset" in clean and clean["offset"] is not None:
            clean["offset"] = float(clean["offset"])
        if "digits_show" in clean and clean["digits_show"] is not None:
            clean["digits_show"] = int(clean["digits_show"])

        # formatter is expected to be None when loaded from JSON
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
    def from_json(self, path_or_fp: Union[PathLike, IO[str]]) -> ColumnMetaRegistry:
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
    dropna_facets: bool = False             # drop NA rows when forming facet combos
    apply_meta_transform_to_data: bool = True  # scale x/y plotted values by meta

    # labeling overrides (if None, use meta/col)
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None

    # titles
    title_vars: Optional[Sequence[str]] = None  # default: facet_vars
    title_sep: str = ", "

    # legend
    legend: bool = True
    legend_loc: str = "best"

    # hue ordering
    hue_order: Optional[Sequence[Any]] = None

    # metadata
    meta: Optional[ColumnMetaRegistry] = None


def _ensure_columns_exist(df: pd.DataFrame, cols: Sequence[Optional[str]]) -> None:
    cols2 = [c for c in cols if c]
    missing = [c for c in cols2 if c not in df.columns]
    if missing:
        raise KeyError(f"DataFrame is missing columns: {missing}")


def _unique_facet_combinations(
    df: pd.DataFrame,
    facet_vars: Sequence[str],
    dropna: bool,
) -> List[Tuple[Any, ...]]:
    if not facet_vars:
        return [tuple()]

    sub = df.loc[:, facet_vars]
    if dropna:
        sub = sub.dropna()

    # preserve encounter order
    combos: List[Tuple[Any, ...]] = []
    seen = set()
    for row in sub.itertuples(index=False, name=None):
        if row not in seen:
            combos.append(row)
            seen.add(row)
    return combos


def _subset_by_facet(
    df: pd.DataFrame,
    facet_vars: Sequence[str],
    facet_values: Tuple[Any, ...],
) -> pd.DataFrame:
    if not facet_vars:
        return df

    mask = pd.Series(True, index=df.index)
    for vname, vval in zip(facet_vars, facet_values):
        if _is_na(vval):
            mask &= df[vname].isna()
        else:
            mask &= (df[vname] == vval)
    return df.loc[mask]


def _apply_transform_series(meta: ColumnMeta, s: pd.Series) -> pd.Series:
    # vectorized numeric transform; non-numeric series will fall back to original values
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float) * meta.scale + meta.offset
    return s


def _prepare_xy(
    d: pd.DataFrame,
    x: str,
    y: str,
    sort_x: bool,
    agg: Optional[AggFunc],
) -> Tuple[pd.Series, pd.Series]:
    dx = d[[x, y]].dropna()
    if dx.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    if agg is None:
        if sort_x:
            dx = dx.sort_values(by=x)
        return dx[x], dx[y]

    # aggregate y by x
    grouped = dx.groupby(x, sort=sort_x)[y]
    if isinstance(agg, str):
        ys = getattr(grouped, agg)()
    else:
        ys = grouped.apply(agg)

    xs = pd.Series(ys.index, name=x)
    ys = pd.Series(ys.values, name=y)
    return xs, ys


def _axis_label(col: str, cfg: PlotScanConfig) -> str:
    if cfg.meta is None:
        return col
    return cfg.meta.get(col).axis_text()


def _legend_title(col: str, cfg: PlotScanConfig) -> str:
    if cfg.meta is None:
        return col
    return cfg.meta.get(col).legend_title()


def _legend_item_label(col: str, value: Any, cfg: PlotScanConfig) -> str:
    if cfg.meta is None:
        return str(value)
    return cfg.meta.get(col).format_value(value)


def _title_kv(col: str, value: Any, cfg: PlotScanConfig) -> str:
    if cfg.meta is None:
        return f"{col}={value}"
    m = cfg.meta.get(col)
    return f"{m.title_key()}={m.format_value(value)}"

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
    config: "PlotScanConfig" = None,
    mode: str = "line",               # "line" or "heatmap"
    colorbar: str = "each",           # "each" | "row" | "col" | "all" (heatmap only)
    cmap: Optional[str] = None,       # matplotlib colormap name, default None -> matplotlib default
    no_autoscale: Optional[Sequence[str]] = None,
) -> Tuple[plt.Figure, np.ndarray]:
    """
    Faceted plotting for multi-parameter scan results in a pandas DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
    x, y : str
        In line mode: x-axis variable and y-axis variable.
        In heatmap mode: x-axis variable and z-axis variable (color) respectively.
    hue : str | None
        In line mode: grouping variable (one line per hue value).
        In heatmap mode: becomes the y-axis variable of the heatmap grid.
        Required in heatmap mode.
    facet_vars : Sequence[str] | None
        Variables used to create facets (one subplot per unique combination).
    config : PlotScanConfig
        Must be provided; uses its fields unchanged.
    mode : str
        "line" or "heatmap".
    colorbar : str
        Heatmap colorbar sharing strategy: "each", "row", "col", "all".
    cmap : str | None
        Colormap name. If None, matplotlib default is used.

    Returns
    -------
    fig, axes_2d
    """
    if config is None:
        raise ValueError("config must be provided (PlotScanConfig).")

    facet_vars = list(facet_vars or [])

    # ----------------------------
    # Helpers (local; do not modify your classes)
    # ----------------------------
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
            pass  # mixed types fall back to encounter order
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

    def _is_numeric_series(s: pd.Series) -> bool:
        return pd.api.types.is_numeric_dtype(s)

    def _meta(col: str) -> "ColumnMeta":
        key = _meta_key(col)
        if config.meta is None:
            return ColumnMeta(name=key)
        return config.meta.get(key)

    def _axis_label(col: str, prefix: str = "") -> str:
        m = _meta(col)
        base = m.axis_label or m.alias or m.name
        if m.unit:
            return f"{base} [{prefix}{m.unit}]"
        return base

    def _format_value(col: str, value: Any, scale: float, prefix: str) -> str:
        """
        Format a scalar using ColumnMeta.digits_show/fmt, and apply autoscale (value*scale, prefix+unit).
        For non-numeric values, return str(value) and ignore scale/prefix.
        """
        m = _meta(col)

        # Non-numeric / NA handling
        if value is None or (isinstance(value, float) and np.isnan(value)) or pd.isna(value):
            return "NaN"

        # Try numeric formatting
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
            # Fallback for categorical/string-like
            return str(value)

    def _title_kv(col: str, value: Any, scale: float, prefix: str) -> str:
        m = _meta(col)
        key = m.alias or m.name
        return f"{key}={_format_value(col, value, scale, prefix)}"

    def _prepare_xy(
        d: pd.DataFrame,
        xcol: str,
        ycol: str,
        sort_x: bool,
        agg: Optional[Union[str, Any]],
    ) -> Tuple[pd.Series, pd.Series]:
        dx = d[[xcol, ycol]].dropna()
        if dx.empty:
            return pd.Series(dtype=float), pd.Series(dtype=float)

        if agg is None:
            if sort_x:
                dx = dx.sort_values(by=xcol)
            return dx[xcol], dx[ycol]

        grouped = dx.groupby(xcol, sort=sort_x)[ycol]
        if isinstance(agg, str):
            ys = getattr(grouped, agg)()
        else:
            ys = grouped.apply(agg)

        xs = pd.Series(ys.index, name=xcol)
        ys = pd.Series(ys.values, name=ycol)
        return xs, ys

    # ----------------------------
    # Validate inputs
    # ----------------------------
    mode = str(mode).lower()
    if mode not in {"line", "heatmap"}:
        raise ValueError(f"mode must be 'line' or 'heatmap', got: {mode}")

    if mode == "heatmap":
        if hue is None:
            raise ValueError("In heatmap mode, 'hue' is required (it becomes the heatmap y-axis).")
        colorbar = str(colorbar).lower()
        if colorbar not in {"each", "row", "col", "all"}:
            raise ValueError(f"colorbar must be one of each/row/col/all, got: {colorbar}")

    _ensure_columns_exist([x, y, hue, *facet_vars])

    # ----------------------------
    # Global autoscale (uniform across all facets)
    # ----------------------------
    # We use autoscale only for numeric series; otherwise (1.0, "").
    autoscale_map: Dict[str, Tuple[float, str]] = {}

    no_autoscale_set = set(no_autoscale or [])
    no_autoscale_key_set = {_meta_key(c) for c in no_autoscale_set}
    def _get_global_scale(col: str) -> Tuple[float, str]:
        if col in autoscale_map:
            return autoscale_map[col]
    
        # User-specified: do not autoscale these columns
        key = _meta_key(col)
        if (col in no_autoscale_set) or (key in no_autoscale_key_set):
            autoscale_map[col] = (1.0, "")
            return 1.0, ""
    
        m = _meta(col)
    
        # Do not autoscale if unit is missing/empty or is a.u./arb.
        u = (m.unit or "").strip()
        if (u == "") or (u.lower() in {"a.u.", "au", "a.u", "arb.", "arb", "arb. unit", "arb units"}):
            autoscale_map[col] = (1.0, "")
            return 1.0, ""
    
        s = df[col]
        if _is_numeric_series(s):
            scale, prefix = get_autoscale(s.to_numpy())
        else:
            scale, prefix = 1.0, ""
    
        autoscale_map[col] = (scale, prefix)
        return scale, prefix



    x_scale, x_prefix = _get_global_scale(x)

    if mode == "line":
        y_scale, y_prefix = _get_global_scale(y)
        if hue is not None:
            hue_scale, hue_prefix = _get_global_scale(hue)  # may be non-numeric -> (1,"")
        else:
            hue_scale, hue_prefix = 1.0, ""
    else:
        # heatmap: hue becomes y-axis; y becomes z(color)
        hue_scale, hue_prefix = _get_global_scale(hue)  # y-axis of heatmap
        z_scale, z_prefix = _get_global_scale(y)        # color axis

    # Title variables scaling (global)
    title_vars = list(config.title_vars) if config.title_vars is not None else facet_vars
    for tv in title_vars:
        if tv in df.columns:
            _get_global_scale(tv)

    # ----------------------------
    # Facet layout
    # ----------------------------
    combos = _unique_facet_combinations(facet_vars, dropna=config.dropna_facets)
    n = len(combos)

    ncols = max(1, int(config.ncols))
    nrows = max(1, int(ceil(n / ncols)))
    figsize = (config.figsize_per_ax[0] * ncols, config.figsize_per_ax[1] * nrows)

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=figsize,
        sharex=config.sharex,
        sharey=config.sharey,
        squeeze=False,
        layout = 'constrained',
    )
    axes_flat = axes.ravel()

    # hue order for line mode
    if mode == "line" and hue is not None:
        if config.hue_order is not None:
            hue_values = list(config.hue_order)
        else:
            hv = df[hue].dropna().tolist()
            hue_values = list(dict.fromkeys(hv).keys())
    else:
        hue_values = [None]

    # ----------------------------
    # Heatmap pre-pass: build Z matrices and vmin/vmax pools
    # ----------------------------
    heatmap_cache: Dict[int, Dict[str, Any]] = {}
    zmin_raw_per_ax: Dict[int, float] = {}
    zmax_raw_per_ax: Dict[int, float] = {}

    if mode == "heatmap":
        # Build per-axis pivot grids and cache them
        for i, facet_values in enumerate(combos):
            dsub = _subset_by_facet(facet_vars, facet_values)

            # Regular grid assumption: use sorted unique coords
            xs = np.sort(dsub[x].dropna().unique())
            ys = np.sort(dsub[hue].dropna().unique())

            if xs.size == 0 or ys.size == 0:
                Z = np.full((ys.size, xs.size), np.nan, dtype=float)
            else:
                # Pivot to grid: index=hue (rows), columns=x (cols), values=y (z)
                # Handle duplicates via agg if provided; else take mean as a safe default
                use_agg = config.agg if config.agg is not None else "mean"
                if isinstance(use_agg, str):
                    pv = (
                        dsub[[hue, x, y]]
                        .dropna()
                        .groupby([hue, x])[y]
                        .agg(use_agg)
                        .unstack(x)
                    )
                else:
                    pv = (
                        dsub[[hue, x, y]]
                        .dropna()
                        .groupby([hue, x])[y]
                        .apply(use_agg)
                        .unstack(x)
                    )

                # Reindex to full grid order
                pv = pv.reindex(index=ys, columns=xs)
                Z = pv.to_numpy(dtype=float)

            # Raw z-range (before autoscale)
            if np.all(np.isnan(Z)):
                zmin = np.nan
                zmax = np.nan
            else:
                zmin = float(np.nanmin(Z))
                zmax = float(np.nanmax(Z))

            heatmap_cache[i] = {"xs": xs, "ys": ys, "Z": Z}
            zmin_raw_per_ax[i] = zmin
            zmax_raw_per_ax[i] = zmax

    def _group_vmin_vmax(i: int) -> Tuple[float, float]:
        """
        Compute vmin/vmax (raw) for this axis index i according to colorbar mode.
        """
        if mode != "heatmap":
            raise RuntimeError("_group_vmin_vmax called in non-heatmap mode")

        def _safe_minmax(indices: List[int]) -> Tuple[float, float]:
            mins = [zmin_raw_per_ax[j] for j in indices if not np.isnan(zmin_raw_per_ax[j])]
            maxs = [zmax_raw_per_ax[j] for j in indices if not np.isnan(zmax_raw_per_ax[j])]
            if not mins or not maxs:
                return np.nan, np.nan
            return float(min(mins)), float(max(maxs))

        if colorbar == "each":
            return zmin_raw_per_ax[i], zmax_raw_per_ax[i]

        if colorbar == "all":
            return _safe_minmax(list(range(n)))

        row = i // ncols
        col = i % ncols

        if colorbar == "row":
            idx = [j for j in range(n) if (j // ncols) == row]
            return _safe_minmax(idx)

        if colorbar == "col":
            idx = [j for j in range(n) if (j % ncols) == col]
            return _safe_minmax(idx)

        raise ValueError(f"Unexpected colorbar mode: {colorbar}")

    # ----------------------------
    # Plot loop
    # ----------------------------
    mappables: Dict[int, Any] = {}  # heatmap mappables per axis index

    for i, facet_values in enumerate(combos):
        ax = axes_flat[i]
        dsub = _subset_by_facet(facet_vars, facet_values)

        # Titles
        if title_vars:
            facet_map = dict(zip(facet_vars, facet_values))
            parts: List[str] = []
            for tv in title_vars:
                if tv in facet_map:
                    sc, pr = autoscale_map.get(tv, (1.0, ""))
                    parts.append(_title_kv(tv, facet_map[tv], sc, pr))
            ax.set_title(config.title_sep.join(parts))

        if mode == "line":
            # Plot lines
            if hue is not None:
                for hv in hue_values:
                    dline = dsub.loc[dsub[hue] == hv]
                    xs, ys = _prepare_xy(dline, x, y, sort_x=config.sort_x, agg=config.agg)

                    # Apply autoscale to plotted values (global)
                    if config.apply_meta_transform_to_data:
                        xs = xs.astype(float) * x_scale
                        ys = ys.astype(float) * y_scale

                    # Legend labels: format hue values with autoscale if numeric
                    label = _format_value(hue, hv, hue_scale, hue_prefix) if hue is not None else str(hv)
                    ax.plot(xs.to_numpy(), ys.to_numpy(), label=label)
            else:
                xs, ys = _prepare_xy(dsub, x, y, sort_x=config.sort_x, agg=config.agg)
                if config.apply_meta_transform_to_data:
                    xs = xs.astype(float) * x_scale
                    ys = ys.astype(float) * y_scale
                ax.plot(xs.to_numpy(), ys.to_numpy())

            # Axis labels (autoscale prefix + SI unit)
            ax.set_xlabel(config.xlabel or _axis_label(x, x_prefix))
            ax.set_ylabel(config.ylabel or _axis_label(y, y_prefix))

            if hue is not None and config.legend:
                ax.legend(
                    title=_meta(hue).axis_label or _meta(hue).alias or _meta(hue).name,
                    loc=config.legend_loc,
                    frameon=True,
                )

        else:
            # Heatmap: x vs hue, color = y
            cache = heatmap_cache.get(i, None)
            if cache is None:
                ax.axis("off")
                continue

            xs_raw = cache["xs"]
            ys_raw = cache["ys"]
            Z_raw = cache["Z"]

            # Apply autoscale (global)
            xs = xs_raw.astype(float) * x_scale if config.apply_meta_transform_to_data else xs_raw.astype(float)
            ys = ys_raw.astype(float) * hue_scale if config.apply_meta_transform_to_data else ys_raw.astype(float)
            Z = Z_raw.astype(float) * z_scale if config.apply_meta_transform_to_data else Z_raw.astype(float)

            vmin_raw, vmax_raw = _group_vmin_vmax(i)
            vmin = (vmin_raw * z_scale) if (config.apply_meta_transform_to_data and not np.isnan(vmin_raw)) else vmin_raw
            vmax = (vmax_raw * z_scale) if (config.apply_meta_transform_to_data and not np.isnan(vmax_raw)) else vmax_raw

            # pcolormesh; shading="auto" handles center/edge ambiguity robustly
            pc = ax.pcolormesh(xs, ys, Z, shading="auto", vmin=vmin, vmax=vmax, cmap=cmap)
            mappables[i] = pc

            ax.set_xlabel(config.xlabel or _axis_label(x, x_prefix))
            ax.set_ylabel(config.ylabel or _axis_label(hue, hue_prefix))

    # Hide unused axes
    for j in range(n, len(axes_flat)):
        axes_flat[j].axis("off")

    # ----------------------------
    # Colorbars (heatmap only)
    # ----------------------------
    if mode == "heatmap":
        # Colorbar label uses z (= original y variable)
        cbar_label = _axis_label(y, z_prefix)

        def _axes_in_row(r: int) -> List[plt.Axes]:
            idx = [k for k in range(n) if (k // ncols) == r]
            return [axes_flat[k] for k in idx if k in mappables]

        def _axes_in_col(c: int) -> List[plt.Axes]:
            idx = [k for k in range(n) if (k % ncols) == c]
            return [axes_flat[k] for k in idx if k in mappables]

        if colorbar == "each":
            for i, pc in mappables.items():
                cb = fig.colorbar(pc, ax=axes_flat[i])
                cb.set_label(cbar_label)

        elif colorbar == "all":
            if mappables:
                first_i = next(iter(mappables.keys()))
                pc = mappables[first_i]
                cb = fig.colorbar(pc, ax=[axes_flat[i] for i in mappables.keys()])
                cb.set_label(cbar_label)

        elif colorbar == "row":
            for r in range(nrows):
                axs = _axes_in_row(r)
                if not axs:
                    continue
                # pick first mappable in this row
                idxs = [k for k in mappables.keys() if (k // ncols) == r]
                pc = mappables[idxs[0]]
                cb = fig.colorbar(pc, ax=axs)
                cb.set_label(cbar_label)

        elif colorbar == "col":
            for c in range(ncols):
                axs = _axes_in_col(c)
                if not axs:
                    continue
                idxs = [k for k in mappables.keys() if (k % ncols) == c]
                pc = mappables[idxs[0]]
                cb = fig.colorbar(pc, ax=axs)
                cb.set_label(cbar_label)

        else:
            raise ValueError(f"Unexpected colorbar mode: {colorbar}")

    return fig, axes

if __name__ == '__main__':
    meta_plot = ColumnMetaRegistry.from_json(r'/afs/ifh.de/group/pitz/data/duoxup/sim1/pyS/colmeta_4.json')
    new_entry_1 = ColumnMeta(name='Freq',
                             axis_label='Frequency',
                             alias=None,
                             unit='THz',
                             scale=1.,
                             offset=0,
                             digits_show=1,
                             fmt=None,
                             formatter=None)
    meta_plot.add(new_entry_1)
    meta_plot.to_json(r'/afs/ifh.de/group/pitz/data/duoxup/sim1/pyS/colmeta_4.json')
    

