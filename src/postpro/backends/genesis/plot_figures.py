"""Figure-level plotting helpers for Genesis single-case results."""

from __future__ import annotations

from typing import Literal

import numpy as np
from matplotlib.figure import Figure

from postpro.backends.genesis.adapters import GenesisResultLike, require_main_results
from postpro.backends.genesis.plot_axes import (
    plot_slice_bunching,
    plot_slice_current,
    plot_spectrum,
    plot_z_energy,
    plot_z_field_size,
    plot_z_particle_size,
    plot_z_pulse_length,
)

ZSelector = float | str | None


def zoverview(
    result: GenesisResultLike,
    *,
    meta=None,
    label_options=None,
    unit_options=None,
    figsize: tuple[float, float] = (8.0, 10.0),
    sharex: bool = True,
    suptitle: str | None = None,
) -> tuple[Figure, np.ndarray]:
    fig, axes = _subplots(4, 1, figsize=figsize, sharex=sharex)

    plot_z_pulse_length(
        axes[0],
        result,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        xlabel=None if sharex else "z",
    )
    plot_z_energy(
        axes[1],
        result,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        xlabel=None if sharex else "z",
    )
    plot_z_particle_size(
        axes[2],
        result,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        xlabel=None if sharex else "z",
    )
    plot_z_field_size(
        axes[3],
        result,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
    )

    fig.suptitle(_resolve_suptitle(result, suptitle))
    return fig, axes


def pulse_metrics_figure(
    result: GenesisResultLike,
    *,
    meta=None,
    label_options=None,
    unit_options=None,
    figsize: tuple[float, float] = (8.0, 6.0),
    sharex: bool = True,
    suptitle: str | None = "Temporal metrics along z",
) -> tuple[Figure, np.ndarray]:
    fig, axes = _subplots(2, 1, figsize=figsize, sharex=sharex)

    plot_z_pulse_length(
        axes[0],
        result,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        xlabel=None if sharex else "z",
    )
    plot_z_energy(
        axes[1],
        result,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
    )

    fig.suptitle(_resolve_suptitle(result, suptitle))
    return fig, axes


def slice_diagnostics(
    result: GenesisResultLike,
    *,
    meta=None,
    label_options=None,
    unit_options=None,
    z: ZSelector = "max_energy",
    figsize: tuple[float, float] = (8.0, 6.0),
    sharex: bool = True,
    suptitle: str | None = None,
) -> tuple[Figure, np.ndarray]:
    fig, axes = _subplots(2, 1, figsize=figsize, sharex=sharex)
    z_target = _resolve_z(result, z)

    plot_slice_current(
        axes[0],
        result,
        z=z_target,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        xlabel=None if sharex else "Slice index",
    )
    plot_slice_bunching(
        axes[1],
        result,
        z=z_target,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
    )

    fig.suptitle(_resolve_suptitle(result, suptitle, fallback="Slice diagnostics"))
    return fig, axes


def spectrum_figure(
    result: GenesisResultLike,
    *,
    meta=None,
    label_options=None,
    unit_options=None,
    z: ZSelector = "max_energy",
    use_nearfield: bool = False,
    figsize: tuple[float, float] = (8.0, 4.0),
    suptitle: str | None = None,
) -> tuple[Figure, np.ndarray]:
    fig, axes = _subplots(1, 1, figsize=figsize, sharex=False)
    z_target = _resolve_z(result, z)

    plot_spectrum(
        axes[0],
        result,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        z=z_target,
        use_nearfield=use_nearfield,
    )

    fig.suptitle(_resolve_suptitle(result, suptitle, fallback="Spectrum"))
    return fig, axes


def _subplots(
    nrows: int,
    ncols: int,
    *,
    figsize: tuple[float, float],
    sharex: bool,
) -> tuple[Figure, np.ndarray]:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, sharex=sharex, layout="constrained")
    return fig, np.atleast_1d(axes)


def _resolve_suptitle(
    result: GenesisResultLike,
    suptitle: str | None,
    *,
    fallback: str | None = None,
) -> str | None:
    if suptitle is not None:
        return suptitle
    gmr = require_main_results(result)
    if hasattr(gmr, "file_basename"):
        return gmr.file_basename
    return fallback


def _resolve_z(result: GenesisResultLike, z: ZSelector) -> float | Literal["last"]:
    if z == "last":
        return "last"
    gmr = require_main_results(result)
    if z in (None, "max_energy"):
        return float(gmr.zplot[np.argmax(gmr.zenergy)])
    return float(z)
