from __future__ import annotations

import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from postpro.backends.genesis import (
    build_stat_metric_registry,
    cluster_statistics,
    load_case_records,
    load_study,
)
from postpro.core.study import CaseRecord


def _write_minimal_genesis_main_output(path: Path) -> None:
    with h5py.File(path, "w") as f:
        meta = f.create_group("Meta")
        version = meta.create_group("Version")
        version.create_dataset("Major", data=np.array([4], dtype=np.int32))
        meta.create_dataset("cwd", data=np.array([b"/tmp/demo-case"]))

        global_grp = f.create_group("Global")
        global_grp.create_dataset("lambdaref", data=np.array([1.5e-9]))
        global_grp.create_dataset("sample", data=np.array([4]))
        global_grp.create_dataset("s", data=np.array([0.0, 1.0e-6, 2.0e-6]))
        global_grp.create_dataset("frequency", data=np.array([1.0, 2.0, 3.0]))

        lattice = f.create_group("Lattice")
        lattice.create_dataset("zplot", data=np.array([0.0, 1.0]))

        field = f.create_group("Field")
        field.create_dataset("power", data=np.array([[1.0, 3.0, 2.0], [2.0, 5.0, 4.0]]))
        field.create_dataset(
            "intensity-farfield",
            data=np.array([[1.0, 4.0, 1.0], [0.0, 2.0, 0.0]]),
        )
        field.create_dataset("phase-farfield", data=np.zeros((2, 3)))
        field.create_dataset(
            "intensity-nearfield",
            data=np.array([[1.0, 4.0, 1.0], [0.0, 2.0, 0.0]]),
        )
        field.create_dataset("phase-nearfield", data=np.zeros((2, 3)))

        field_global = field.create_group("Global")
        field_global.create_dataset("energy", data=np.array([1.1e-6, 2.2e-6]))


def test_genesis_scan_records_use_core_case_record(tmp_path: Path) -> None:
    case_dir = tmp_path / "case001" / "outputs"
    case_dir.mkdir(parents=True)
    _write_minimal_genesis_main_output(case_dir / "g4.000.out.h5")
    (tmp_path / "cases.csv").write_text("case_id,directory,param_a\n1,case001,42\n", encoding="utf-8")

    records = load_case_records(tmp_path)

    assert len(records) == 1
    assert isinstance(records[0], CaseRecord)
    assert records[0].case_id == "1"
    assert records[0].artifact_path is not None
    assert records[0].artifact_path.name == "g4.000.out.h5"
    assert records[0].result is None
    assert records[0].result_loader is not None


def test_genesis_load_study_materializes_results_and_evaluates_metrics(tmp_path: Path) -> None:
    case_dir = tmp_path / "case001" / "outputs"
    case_dir.mkdir(parents=True)
    _write_minimal_genesis_main_output(case_dir / "g4.000.out.h5")
    (tmp_path / "cases.csv").write_text("case_id,directory,param_a\n1,case001,42\n", encoding="utf-8")

    study = load_study(tmp_path, eager=False)
    materialized = study.materialize()

    assert study.case_ids() == ("1",)
    assert materialized.cases[0].result is not None
    assert materialized.cases[0].result.describe()["kind"] == "genesis"

    registry = build_stat_metric_registry(zs=[1.0], ratios2max=[1.0])
    rows = materialized.evaluate(registry.names(), registry)

    assert len(rows) == 1
    assert rows[0]["case_id"] == "1"
    assert rows[0]["param_a"] == 42
    assert rows[0]["max_energy"] == 2.2e-6
    assert rows[0]["max_ppower"] == 5.0
    assert "fwhm@1.00m" in rows[0]
    assert "z@100%_max_energy" in rows[0]


def test_cluster_statistics_uses_study_and_metric_registry(tmp_path: Path) -> None:
    case_dir = tmp_path / "case001" / "outputs"
    case_dir.mkdir(parents=True)
    _write_minimal_genesis_main_output(case_dir / "g4.000.out.h5")
    (tmp_path / "cases.csv").write_text("case_id,directory,param_a\n1,case001,42\n", encoding="utf-8")

    rows = cluster_statistics(tmp_path, zs=[1.0], ratios2max=[1.0])

    assert len(rows) == 1
    assert rows[0]["case_id"] == "1"
    assert rows[0]["param_a"] == 42
    assert rows[0]["max_power"] == 11.0
    assert rows[0]["energy@1.00m"] == 2.2e-6


def test_scan_loading_supports_user_defined_result_relpath(tmp_path: Path) -> None:
    case_dir = tmp_path / "case001" / "results"
    case_dir.mkdir(parents=True)
    _write_minimal_genesis_main_output(case_dir / "g4.000.out.h5")
    (tmp_path / "cases.csv").write_text("case_id,directory,param_a\n1,case001,42\n", encoding="utf-8")

    records = load_case_records(tmp_path, result_relpath="results/g4.000.out.h5")
    study = load_study(tmp_path, result_relpath="results/g4.000.out.h5", eager=False)
    rows = cluster_statistics(
        tmp_path,
        zs=[1.0],
        ratios2max=[1.0],
        result_relpath="results/g4.000.out.h5",
    )

    assert records[0].artifact_path == tmp_path / "case001" / "results" / "g4.000.out.h5"
    assert study.cases[0].artifact_path == tmp_path / "case001" / "results" / "g4.000.out.h5"
    assert rows[0]["max_energy"] == 2.2e-6
