"""Case discovery and manifest loading for ASTRA scan directories."""

from __future__ import annotations

from pathlib import Path

from postpro.backends.astra.adapters import AstraResultAdapter
from postpro.backends.astra.models import AstraPhaseSpace
from postpro.core.study import CaseRecord, Study
from postpro.io.manifest import build_case_records, load_scan_manifest

DEFAULT_RESULT_RELPATH = "ast.dist"


def load_case_records(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = DEFAULT_RESULT_RELPATH,
    n_slices_energy: int = 50,
) -> list[CaseRecord]:
    df = load_scan_manifest(cluster_dir)

    def load_case_result(case: CaseRecord) -> AstraResultAdapter:
        if case.artifact_path is None:
            raise ValueError(f"Case {case.case_id!r} does not define an artifact path.")
        return AstraResultAdapter(
            source=AstraPhaseSpace(case.artifact_path, n_slices_energy=n_slices_energy)
        )

    return build_case_records(
        cluster_dir,
        df,
        result_relpath=result_relpath,
        result_loader=load_case_result,
    )


def load_study(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = DEFAULT_RESULT_RELPATH,
    n_slices_energy: int = 50,
    eager: bool = False,
) -> Study:
    study = Study(
        cases=load_case_records(
            cluster_dir,
            result_relpath=result_relpath,
            n_slices_energy=n_slices_energy,
        )
    )
    if eager:
        return study.materialize()
    return study
