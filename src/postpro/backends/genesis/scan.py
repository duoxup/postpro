"""Case discovery and manifest loading for Genesis scan directories."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from postpro.backends.genesis.adapters import load_main_result
from postpro.core.study import CaseRecord, Study


def discover_case_directories(cluster_dir: str | Path) -> list[str]:
    cluster_path = Path(cluster_dir)
    if not cluster_path.exists():
        raise FileNotFoundError("Cluster directory not found.")

    legacy_index = cluster_path / "CasesInCluster.txt"
    if legacy_index.exists():
        return [line.strip() for line in legacy_index.read_text(encoding="utf-8").splitlines() if line.strip()]

    return sorted(child.name for child in cluster_path.iterdir() if child.is_dir())


def load_case_records(cluster_dir: str | Path, *, version: int = 1) -> list[CaseRecord]:
    cluster_path = Path(cluster_dir)
    if not cluster_path.exists():
        raise FileNotFoundError("Cluster directory not found.")

    match version:
        case 1:
            return _load_case_records_v1(cluster_path)
        case 2:
            return _load_case_records_v2(cluster_path)
        case _:
            raise NotImplementedError(f"Version {version} is not implemented.")


def _load_case_records_v1(cluster_dir: Path) -> list[CaseRecord]:
    casefolders = [
        line.strip()
        for line in (cluster_dir / "CasesInCluster.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    caseargs_list = json.loads((cluster_dir / "CasesInCluster.json").read_text(encoding="utf-8"))

    return [
        CaseRecord(
            case_id=casefolder,
            params=dict(caseargs),
            artifact_path=cluster_dir / casefolder / "g4.000.out.h5",
            result_loader=_load_case_result,
        )
        for casefolder, caseargs in zip(casefolders, caseargs_list, strict=True)
    ]


def _load_case_records_v2(cluster_dir: Path) -> list[CaseRecord]:
    df = pd.read_csv(cluster_dir / "cases.csv")
    df_params = df.drop(columns=["case_id", "directory"])

    records: list[CaseRecord] = []
    for idx in range(len(df)):
        casefolder = str(df.loc[idx, "directory"])
        case_id = str(df.loc[idx, "case_id"])
        caseargs = df_params.loc[idx].to_dict()
        records.append(
            CaseRecord(
                case_id=case_id,
                params=caseargs,
                artifact_path=cluster_dir / casefolder / "outputs/g4.000.out.h5",
                result_loader=_load_case_result,
            )
        )
    return records


def load_study(cluster_dir: str | Path, *, version: int = 1, eager: bool = False) -> Study:
    study = Study(cases=load_case_records(cluster_dir, version=version))
    if eager:
        return study.materialize()
    return study


def _load_case_result(case: CaseRecord):
    if case.artifact_path is None:
        raise ValueError(f"Case {case.case_id!r} does not define an artifact path.")
    return load_main_result(case.artifact_path)
