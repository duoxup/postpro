#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 16:09:14 2026

@author: duoxup
"""

from __future__ import annotations
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from typing import Tuple, Optional

from contextlib import contextmanager
import matplotlib as mpl
import matplotlib.pyplot as plt

def focus_xlim_on_y_threshold(
    ax: Axes,
    *,
    threshold_abs: Optional[float] = None,
    threshold_rel: Optional[float] = None,
    pad_frac: float = 0.05,
    min_width: Optional[float] = None,
    include_lines: bool = True,
    include_scatters: bool = True,
    ignore_nonfinite: bool = True,
    set_xlim: bool = True,
    rel_ref: str = "max",   # "max" or "p99" or "p95"
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Set ax.set_xlim() to focus on region where y > threshold.

    Threshold can be absolute (threshold_abs) and/or relative (threshold_rel).
    Relative threshold is computed as threshold_rel * y_ref, where y_ref is
    derived from all y data found in the Axes.

    Returns (xmin, xmax, threshold_used). If no points satisfy condition, returns (None, None, threshold_used).
    """
    if threshold_abs is None and threshold_rel is None:
        raise ValueError("Provide at least one of threshold_abs or threshold_rel.")

    xs_all: list[np.ndarray] = []
    ys_all: list[np.ndarray] = []

    def _clean_xy(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        x = np.asarray(x).ravel()
        y = np.asarray(y).ravel()
        if ignore_nonfinite:
            m = np.isfinite(x) & np.isfinite(y)
            x, y = x[m], y[m]
        return x, y

    # Collect data from lines
    if include_lines:
        for ln in ax.lines:  # type: ignore[attr-defined]
            if not isinstance(ln, Line2D):
                continue
            x, y = _clean_xy(ln.get_xdata(orig=False), ln.get_ydata(orig=False))
            if x.size:
                xs_all.append(x)
                ys_all.append(y)

    # Collect data from scatters
    if include_scatters:
        for col in ax.collections:
            if not isinstance(col, PathCollection):
                continue
            off = col.get_offsets()
            if off is None or len(off) == 0:
                continue
            x = np.asarray(off[:, 0]).ravel()
            y = np.asarray(off[:, 1]).ravel()
            x, y = _clean_xy(x, y)
            if x.size:
                xs_all.append(x)
                ys_all.append(y)

    if not ys_all:
        return (None, None, None)

    y_all = np.concatenate(ys_all)

    # Reference for relative threshold
    if rel_ref == "max":
        y_ref = float(np.max(y_all))
    elif rel_ref == "p99":
        y_ref = float(np.quantile(y_all, 0.99))
    elif rel_ref == "p95":
        y_ref = float(np.quantile(y_all, 0.95))
    else:
        raise ValueError("rel_ref must be one of: 'max', 'p99', 'p95'.")

    thr_used = -np.inf
    if threshold_abs is not None:
        thr_used = max(thr_used, float(threshold_abs))
    if threshold_rel is not None:
        if not (0 <= threshold_rel <= 1):
            raise ValueError("threshold_rel should be in [0, 1].")
        thr_used = max(thr_used, float(threshold_rel) * y_ref)

    # Now find x where y > thr_used
    xs_hit: list[np.ndarray] = []
    for x, y in zip(xs_all, ys_all):
        m = y > thr_used
        if np.any(m):
            xs_hit.append(x[m])

    if not xs_hit:
        return (None, None, thr_used)

    x_hit = np.concatenate(xs_hit)
    xmin = float(np.min(x_hit))
    xmax = float(np.max(x_hit))

    # Padding
    span = xmax - xmin
    if span == 0:
        span = 1.0
    pad = pad_frac * span
    xmin -= pad
    xmax += pad

    # Minimum width
    if min_width is not None and (xmax - xmin) < min_width:
        mid = 0.5 * (xmin + xmax)
        half = 0.5 * min_width
        xmin, xmax = mid - half, mid + half

    if set_xlim:
        ax.set_xlim(xmin, xmax)

    return (xmin, xmax, thr_used)

@contextmanager
def use_backend(name: str):
    prev = mpl.get_backend()
    plt.close('all')
    plt.switch_backend(name)
    try:
        yield
    finally:
        plt.close('all')
        plt.switch_backend(prev)
        