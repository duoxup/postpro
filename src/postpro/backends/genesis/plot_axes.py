"""Axes-level plotting helpers for Genesis single-case results."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
from matplotlib.axes import Axes

from postpro.backends.genesis.adapters import GenesisResultLike
from postpro.backends.genesis.plot_meta import build_default_main_results_meta
from postpro.backends.genesis.plot_series import (
    PlotSeries,
    slice_profile_series,
    spectrum_series,
    z_energy_series,
    z_field_size_series,
    z_particle_size_series,
    z_pulse_length_series,
)


def plot_z_pulse_length(
    ax: Axes,
    result: GenesisResultLike,
    *,
    meta: Any = None,
    label_options: Any = None,
    unit_options: Any = None,
    xlabel: str | None = "z",
    ylabel: str | None = "Duration",
    title: str | None = "Pulse length",
    labels: Mapping[str, str] | None = None,
    grid: bool = True,
    legend: bool = True,
) -> Axes:
    return _plot_series(
        ax,
        z_pulse_length_series(result),
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        ylabel=ylabel,
        xlabel=xlabel,
        title=title,
        labels=dict(labels or {}),
        grid=grid,
        legend=legend,
    )


def plot_z_energy(
    ax: Axes,
    result: GenesisResultLike,
    *,
    meta: Any = None,
    label_options: Any = None,
    unit_options: Any = None,
    xlabel: str | None = "z",
    ylabel: str | None = "Energy",
    title: str | None = "Pulse energy",
    labels: Mapping[str, str] | None = None,
    grid: bool = True,
    legend: bool = True,
) -> Axes:
    return _plot_series(
        ax,
        z_energy_series(result),
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        ylabel=ylabel,
        xlabel=xlabel,
        title=title,
        labels=dict(labels or {}),
        grid=grid,
        legend=legend,
    )


def plot_z_particle_size(
    ax: Axes,
    result: GenesisResultLike,
    *,
    meta: Any = None,
    label_options: Any = None,
    unit_options: Any = None,
    xlabel: str | None = "z",
    ylabel: str | None = "Beam size",
    title: str | None = "Beam transverse size",
    labels: Mapping[str, str] | None = None,
    grid: bool = True,
    legend: bool = True,
) -> Axes:
    return _plot_series(
        ax,
        z_particle_size_series(result),
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        ylabel=ylabel,
        xlabel=xlabel,
        title=title,
        labels={"par_g_xsize": "x size", "par_g_ysize": "y size"} | dict(labels or {}),
        grid=grid,
        legend=legend,
    )


def plot_z_field_size(
    ax: Axes,
    result: GenesisResultLike,
    *,
    meta: Any = None,
    label_options: Any = None,
    unit_options: Any = None,
    xlabel: str | None = "z",
    ylabel: str | None = "Field size",
    title: str | None = "Field transverse size",
    labels: Mapping[str, str] | None = None,
    grid: bool = True,
    legend: bool = True,
) -> Axes:
    return _plot_series(
        ax,
        z_field_size_series(result),
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        ylabel=ylabel,
        xlabel=xlabel,
        title=title,
        labels={"fld_g_xsize": "x size", "fld_g_ysize": "y size"} | dict(labels or {}),
        grid=grid,
        legend=legend,
    )


def plot_slice_current(
    ax: Axes,
    result: GenesisResultLike,
    *,
    meta: Any = None,
    label_options: Any = None,
    unit_options: Any = None,
    z: float | str = "last",
    xlabel: str | None = "Slice index",
    ylabel: str | None = "Current",
    title: str | None = None,
    label: str | None = None,
    grid: bool = True,
) -> Axes:
    series = slice_profile_series(result, z=z, y_keys=("current",))
    return _plot_series(
        ax,
        series,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        ylabel=ylabel,
        xlabel=xlabel,
        title=_slice_title("Current profile", series, title),
        labels={} if label is None else {"current": label},
        grid=grid,
        legend=False,
    )


def plot_slice_bunching(
    ax: Axes,
    result: GenesisResultLike,
    *,
    meta: Any = None,
    label_options: Any = None,
    unit_options: Any = None,
    z: float | str = "last",
    xlabel: str | None = "Slice index",
    ylabel: str | None = "Bunching",
    title: str | None = None,
    label: str | None = None,
    grid: bool = True,
) -> Axes:
    series = slice_profile_series(result, z=z, y_keys=("bunching",))
    return _plot_series(
        ax,
        series,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        ylabel=ylabel,
        xlabel=xlabel,
        title=_slice_title("Bunching profile", series, title),
        labels={} if label is None else {"bunching": label},
        grid=grid,
        legend=False,
    )


def plot_pulse_structure(
    ax: Axes,
    result: GenesisResultLike,
    *,
    meta: Any = None,
    label_options: Any = None,
    unit_options: Any = None,
    z: float | str = "last",
    x_key: str = "t_from_s",
    y_key: str = "intfar",
    xlabel: str | None = "auto",
    ylabel: str | None = None,
    title: str | None = None,
    label: str | None = None,
    sort_x: bool = True,
    grid: bool = True,
) -> Axes:
    series = slice_profile_series(result, z=z, x_key=x_key, y_keys=(y_key,))
    xlabel_text = x_key if xlabel == "auto" else xlabel
    return _plot_series(
        ax,
        series,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        ylabel=ylabel,
        xlabel=xlabel_text,
        title=_slice_title("Pulse structure", series, title),
        labels={} if label is None else {y_key: label},
        grid=grid,
        legend=False,
        sort_x=sort_x,
    )


def plot_spectrum(
    ax: Axes,
    result: GenesisResultLike,
    *,
    meta: Any = None,
    label_options: Any = None,
    unit_options: Any = None,
    z: float | None = None,
    use_nearfield: bool = False,
    xlabel: str | None = "Wavelength",
    ylabel: str | None = "Spectral intensity",
    title: str | None = None,
    label: str | None = None,
    sort_x: bool = True,
    grid: bool = True,
) -> Axes:
    series = spectrum_series(result, z=z, use_nearfield=use_nearfield)
    return _plot_series(
        ax,
        series,
        meta=meta,
        label_options=label_options,
        unit_options=unit_options,
        ylabel=ylabel,
        xlabel=xlabel,
        title=_spectrum_title(series, title),
        labels={} if label is None else {"wavelength_spectra_int": label},
        grid=grid,
        legend=False,
        sort_x=sort_x,
    )


def _plot_series(
    ax: Axes,
    series: PlotSeries,
    *,
    meta: Any,
    label_options: Any,
    unit_options: Any,
    ylabel: str | None,
    xlabel: str | None,
    title: str | None,
    labels: Mapping[str, str],
    grid: bool = True,
    legend: bool = True,
    sort_x: bool = False,
) -> Axes:
    meta = _resolve_meta(meta)
    label_options = _resolve_label_options(label_options)
    unit_options = _resolve_unit_options(unit_options)

    x_scale = _resolve_column_scale(series.x, series.x_key, meta, unit_options)
    y_shared_scale = _resolve_shared_curve_scale(series, meta, unit_options)

    x = _apply_scale(series.x, x_scale)
    order = np.argsort(x) if sort_x else None

    for curve in series.curves:
        curve_scale = y_shared_scale or _resolve_column_scale(
            curve.values,
            curve.key,
            meta,
            unit_options,
        )
        y = _apply_scale(curve.values, curve_scale)
        line_label = labels.get(curve.key) or _default_curve_label(
            curve.key,
            meta,
            label_options,
        )
        if order is not None:
            ax.plot(x[order], y[order], label=line_label)
        else:
            ax.plot(x, y, label=line_label)

    if xlabel is not None:
        ax.set_xlabel(_format_axis_label(xlabel, series.x_key, meta, x_scale, label_options))
    if ylabel is not None:
        ax.set_ylabel(_format_text_with_unit(ylabel, y_shared_scale, label_options))
    else:
        first_curve_key = series.curves[0].key if series.curves else ""
        ax.set_ylabel(_default_axis_label(first_curve_key, meta, y_shared_scale, label_options))
    if title is not None:
        ax.set_title(title)
    if grid:
        ax.grid(True)
    if legend and len(series.curves) > 1:
        ax.legend()
    return ax


def _slice_title(prefix: str, series: PlotSeries, title: str | None) -> str | None:
    if title is not None:
        return title
    z_value = series.context.get("z")
    return None if z_value is None else f"{prefix} at z = {float(z_value):.3f} m"


def _spectrum_title(series: PlotSeries, title: str | None) -> str | None:
    if title is not None:
        return title
    z_value = series.context.get("z")
    field = "nearfield" if series.context.get("use_nearfield", False) else "farfield"
    if z_value is None:
        return f"Spectrum ({field})"
    return f"Spectrum ({field}) at z = {float(z_value):.3f} m"


@dataclass(frozen=True)
class _LabelOptionsFallback:
    prefer_symbol: bool = False
    show_units: bool = True


@dataclass(frozen=True)
class _UnitOptionsFallback:
    autoscale: bool = True
    use_preferred: bool = True


def _resolve_meta(meta: Any):
    if meta is not None:
        return meta
    try:
        return build_default_main_results_meta()
    except ModuleNotFoundError:
        return None


def _resolve_label_options(label_options: Any) -> Any:
    return label_options if label_options is not None else _LabelOptionsFallback()


def _resolve_unit_options(unit_options: Any) -> Any:
    return unit_options if unit_options is not None else _UnitOptionsFallback()


def _resolve_shared_curve_scale(series: PlotSeries, meta: Any, unit_options: Any):
    if meta is None or not series.curves:
        return None
    metas = [meta.get(curve.key) for curve in series.curves]
    first = metas[0]
    if first.unit is None:
        return None
    if not all(m.unit == first.unit and m.preferred_unit == first.preferred_unit for m in metas[1:]):
        return None
    values = np.concatenate([np.asarray(curve.values, dtype=float).ravel() for curve in series.curves])
    return _resolve_scale(values, first, unit_options)


def _resolve_column_scale(values: Any, key: str, meta: Any, unit_options: Any):
    if meta is None:
        return None
    return _resolve_scale(values, meta.get(key), unit_options)


def _resolve_scale(values: Any, column_meta: Any, unit_options: Any):
    if column_meta is None or getattr(column_meta, "unit", None) is None:
        return None
    try:
        from paramstudy import resolve_unit_scale
    except ModuleNotFoundError:
        return None
    return resolve_unit_scale(
        np.asarray(values, dtype=float).ravel(),
        column_meta.unit,
        preferred_unit=column_meta.preferred_unit,
        autoscale=unit_options.autoscale,
        use_preferred=unit_options.use_preferred,
    )


def _apply_scale(values: Any, scale: Any) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    multiplier = scale.multiplier if scale is not None else 1.0
    return array * multiplier


def _default_curve_label(key: str, meta: Any, label_options: Any) -> str:
    if meta is None:
        return key
    return meta.get(key).display_name(key, prefer_symbol=label_options.prefer_symbol)


def _default_axis_label(key: str, meta: Any, scale: Any, label_options: Any) -> str:
    if meta is None:
        return _format_text_with_unit(key, scale, label_options)
    text = meta.get(key).display_name(key, prefer_symbol=label_options.prefer_symbol)
    return _format_text_with_unit(text, scale, label_options)


def _format_axis_label(
    text: str,
    key: str,
    meta: Any,
    scale: Any,
    label_options: Any,
) -> str:
    if meta is not None and text == key:
        return _default_axis_label(key, meta, scale, label_options)
    return _format_text_with_unit(text, scale, label_options)


def _format_text_with_unit(text: str, scale: Any, label_options: Any) -> str:
    if getattr(label_options, "show_units", True) and scale is not None:
        return f"{text} [{scale.render_unit()}]"
    return text
