from __future__ import annotations

from pathlib import Path
import sys

import h5py
import matplotlib
import numpy as np

matplotlib.use("Agg")

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "paramstudy" / "src"))

from postpro.api.genesis import (
    render_pulse_metrics,
    render_pulse_structure,
    render_slice_diagnostics,
    render_spectrum,
    render_zoverview,
)
from postpro.backends.genesis import MainResults


def _write_genesis_main_output_for_api(path: Path) -> None:
    with h5py.File(path, "w") as f:
        meta = f.create_group("Meta")
        version = meta.create_group("Version")
        version.create_dataset("Major", data=np.array([4], dtype=np.int32))
        meta.create_dataset("cwd", data=np.array([b"/tmp/demo-case"]))
        meta.create_dataset("mpisize", data=np.array([8], dtype=np.int32))

        global_grp = f.create_group("Global")
        global_grp.create_dataset("lambdaref", data=np.array([1.5e-9]))
        global_grp.create_dataset("sample", data=np.array([4]))
        global_grp.create_dataset("s", data=np.array([0.0, 1.0e-6, 2.0e-6]))
        global_grp.create_dataset("frequency", data=np.array([1.0, 2.0, 3.0]))

        lattice = f.create_group("Lattice")
        lattice.create_dataset("zplot", data=np.array([0.0, 1.0]))

        beam = f.create_group("Beam")
        beam.create_dataset("current", data=np.array([[10.0, 20.0, 15.0], [12.0, 18.0, 14.0]]))
        beam.create_dataset("bunching", data=np.array([[0.1, 0.2, 0.15], [0.2, 0.3, 0.25]]))
        beam_global = beam.create_group("Global")
        beam_global.create_dataset("xsize", data=np.array([0.9e-4, 1.0e-4]))
        beam_global.create_dataset("ysize", data=np.array([1.0e-4, 1.1e-4]))

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
        field_global.create_dataset("xsize", data=np.array([0.65e-4, 0.72e-4]))
        field_global.create_dataset("ysize", data=np.array([0.55e-4, 0.70e-4]))


def test_render_functions_accept_file_paths_and_save_outputs(tmp_path: Path) -> None:
    input_path = tmp_path / "mini.out.h5"
    _write_genesis_main_output_for_api(input_path)

    fig1, axes1 = render_zoverview(input_path, save_to=tmp_path / "zoverview.png")
    fig2, axes2 = render_pulse_metrics(input_path, save_to=tmp_path / "pulse_metrics.png")
    fig3, axes3 = render_slice_diagnostics(input_path, save_to=tmp_path / "slice.png")
    fig4, axes4 = render_spectrum(input_path, save_to=tmp_path / "spectrum.png")
    fig5, axes5 = render_pulse_structure(
        input_path,
        x="g_s",
        y="power",
        save_to=tmp_path / "pulse_structure.png",
    )

    assert len(axes1) == 4
    assert len(axes2) == 2
    assert len(axes3) == 2
    assert len(axes4) == 1
    assert len(axes5) == 1

    assert (tmp_path / "zoverview.png").is_file()
    assert (tmp_path / "pulse_metrics.png").is_file()
    assert (tmp_path / "slice.png").is_file()
    assert (tmp_path / "spectrum.png").is_file()
    assert (tmp_path / "pulse_structure.png").is_file()

    plt.close(fig1)
    plt.close(fig2)
    plt.close(fig3)
    plt.close(fig4)
    plt.close(fig5)


def test_render_functions_accept_existing_results_objects(tmp_path: Path) -> None:
    input_path = tmp_path / "mini.out.h5"
    _write_genesis_main_output_for_api(input_path)
    result = MainResults(input_path)

    fig, axes = render_zoverview(result, suptitle="Custom overview")

    assert len(axes) == 4
    assert fig._suptitle is not None
    assert fig._suptitle.get_text() == "Custom overview"
    assert result.zplot.tolist() == [0.0, 1.0]

    plt.close(fig)
    result.close()
