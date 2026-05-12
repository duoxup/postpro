"""Batch statistics for Genesis scan directories."""

from __future__ import annotations

from postpro.api.genesis import collect_scan_rows
from postpro.backends.genesis.metric_registry import build_stat_metric_registry


def cluster_statistics(
    cluster_dir,
    *,
    zs=None,
    ratios2max=None,
    max_workers: int | None = None,
    progress: bool = False,
    result_relpath="outputs/g4.000.out.h5",
):
    zs = [] if zs is None else zs
    ratios2max = [1, 0.9, 0.8] if ratios2max is None else ratios2max
    registry = build_stat_metric_registry(zs=zs, ratios2max=ratios2max)
    return collect_scan_rows(
        cluster_dir,
        result_relpath=result_relpath,
        registry=registry,
        include_params=True,
        max_workers=max_workers,
        progress=progress,
    )
