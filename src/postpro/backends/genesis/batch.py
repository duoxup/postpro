"""Batch statistics for Genesis scan directories."""

from __future__ import annotations

from tqdm import tqdm

from postpro.api.genesis import collect_scan_rows
from postpro.backends.genesis.metric_registry import build_stat_metric_registry
from postpro.backends.genesis.scan import load_study

def cluster_statistics(
    cluster_dir,
    zs=None,
    ratios2max=None,
    pool=None,
    result_relpath="outputs/g4.000.out.h5",
):
    zs = [] if zs is None else zs
    ratios2max = [1, 0.9, 0.8] if ratios2max is None else ratios2max
    registry = build_stat_metric_registry(zs=zs, ratios2max=ratios2max)

    if pool is None:
        return collect_scan_rows(
            cluster_dir,
            result_relpath=result_relpath,
            registry=registry,
            include_params=True,
            eager=False,
        )

    study = load_study(cluster_dir, result_relpath=result_relpath, eager=True)
    metric_names = registry.names()
    args_list = [(case, metric_names, registry) for case in study.cases]
    return list(tqdm(pool.imap(_evaluate_case, args_list), total=len(study.cases)))


def _evaluate_case(args):
    case, metric_names, registry = args
    row = {"case_id": case.case_id, **case.params}
    row.update({name: registry.get(name).compute(case.result) for name in metric_names})
    return row
