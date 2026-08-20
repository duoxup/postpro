"""Case discovery and manifest loading for Genesis scan directories."""

from __future__ import annotations

from pathlib import Path

from postpro.backends.genesis.adapters import load_main_result
from postpro.core.study import CaseRecord, Study
from postpro.io.manifest import build_case_records, load_scan_manifest


def discover_case_directories(cluster_dir: str | Path) -> list[str]:
    df = load_scan_manifest(cluster_dir)
    return [str(directory) for directory in df["directory"].tolist()]


def load_case_records(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = "outputs/g4.000.out.h5",
) -> list[CaseRecord]:
    df = load_scan_manifest(cluster_dir)
    return build_case_records(
        cluster_dir,
        df,
        result_relpath=result_relpath,
        result_loader=_load_case_result,
    )


def load_study(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = "outputs/g4.000.out.h5",
    eager: bool = False,
) -> Study:
    study = Study(cases=load_case_records(cluster_dir, result_relpath=result_relpath))
    if eager:
        return study.materialize()
    return study


def _load_case_result(case: CaseRecord):
    if case.artifact_path is None:
        raise ValueError(f"Case {case.case_id!r} does not define an artifact path.")
    return load_main_result(case.artifact_path)
