from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from postpro.core.study import CaseRecord
from postpro.io.manifest import build_case_records, load_scan_manifest


def _dummy_loader(case: CaseRecord):
    raise AssertionError("loader should not be called by these tests")


def test_load_scan_manifest_reads_cases_csv(tmp_path: Path) -> None:
    (tmp_path / "cases.csv").write_text(
        "case_id,directory,param_a\n1,case001,42\n2,case002,84\n",
        encoding="utf-8",
    )
    df = load_scan_manifest(tmp_path)
    assert df["case_id"].tolist() == [1, 2]
    assert df["directory"].tolist() == ["case001", "case002"]
    assert df["param_a"].tolist() == [42, 84]


def test_load_scan_manifest_missing_cluster_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_scan_manifest(tmp_path / "does-not-exist")


def test_load_scan_manifest_missing_manifest_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_scan_manifest(tmp_path)


def test_load_scan_manifest_missing_columns_raises(tmp_path: Path) -> None:
    (tmp_path / "cases.csv").write_text("case_id,param_a\n1,42\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_scan_manifest(tmp_path)


def test_build_case_records_builds_paths_and_params(tmp_path: Path) -> None:
    (tmp_path / "cases.csv").write_text(
        "case_id,directory,param_a,param_b\n1,case001,42,0.1\n2,case002,84,0.2\n",
        encoding="utf-8",
    )
    df = load_scan_manifest(tmp_path)
    records = build_case_records(
        tmp_path, df, result_relpath="out/ast.dist", result_loader=_dummy_loader
    )
    assert [r.case_id for r in records] == ["1", "2"]
    assert records[0].params == {"param_a": 42, "param_b": 0.1}
    assert records[0].artifact_path == tmp_path / "case001" / "out" / "ast.dist"
    assert records[0].result_loader is _dummy_loader


def test_build_case_records_rejects_absolute_relpath(tmp_path: Path) -> None:
    (tmp_path / "cases.csv").write_text(
        "case_id,directory\n1,case001\n", encoding="utf-8"
    )
    df = load_scan_manifest(tmp_path)
    with pytest.raises(ValueError):
        build_case_records(
            tmp_path, df, result_relpath="/abs/ast.dist", result_loader=_dummy_loader
        )
