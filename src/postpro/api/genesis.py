"""User-facing Genesis plotting APIs."""

from __future__ import annotations

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from tqdm import tqdm

from postpro.backends.genesis.adapters import (
    GenesisResultAdapter,
    GenesisResultLike,
    require_main_results,
)
from postpro.backends.genesis.metric_registry import build_stat_metric_registry
from postpro.backends.genesis.models import MainResults
from postpro.backends.genesis.plot_figures import (
    pulse_structure_figure,
    pulse_metrics_figure,
    slice_diagnostics,
    spectrum_figure,
    zoverview,
)
from postpro.backends.genesis.scan import load_study
from postpro.core.metric import MetricRegistry, compute_many
from postpro.core.study import CaseRecord, Study

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


def render_pulse_structure(
    source: GenesisSource,
    *,
    meta=None,
    label_options=None,
    unit_options=None,
    z: float | str | None = "max_energy",
    x: str = "t_from_s",
    y: str = "intfar",
    sort_x: bool = True,
    save_to: str | Path | None = None,
    dpi: int = 140,
    figsize: tuple[float, float] = (8.0, 4.0),
    suptitle: str | None = None,
) -> tuple[Figure, AxesArray]:
    with _managed_main_results(source) as result:
        fig, axes = pulse_structure_figure(
            result,
            meta=meta,
            label_options=label_options,
            unit_options=unit_options,
            z=z,
            x_key=x,
            y_key=y,
            sort_x=sort_x,
            figsize=figsize,
            suptitle=suptitle,
        )
    _save_figure(fig, save_to=save_to, dpi=dpi)
    return fig, axes


def collect_scan_rows(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = "outputs/g4.000.out.h5",
    registry: MetricRegistry | None = None,
    metric_names: list[str] | tuple[str, ...] | None = None,
    zs: list[float] | None = None,
    ratios2max: list[float] | None = None,
    include_params: bool = True,
    eager: bool = False,
    max_workers: int | None = None,
    progress: bool = False,
) -> list[dict[str, object]]:
    study = load_study(cluster_dir, result_relpath=result_relpath, eager=eager)
    metric_registry = _resolve_metric_registry(
        registry=registry,
        zs=zs,
        ratios2max=ratios2max,
    )
    names = tuple(metric_names) if metric_names is not None else metric_registry.names()
    return _evaluate_study(
        study,
        names,
        metric_registry,
        include_params=include_params,
        max_workers=max_workers,
        progress=progress,
    )


def collect_scan_table(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = "outputs/g4.000.out.h5",
    registry: MetricRegistry | None = None,
    metric_names: list[str] | tuple[str, ...] | None = None,
    zs: list[float] | None = None,
    ratios2max: list[float] | None = None,
    include_params: bool = True,
    eager: bool = False,
    max_workers: int | None = None,
    progress: bool = False,
) -> pd.DataFrame:
    rows = collect_scan_rows(
        cluster_dir,
        result_relpath=result_relpath,
        registry=registry,
        metric_names=metric_names,
        zs=zs,
        ratios2max=ratios2max,
        include_params=include_params,
        eager=eager,
        max_workers=max_workers,
        progress=progress,
    )
    return pd.DataFrame(rows)


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


def _resolve_metric_registry(
    *,
    registry: MetricRegistry | None,
    zs: list[float] | None,
    ratios2max: list[float] | None,
) -> MetricRegistry:
    if registry is not None:
        return registry
    return build_stat_metric_registry(zs=zs, ratios2max=ratios2max)


def _evaluate_study(
    study: Study,
    names: tuple[str, ...],
    registry: MetricRegistry,
    *,
    include_params: bool,
    max_workers: int | None,
    progress: bool,
) -> list[dict[str, object]]:
    cases = study.cases
    if not cases:
        return []

    def work(case: CaseRecord) -> dict[str, object] | None:
        return _evaluate_case_row(case, names, registry, include_params)

    if max_workers is None or max_workers <= 1:
        iterator = map(work, cases)
        if progress:
            iterator = tqdm(iterator, total=len(cases))
        rows = list(iterator)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            iterator = executor.map(work, cases)
            if progress:
                iterator = tqdm(iterator, total=len(cases))
            rows = list(iterator)
    return [row for row in rows if row is not None]


def _evaluate_case_row(
    case: CaseRecord,
    names: tuple[str, ...],
    registry: MetricRegistry,
    include_params: bool,
) -> dict[str, object] | None:
    try:
        own_result = case.result is None
        result = case.load_result()
    except ValueError:
        return None
    try:
        row: dict[str, object] = {"case_id": case.case_id}
        if include_params:
            row.update(case.params)
        row.update(compute_many(result, names, registry))
        return row
    finally:
        if own_result:
            _close_result(result)


def _close_result(result: object) -> None:
    target = result.source if isinstance(result, GenesisResultAdapter) else result
    close = getattr(target, "close", None)
    if not callable(close):
        return
    try:
        close()
    except Exception:
        pass
