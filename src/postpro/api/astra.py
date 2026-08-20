"""User-facing ASTRA scan-collection APIs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from postpro.api._collect import evaluate_study_rows
from postpro.backends.astra.metric_registry import build_diagnostics_metric_registry
from postpro.backends.astra.scan import DEFAULT_RESULT_RELPATH, load_study
from postpro.core.metric import MetricRegistry


def collect_scan_rows(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = DEFAULT_RESULT_RELPATH,
    registry: MetricRegistry | None = None,
    metric_names: list[str] | tuple[str, ...] | None = None,
    fields: list[str] | tuple[str, ...] | None = None,
    n_slices_energy: int = 50,
    include_params: bool = True,
    eager: bool = False,
    max_workers: int | None = None,
    progress: bool = False,
    skip_missing: bool = False,
) -> list[dict[str, object]]:
    study = load_study(
        cluster_dir,
        result_relpath=result_relpath,
        n_slices_energy=n_slices_energy,
        eager=eager,
    )
    metric_registry = (
        registry
        if registry is not None
        else build_diagnostics_metric_registry(fields=fields)
    )
    names = tuple(metric_names) if metric_names is not None else metric_registry.names()
    return evaluate_study_rows(
        study,
        names,
        metric_registry,
        include_params=include_params,
        max_workers=max_workers,
        progress=progress,
        skip_missing=skip_missing,
    )


def collect_scan_table(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = DEFAULT_RESULT_RELPATH,
    registry: MetricRegistry | None = None,
    metric_names: list[str] | tuple[str, ...] | None = None,
    fields: list[str] | tuple[str, ...] | None = None,
    n_slices_energy: int = 50,
    include_params: bool = True,
    eager: bool = False,
    max_workers: int | None = None,
    progress: bool = False,
    skip_missing: bool = False,
) -> pd.DataFrame:
    rows = collect_scan_rows(
        cluster_dir,
        result_relpath=result_relpath,
        registry=registry,
        metric_names=metric_names,
        fields=fields,
        n_slices_energy=n_slices_energy,
        include_params=include_params,
        eager=eager,
        max_workers=max_workers,
        progress=progress,
        skip_missing=skip_missing,
    )
    return pd.DataFrame(rows)
