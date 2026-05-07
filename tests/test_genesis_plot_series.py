from __future__ import annotations

from pathlib import Path
import sys

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from postpro.backends.genesis import (
    MainResults,
    slice_profile_series,
    spectrum_series,
    z_energy_series,
    z_field_size_series,
    z_particle_size_series,
    z_pulse_length_series,
)


def _write_genesis_main_output_for_plot_series(path: Path) -> None:
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

        beam = f.create_group("Beam")
        beam.create_dataset("current", data=np.array([[10.0, 20.0, 15.0], [12.0, 18.0, 14.0]]))
        beam.create_dataset("bunching", data=np.array([[0.1, 0.2, 0.15], [0.2, 0.3, 0.25]]))
        beam.create_dataset("xsize", data=np.array([1.0e-4, 1.2e-4]))
        beam.create_dataset("ysize", data=np.array([1.1e-4, 1.3e-4]))
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
        field.create_dataset("xsize", data=np.array([0.7e-4, 0.8e-4]))
        field.create_dataset("ysize", data=np.array([0.6e-4, 0.75e-4]))
        field_global = field.create_group("Global")
        field_global.create_dataset("energy", data=np.array([1.1e-6, 2.2e-6]))
        field_global.create_dataset("xsize", data=np.array([0.65e-4, 0.72e-4]))
        field_global.create_dataset("ysize", data=np.array([0.55e-4, 0.70e-4]))


def test_z_series_extractors_return_expected_curve_groups(tmp_path: Path) -> None:
    path = tmp_path / "mini.out.h5"
    _write_genesis_main_output_for_plot_series(path)
    result = MainResults(path)

    pulse_length = z_pulse_length_series(result)
    energy = z_energy_series(result)
    particle_size = z_particle_size_series(result)
    field_size = z_field_size_series(result)

    assert pulse_length.x_key == "zplot"
    assert pulse_length.curve_keys == ("zsigmat_fld", "zfwhm_fld")
    assert pulse_length.x.tolist() == [0.0, 1.0]

    assert energy.curve_keys == ("zenergy",)
    assert energy.curves[0].values.tolist() == [1.1e-6, 2.2e-6]

    assert particle_size.curve_keys == ("par_g_xsize", "par_g_ysize")
    assert field_size.curve_keys == ("fld_g_xsize", "fld_g_ysize")

    result.close()


def test_slice_and_spectrum_series_include_context(tmp_path: Path) -> None:
    path = tmp_path / "mini.out.h5"
    _write_genesis_main_output_for_plot_series(path)
    result = MainResults(path)

    slice_series = slice_profile_series(result, z=0.8)
    spectrum = spectrum_series(result, z=0.8)

    assert slice_series.x_key == "slice_num"
    assert slice_series.curve_keys == ("current", "bunching")
    assert slice_series.context["z"] == 1.0
    assert slice_series.curves[0].values.tolist() == [12.0, 18.0, 14.0]

    assert spectrum.x_key == "wavelength_spectra_wl"
    assert spectrum.curve_keys == ("wavelength_spectra_int",)
    assert spectrum.context["z"] == 1.0
    assert spectrum.curves[0].values.shape == (3,)

    result.close()
