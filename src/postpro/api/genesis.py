"""User-facing Genesis plotting APIs."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from postpro.backends.genesis.adapters import GenesisResultLike, require_main_results
from postpro.backends.genesis.models import MainResults
from postpro.backends.genesis.plot_figures import (
    pulse_metrics_figure,
    slice_diagnostics,
    spectrum_figure,
    zoverview,
)

GenesisSource = str | Path | GenesisResultLike
AxesArray = np.ndarray


def render_zoverview(
    source: GenesisSource,
    *,
    meta=None,
    label_options=None,
    unit_options=None,
    save_to: str | Path | None = None,
    dpi: int = 140,
    figsize: tuple[float, float] = (8.0, 10.0),
    sharex: bool = True,
    suptitle: str | None = None,
) -> tuple[Figure, AxesArray]:
    with _managed_main_results(source) as result:
        fig, axes = zoverview(
            result,
            meta=meta,
            label_options=label_options,
            unit_options=unit_options,
            figsize=figsize,
            sharex=sharex,
            suptitle=suptitle,
        )
    _save_figure(fig, save_to=save_to, dpi=dpi)
    return fig, axes


def render_pulse_metrics(
    source: GenesisSource,
    *,
    meta=None,
    label_options=None,
    unit_options=None,
    save_to: str | Path | None = None,
    dpi: int = 140,
    figsize: tuple[float, float] = (8.0, 6.0),
    sharex: bool = True,
    suptitle: str | None = "Temporal metrics along z",
) -> tuple[Figure, AxesArray]:
    with _managed_main_results(source) as result:
        fig, axes = pulse_metrics_figure(
            result,
            meta=meta,
            label_options=label_options,
            unit_options=unit_options,
            figsize=figsize,
            sharex=sharex,
            suptitle=suptitle,
        )
    _save_figure(fig, save_to=save_to, dpi=dpi)
    return fig, axes


def render_slice_diagnostics(
    source: GenesisSource,
    *,
    meta=None,
    label_options=None,
    unit_options=None,
    z: float | str | None = "max_energy",
    save_to: str | Path | None = None,
    dpi: int = 140,
    figsize: tuple[float, float] = (8.0, 6.0),
    sharex: bool = True,
    suptitle: str | None = None,
) -> tuple[Figure, AxesArray]:
    with _managed_main_results(source) as result:
        fig, axes = slice_diagnostics(
            result,
            meta=meta,
            label_options=label_options,
            unit_options=unit_options,
            z=z,
            figsize=figsize,
            sharex=sharex,
            suptitle=suptitle,
        )
    _save_figure(fig, save_to=save_to, dpi=dpi)
    return fig, axes


def render_spectrum(
    source: GenesisSource,
    *,
    meta=None,
    label_options=None,
    unit_options=None,
    z: float | str | None = "max_energy",
    use_nearfield: bool = False,
    save_to: str | Path | None = None,
    dpi: int = 140,
    figsize: tuple[float, float] = (8.0, 4.0),
    suptitle: str | None = None,
) -> tuple[Figure, AxesArray]:
    with _managed_main_results(source) as result:
        fig, axes = spectrum_figure(
            result,
            meta=meta,
            label_options=label_options,
            unit_options=unit_options,
            z=z,
            use_nearfield=use_nearfield,
            figsize=figsize,
            suptitle=suptitle,
        )
    _save_figure(fig, save_to=save_to, dpi=dpi)
    return fig, axes


@contextmanager
def _managed_main_results(source: GenesisSource) -> Iterator[MainResults]:
    if isinstance(source, (str, Path)):
        result = MainResults(source)
        try:
            yield result
        finally:
            result.close()
        return
    yield require_main_results(source)


def _save_figure(fig: Figure, *, save_to: str | Path | None, dpi: int) -> None:
    if save_to is None:
        return
    path = Path(save_to)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi)
