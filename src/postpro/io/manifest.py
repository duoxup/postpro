"""Shared scan-manifest loading for backend scan directories."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from postpro.core.study import CaseRecord, ResultLoader


def load_scan_manifest(cluster_dir: str | Path) -> pd.DataFrame:
    """Load and validate the `cases.csv` manifest of a scan directory."""
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


def build_case_records(
    cluster_dir: str | Path,
    df: pd.DataFrame,
    *,
    result_relpath: str | Path,
    result_loader: ResultLoader,
) -> list[CaseRecord]:
    """Build one CaseRecord per manifest row, pointing at a case-relative artifact."""
    cluster_path = Path(cluster_dir)
    artifact_relpath = Path(result_relpath)
    if artifact_relpath.is_absolute():
        raise ValueError("result_relpath must be relative to each case directory.")

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
                artifact_path=cluster_path / casefolder / artifact_relpath,
                result_loader=result_loader,
            )
        )
    return records
