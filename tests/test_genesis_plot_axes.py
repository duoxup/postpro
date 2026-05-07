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

from postpro.backends.genesis import (
    MainResults,
    build_default_main_results_meta,
    plot_slice_bunching,
    plot_slice_current,
    plot_spectrum,
    plot_z_energy,
    plot_z_field_size,
    plot_z_particle_size,
    plot_z_pulse_length,
)


def _write_genesis_main_output_for_plot_axes(path: Path) -> None:
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


def test_z_axes_plotters_draw_expected_lines_and_labels(tmp_path: Path) -> None:
    path = tmp_path / "mini.out.h5"
    _write_genesis_main_output_for_plot_axes(path)
    result = MainResults(path)

    fig, axes = plt.subplots(4, 1, figsize=(7, 9))
    plot_z_pulse_length(axes[0], result)
    plot_z_energy(axes[1], result)
    plot_z_particle_size(axes[2], result)
    plot_z_field_size(axes[3], result)

    assert len(axes[0].lines) == 2
    assert axes[0].get_ylabel().startswith("Duration [")
    assert axes[0].get_title() == "Pulse length"
    assert axes[0].get_legend() is not None

    assert len(axes[1].lines) == 1
    assert axes[1].get_ylabel() == "Energy [uJ]"
    assert axes[1].get_title() == "Pulse energy"

    assert len(axes[2].lines) == 2
    assert axes[2].get_ylabel() == "Beam size [um]"
    assert axes[2].get_title() == "Beam transverse size"
    assert axes[2].get_legend() is not None

    assert len(axes[3].lines) == 2
    assert axes[3].get_ylabel() == "Field size [um]"
    assert axes[3].get_title() == "Field transverse size"
    assert axes[3].get_legend() is not None

    plt.close(fig)
    result.close()


def test_plot_axes_respect_user_meta_overrides(tmp_path: Path) -> None:
    path = tmp_path / "mini.out.h5"
    _write_genesis_main_output_for_plot_axes(path)
    result = MainResults(path)
    meta = build_default_main_results_meta(
        extra_spec={"zenergy": {"preferred_unit": "mJ"}}
    )

    fig, ax = plt.subplots(figsize=(6, 4))
    plot_z_energy(ax, result, meta=meta)

    assert ax.get_ylabel() == "Energy [mJ]"

    plt.close(fig)
    result.close()


def test_slice_and_spectrum_axes_plotters_use_context(tmp_path: Path) -> None:
    path = tmp_path / "mini.out.h5"
    _write_genesis_main_output_for_plot_axes(path)
    result = MainResults(path)

    fig, axes = plt.subplots(3, 1, figsize=(7, 8))
    plot_slice_current(axes[0], result, z=0.8)
    plot_slice_bunching(axes[1], result, z=0.8)
    plot_spectrum(axes[2], result, z=0.8)

    assert len(axes[0].lines) == 1
    assert axes[0].get_ylabel() == "Current [A]"
    assert axes[0].get_title() == "Current profile at z = 1.000 m"

    assert len(axes[1].lines) == 1
    assert axes[1].get_ylabel() == "Bunching"
    assert axes[1].get_title() == "Bunching profile at z = 1.000 m"

    assert len(axes[2].lines) == 1
    assert axes[2].get_xlabel() == "Wavelength [nm]"
    assert axes[2].get_ylabel() == "Spectral intensity [a.u.]"
    assert axes[2].get_title() == "Spectrum (farfield) at z = 1.000 m"
    xdata = axes[2].lines[0].get_xdata()
    assert np.all(np.diff(xdata) >= 0.0)

    plt.close(fig)
    result.close()
