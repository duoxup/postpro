from __future__ import annotations

from pathlib import Path
import sys

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from postpro.backends.genesis import MainResults, adapt_result


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


def test_mainresults_and_adapter_against_minimal_genesis_file(tmp_path: Path) -> None:
    path = tmp_path / "mini.out.h5"
    _write_minimal_genesis_main_output(path)

    result = MainResults(path)
    adapter = adapt_result(result)

    assert result.h5_path.name == "mini.out.h5"
    assert result.zplot.tolist() == [0.0, 1.0]
    assert result.power.shape == (2, 3)

    assert result.peakpower.tolist() == [3.0, 5.0]
    assert result.zenergy.tolist() == [1.1e-6, 2.2e-6]
    assert len(result.t_from_s) == 3

    wl, spec = result.get_spectrum()
    assert wl.shape == (3,)
    assert spec.shape == (3,)

    data_at_z, z_actual = result.get_data_at_z("power", z=0.8)
    assert z_actual == 1.0
    assert data_at_z.tolist() == [2.0, 5.0, 4.0]

    assert adapter.has("power")
    assert adapter.has("peakpower")
    assert adapter.get("peakpower").tolist() == [3.0, 5.0]

    assert "power" in result.raw_keys
    assert "peakpower" in result.derived_keys
    assert "power" in result.available_keys
    assert "peakpower" in result.available_keys

    desc = adapter.describe()
    assert desc["kind"] == "genesis"
    assert desc["model_type"] == "MainResults"
    assert desc["version"] == 4
    assert "power" in desc["raw_keys"]
    assert "peakpower" in desc["derived_keys"]

    result.close()
