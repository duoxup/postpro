#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from pathlib import Path
from importlib import resources
from typing import Union

import numpy as np
import matplotlib.pyplot as plt

from xtils import get_autoscale

from .core import MainResults
from .vizdfscan import ColumnMetaRegistry

prj_dir = resources.files("postgenesis")
colmr = ColumnMetaRegistry.from_json(os.path.join(prj_dir, "gcmr_2.json"))

_ARB_UNITS = {"a.u.", "au", "a.u", "arb.", "arb", "arb. unit", "arb units"}


def _autoscale(values: np.ndarray, unit: str) -> tuple[float, str]:
    u = (unit or "").strip()
    if not u or u.lower() in _ARB_UNITS:
        return 1.0, ""
    return get_autoscale(np.asarray(values).flatten())


def _auto_label(gmr: MainResults) -> str:
    parts = gmr.file_basename.split(".")
    if len(parts) >= 2:
        return parts[1]
    return gmr.file_basename


def _load_case(x) -> MainResults:
    if isinstance(x, (str, Path)):
        return MainResults(x)
    if isinstance(x, MainResults):
        return x
    raise TypeError(
        f"Expected str, Path, or MainResults, got {type(x).__name__}"
    )


class CaseComparison:
    """Compare multiple MainResults files with overlay plots."""

    def __init__(
        self,
        cases: list,
        labels: list[str] | None = None,
    ) -> None:
        self.cases: list[MainResults] = [_load_case(c) for c in cases]
        if labels is None:
            self.labels: list[str] = [_auto_label(gmr) for gmr in self.cases]
        else:
            if len(labels) != len(self.cases):
                raise ValueError(
                    f"labels length ({len(labels)}) does not match "
                    f"cases length ({len(self.cases)})"
                )
            self.labels = list(labels)

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
        """Overlay z-evolution curves for all cases.

        One subplot per entry in *yattrs* (vertical stack).
        x-axis is always ``zplot``; each case is one line.
        """
        n = len(yattrs)
        if fig is None or axes is None:
            fig, axes_arr = plt.subplots(
                n, 1,
                sharex="all" if sharex else False,
                sharey="all" if sharey else False,
                squeeze=False,
                layout="constrained",
                figsize=(6, 2.5 * n),
            )
            axes_arr = axes_arr.ravel()
        else:
            axes_arr = np.asarray(axes).ravel()

        x_meta = colmr.get("zplot")
        x_unit = x_meta.unit or ""
        x_scale, x_prefix = _autoscale(self.cases[0].zplot, x_unit)

        for i, yattr in enumerate(yattrs):
            ax = axes_arr[i]
            y_meta = colmr.get(yattr)
            y_unit = y_meta.unit or ""

            all_y = np.concatenate(
                [np.asarray(getattr(gmr, yattr)).flatten() for gmr in self.cases]
            )
            y_scale, y_prefix = _autoscale(all_y, y_unit)

            for gmr, label in zip(self.cases, self.labels):
                ax.plot(
                    gmr.zplot * x_scale,
                    np.asarray(getattr(gmr, yattr)) * y_scale,
                    label=label,
                    **pltkwargs,
                )

            ax.legend()

            y_lbl = y_meta.axis_label or yattr
            if y_unit:
                y_lbl = f"{y_lbl} [{y_prefix}{y_unit}]"
            ax.set_ylabel(y_lbl)

            if not sharex or i == n - 1:
                x_lbl = x_meta.axis_label or "z"
                if x_unit:
                    x_lbl = f"{x_lbl} [{x_prefix}{x_unit}]"
                ax.set_xlabel(x_lbl)

        return fig, axes_arr
