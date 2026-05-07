"""Data extraction helpers for Genesis single-case plotting.

This module prepares stable plot-ready series bundles from `MainResults`.
It does not create figures or axes; that is the responsibility of future
plotting layers built on top of these helpers.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from postpro.backends.genesis.adapters import GenesisResultLike, require_main_results


@dataclass(frozen=True, slots=True)
class SeriesCurve:
    key: str
    values: np.ndarray


@dataclass(frozen=True, slots=True)
class PlotSeries:
    x_key: str
    x: np.ndarray
    curves: tuple[SeriesCurve, ...]
    context: Mapping[str, Any] = field(default_factory=dict)

    @property
    def curve_keys(self) -> tuple[str, ...]:
        return tuple(curve.key for curve in self.curves)


def z_pulse_length_series(result: GenesisResultLike) -> PlotSeries:
    return _z_series(result, y_keys=("zsigmat_fld", "zfwhm_fld"))


def z_energy_series(result: GenesisResultLike) -> PlotSeries:
    return _z_series(result, y_keys=("zenergy",))


def z_particle_size_series(result: GenesisResultLike) -> PlotSeries:
    return _z_series(result, y_keys=("par_g_xsize", "par_g_ysize"))


def z_field_size_series(result: GenesisResultLike) -> PlotSeries:
    return _z_series(result, y_keys=("fld_g_xsize", "fld_g_ysize"))


def slice_profile_series(
    result: GenesisResultLike,
    *,
    z: float | str = "last",
    y_keys: Iterable[str] = ("current", "bunching"),
    x_key: str = "slice_num",
) -> PlotSeries:
    gmr = require_main_results(result)
    x = np.asarray(getattr(gmr, x_key))
    curves = []
    z_actual = None
    for y_key in y_keys:
        values, z_actual = gmr.get_data_at_z(y_key, z=z)
        curves.append(SeriesCurve(key=y_key, values=np.asarray(values)))
    return PlotSeries(
        x_key=x_key,
        x=x,
        curves=tuple(curves),
        context={"z": z_actual},
    )


def spectrum_series(
    result: GenesisResultLike,
    *,
    z: float | None = None,
    use_nearfield: bool = False,
) -> PlotSeries:
    gmr = require_main_results(result)
    wavelength, spectrum = gmr.get_spectrum(z=z, use_nearfield=use_nearfield)
    z_actual = float(gmr.zplot[-1] if z is None else gmr.get_data_at_z("zenergy", z=z)[1])
    return PlotSeries(
        x_key="wavelength_spectra_wl",
        x=np.asarray(wavelength),
        curves=(SeriesCurve(key="wavelength_spectra_int", values=np.asarray(spectrum)),),
        context={"z": z_actual, "use_nearfield": use_nearfield},
    )


def _z_series(result: GenesisResultLike, *, y_keys: tuple[str, ...]) -> PlotSeries:
    gmr = require_main_results(result)
    x = np.asarray(gmr.zplot)
    curves = tuple(
        SeriesCurve(key=y_key, values=np.asarray(getattr(gmr, y_key)))
        for y_key in y_keys
    )
    return PlotSeries(x_key="zplot", x=x, curves=curves)
