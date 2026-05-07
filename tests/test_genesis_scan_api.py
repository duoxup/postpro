from __future__ import annotations

from pathlib import Path
import sys

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from postpro.api.genesis import collect_scan_rows, collect_scan_table
from postpro.backends.genesis import build_stat_metric_registry


def _write_minimal_genesis_main_output(
    path: Path,
    *,
    power: np.ndarray,
    intensity_far: np.ndarray,
    energy: np.ndarray,
) -> None:
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
        field.create_dataset("power", data=power)
        field.create_dataset("intensity-farfield", data=intensity_far)
        field.create_dataset("phase-farfield", data=np.zeros_like(intensity_far))
        field.create_dataset("intensity-nearfield", data=intensity_far)
        field.create_dataset("phase-nearfield", data=np.zeros_like(intensity_far))

        field_global = field.create_group("Global")
        field_global.create_dataset("energy", data=energy)


def _write_case(
    cluster_dir: Path,
    *,
    directory: str,
    result_relpath: str = "outputs/g4.000.out.h5",
    power: np.ndarray,
    intensity_far: np.ndarray,
    energy: np.ndarray,
) -> None:
    case_dir = cluster_dir / directory / Path(result_relpath).parent
    case_dir.mkdir(parents=True)
    _write_minimal_genesis_main_output(
        cluster_dir / directory / result_relpath,
        power=power,
        intensity_far=intensity_far,
        energy=energy,
    )


def test_collect_scan_table_returns_one_row_per_case(tmp_path: Path) -> None:
    _write_case(
        tmp_path,
        directory="case001",
        power=np.array([[1.0, 3.0, 2.0], [2.0, 5.0, 4.0]]),
        intensity_far=np.array([[1.0, 4.0, 1.0], [0.0, 2.0, 0.0]]),
        energy=np.array([1.1e-6, 2.2e-6]),
    )
    _write_case(
        tmp_path,
        directory="case002",
        power=np.array([[2.0, 6.0, 3.0], [3.0, 7.0, 5.0]]),
        intensity_far=np.array([[0.5, 3.0, 0.5], [0.0, 1.5, 0.0]]),
        energy=np.array([1.4e-6, 2.8e-6]),
    )
    (tmp_path / "cases.csv").write_text(
        "case_id,directory,param_a,param_b\n"
        "1,case001,42,0.1\n"
        "2,case002,84,0.2\n",
        encoding="utf-8",
    )

    df = collect_scan_table(tmp_path, zs=[1.0], ratios2max=[1.0])

    assert len(df) == 2
    assert df["case_id"].tolist() == ["1", "2"]
    assert df["param_a"].tolist() == [42, 84]
    assert "max_energy" in df.columns
    assert "max_power" in df.columns
    assert "max_ppower" in df.columns
    assert "energy@1.00m" in df.columns
    assert df.loc[df["case_id"] == "1", "max_energy"].item() == 2.2e-6
    assert df.loc[df["case_id"] == "2", "max_energy"].item() == 2.8e-6


def test_collect_scan_rows_support_metric_subset_and_column_order(tmp_path: Path) -> None:
    _write_case(
        tmp_path,
        directory="case001",
        power=np.array([[1.0, 3.0, 2.0], [2.0, 5.0, 4.0]]),
        intensity_far=np.array([[1.0, 4.0, 1.0], [0.0, 2.0, 0.0]]),
        energy=np.array([1.1e-6, 2.2e-6]),
    )
    (tmp_path / "cases.csv").write_text(
        "case_id,directory,param_a\n"
        "1,case001,42\n",
        encoding="utf-8",
    )

    registry = build_stat_metric_registry(zs=[1.0], ratios2max=[])
    rows = collect_scan_rows(
        tmp_path,
        registry=registry,
        metric_names=["max_energy", "energy@1.00m"],
        include_params=False,
    )

    assert rows == [{"case_id": "1", "max_energy": 2.2e-6, "energy@1.00m": 2.2e-6}]


def test_collect_scan_table_accepts_string_cluster_path(tmp_path: Path) -> None:
    _write_case(
        tmp_path,
        directory="case001",
        power=np.array([[1.0, 3.0, 2.0], [2.0, 5.0, 4.0]]),
        intensity_far=np.array([[1.0, 4.0, 1.0], [0.0, 2.0, 0.0]]),
        energy=np.array([1.1e-6, 2.2e-6]),
    )
    (tmp_path / "cases.csv").write_text(
        "case_id,directory,param_a\n"
        "1,case001,42\n",
        encoding="utf-8",
    )

    df = collect_scan_table(str(tmp_path))

    assert df["case_id"].tolist() == ["1"]


def test_collect_scan_table_supports_custom_result_relpath(tmp_path: Path) -> None:
    _write_case(
        tmp_path,
        directory="case001",
        result_relpath="results/g4.000.out.h5",
        power=np.array([[1.0, 3.0, 2.0], [2.0, 5.0, 4.0]]),
        intensity_far=np.array([[1.0, 4.0, 1.0], [0.0, 2.0, 0.0]]),
        energy=np.array([1.1e-6, 2.2e-6]),
    )
    (tmp_path / "cases.csv").write_text(
        "case_id,directory,param_a\n"
        "1,case001,42\n",
        encoding="utf-8",
    )

    df = collect_scan_table(tmp_path, result_relpath="results/g4.000.out.h5")

    assert df["case_id"].tolist() == ["1"]
    assert df["max_energy"].tolist() == [2.2e-6]
