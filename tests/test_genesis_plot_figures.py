from __future__ import annotations

from pathlib import Path
import sys

import h5py
import matplotlib
import numpy as np

matplotlib.use("Agg")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "paramstudy" / "src"))

from postpro.backends.genesis import (
    MainResults,
    pulse_metrics_figure,
    slice_diagnostics,
    spectrum_figure,
    zoverview,
)


def _write_genesis_main_output_for_plot_figures(path: Path) -> None:
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


def test_zoverview_and_pulse_metrics_build_expected_layouts(tmp_path: Path) -> None:
    path = tmp_path / "mini.out.h5"
    _write_genesis_main_output_for_plot_figures(path)
    result = MainResults(path)

    fig_overview, axes_overview = zoverview(result)
    fig_metrics, axes_metrics = pulse_metrics_figure(result)

    assert len(axes_overview) == 4
    assert axes_overview[0].get_title() == "Pulse length"
    assert axes_overview[1].get_title() == "Pulse energy"
    assert axes_overview[2].get_title() == "Beam transverse size"
    assert axes_overview[3].get_title() == "Field transverse size"
    assert fig_overview._suptitle is not None
    assert fig_overview._suptitle.get_text() == "mini.out.h5"

    assert len(axes_metrics) == 2
    assert axes_metrics[0].get_title() == "Pulse length"
    assert axes_metrics[1].get_title() == "Pulse energy"
    assert fig_metrics._suptitle is not None
    assert fig_metrics._suptitle.get_text() == "Temporal metrics along z"

    result.close()


def test_slice_and_spectrum_figures_resolve_max_energy_z(tmp_path: Path) -> None:
    path = tmp_path / "mini.out.h5"
    _write_genesis_main_output_for_plot_figures(path)
    result = MainResults(path)

    fig_slice, axes_slice = slice_diagnostics(result)
    fig_spectrum, axes_spectrum = spectrum_figure(result)

    assert len(axes_slice) == 2
    assert axes_slice[0].get_title() == "Current profile at z = 1.000 m"
    assert axes_slice[1].get_title() == "Bunching profile at z = 1.000 m"
    assert fig_slice._suptitle is not None
    assert fig_slice._suptitle.get_text() == "mini.out.h5"

    assert len(axes_spectrum) == 1
    assert axes_spectrum[0].get_title() == "Spectrum (farfield) at z = 1.000 m"
    assert fig_spectrum._suptitle is not None
    assert fig_spectrum._suptitle.get_text() == "mini.out.h5"

    result.close()
