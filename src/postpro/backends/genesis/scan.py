"""Case discovery and manifest loading for Genesis scan directories."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from postpro.backends.genesis.adapters import load_main_result
from postpro.core.study import CaseRecord, Study


def discover_case_directories(cluster_dir: str | Path) -> list[str]:
    df = _load_cases_df(cluster_dir)
    return [str(directory) for directory in df["directory"].tolist()]


def load_case_records(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = "outputs/g4.000.out.h5",
) -> list[CaseRecord]:
    cluster_path = Path(cluster_dir)
    df = _load_cases_df(cluster_path)
    df_params = df.drop(columns=["case_id", "directory"])
    artifact_relpath = Path(result_relpath)
    if artifact_relpath.is_absolute():
        raise ValueError("result_relpath must be relative to each case directory.")

    records: list[CaseRecord] = []
    for idx in range(len(df)):
        casefolder = str(df.loc[idx, "directory"])
        case_id = str(df.loc[idx, "case_id"])
        caseargs = df_params.loc[idx].to_dict()
        records.append(
            CaseRecord(
                case_id=case_id,
                params=caseargs,
                artifact_path=cluster_path / casefolder / artifact_relpath,
                result_loader=_load_case_result,
            )
        )
    return records


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


def _load_cases_df(cluster_dir: str | Path) -> pd.DataFrame:
    cluster_path = Path(cluster_dir)
    if not cluster_path.exists():
        raise FileNotFoundError("Cluster directory not found.")

    path = cluster_path / "cases.csv"
    if not path.exists():
        raise FileNotFoundError(f"Expected scan manifest at {path}.")

    df = pd.read_csv(path)
    required = {"case_id", "directory"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"cases.csv is missing required columns: {sorted(missing)}")
    return df


def _load_case_result(case: CaseRecord):
    if case.artifact_path is None:
        raise ValueError(f"Case {case.case_id!r} does not define an artifact path.")
    return load_main_result(case.artifact_path)
