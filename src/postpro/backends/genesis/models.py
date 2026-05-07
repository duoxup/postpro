"""Genesis result models."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np
from scipy.constants import c as c0

from postpro.backends.genesis.metrics import calc_spectrum, nearest_index
from postpro.backends.genesis.reader import GenesisH5File
from postpro.numerics.intensity import fwhm, rms_width
from postpro.utils.re import max_slice_index


class MainResults(GenesisH5File):
    expected_suffix = "out.h5"
    derived_field_names = (
        "file_basename",
        "lslice",
        "mpisize",
        "nslice",
        "nslice_eff",
        "peakpower",
        "seed_label",
        "slice_num",
        "t_from_s",
        "wavelength_spectra_int",
        "wavelength_spectra_wl",
        "zfwhm_fld",
        "zenergy",
        "zpower",
        "zsigmat_fld",
    )

    mapping_v4 = dict(
        par_g_energy="/Beam/Global/energy",
        par_g_energyspread="/Beam/Global/energyspread",
        par_g_xposition="/Beam/Global/xposition",
        par_g_xsize="/Beam/Global/xsize",
        par_g_yposition="/Beam/Global/yposition",
        par_g_ysize="/Beam/Global/ysize",
        fld_g_energy="/Field/Global/energy",
        fld_g_intnear="/Field/Global/intensity-nearfield",
        fld_g_intfar="/Field/Global/intensity-farfield",
        fld_g_xdivergence="/Field/Global/xdivergence",
        fld_g_xpointing="/Field/Global/xpointing",
        fld_g_xsize="/Field/Global/xsize",
        fld_g_ydivergence="/Field/Global/ydivergence",
        fld_g_ypointing="/Field/Global/ypointing",
        fld_g_ysize="/Field/Global/ysize",
        g_frequency="/Global/frequency",
        g_gamma0="/Global/gamma0",
        g_lambdaref="/Global/lambdaref",
        g_one4one="/Global/one4one",
        g_s="/Global/s",
        g_sample="/Global/sample",
        g_scan="/Global/scan",
        g_slen="/Global/slen",
        g_time="/Global/time",
        aw="/Lattice/aw",
        ax="/Lattice/ax",
        ay="/Lattice/ay",
        chic_angle="/Lattice/chic_angle",
        chic_lb="/Lattice/chic_lb",
        chic_ld="/Lattice/chic_ld",
        chic_lt="/Lattice/chic_lt",
        cx="/Lattice/cx",
        cy="/Lattice/cy",
        dz="/Lattice/dz",
        gradx="/Lattice/gradx",
        grady="/Lattice/grady",
        ku="/Lattice/ku",
        kx="/Lattice/kx",
        ky="/Lattice/ky",
        phaseshift="/Lattice/phaseshift",
        qf="/Lattice/qf",
        qx="/Lattice/qx",
        qy="/Lattice/qy",
        slippage="/Lattice/slippage",
        z="/Lattice/z",
        zplot="/Lattice/zplot",
        LSCfield="/Beam/LSCfield",
        SSCfield="/Beam/SSCfield",
        alphax="/Beam/alphax",
        alphay="/Beam/alphay",
        betax="/Beam/betax",
        betay="/Beam/betay",
        bunching="/Beam/bunching",
        bunchingphase="/Beam/bunchingphase",
        current="/Beam/current",
        efield="/Beam/efield",
        emax="/Beam/emax",
        emin="/Beam/emin",
        emitx="/Beam/emitx",
        emity="/Beam/emity",
        par_energy="/Beam/par_energy",
        par_energyspread="/Beam/par_energyspread",
        pxmax="/Beam/pxmax",
        pxmin="/Beam/pxmin",
        pxposition="/Beam/pxposition",
        pymax="/Beam/pymax",
        pymin="/Beam/pymin",
        pyposition="/Beam/pyposition",
        wakefield="/Beam/wakefield",
        par_xmax="/Beam/xmax",
        par_xmin="/Beam/xmin",
        par_xposition="/Beam/xposition",
        par_xsize="/Beam/xsize",
        par_ymax="/Beam/ymax",
        par_ymin="/Beam/ymin",
        par_yposition="/Beam/yposition",
        par_ysize="/Beam/ysize",
        dgrid="/Field/dgrid",
        gridspacing="/Field/gridspacing",
        intnear="/Field/intensity-nearfield",
        intfar="/Field/intensity-farfield",
        ngrid="/Field/ngrid",
        phinear="/Field/phase-nearfield",
        phifar="/Field/phase-farfield",
        power="/Field/power",
        xdivergence="/Field/xdivergence",
        xpointing="/Field/xpointing",
        fld_xposition="/Field/xposition",
        fld_xsize="/Field/xsize",
        ydivergence="/Field/ydivergence",
        ypointing="/Field/ypointing",
        fld_yposition="/Field/yposition",
        fld_ysize="/Field/ysize",
        HOST="/Meta/HOST",
        InputFile="/Meta/InputFile",
        LatticeFile="/Meta/LatticeFile",
        TimeStamp="/Meta/TimeStamp",
        User="/Meta/User",
        cwd="/Meta/cwd",
    )
    cache: bool = True
    as_array: bool = True

    def __init__(self, fname: str | Path):
        super().__init__(fname, mapping=self.mapping_v4, cache=self.cache, as_array=self.as_array)

    def get_spectrum(self, z=None, use_nearfield=False):
        if z is None:
            z = self.zplot[-1]
        idx_zgrid = nearest_index(self.zplot, z)
        intensity, phase = (self.intfar, self.phifar)
        if use_nearfield:
            intensity, phase = self.intnear, self.phinear
        return calc_spectrum(intensity[idx_zgrid, :], phase[idx_zgrid, :], lambda0=self.g_lambdaref)

    def get_data_at_z(self, key: str, z: Union[float, str] = "last") -> Tuple[np.ndarray, float]:
        tmp_data = getattr(self, key)
        if tmp_data is None:
            raise KeyError(f"{key!r} --> None.")
        if tmp_data.shape[0] != len(self.zplot):
            raise ValueError("Please check data shape.")
        idx = -1 if z == "last" else nearest_index(self.zplot, z)
        z_new = self.zplot[idx]
        if len(tmp_data.shape) == 1:
            return tmp_data[idx], z_new
        return tmp_data[idx, :], z_new

    @property
    def wavelength_spectra_int(self):
        spectra = [
            calc_spectrum(self.intfar[idx, :], self.phifar[idx, :], lambda0=self.g_lambdaref)[1]
            for idx in range(len(self.zplot))
        ]
        return np.vstack(spectra)

    @property
    def wavelength_spectra_wl(self):
        return calc_spectrum(self.intfar[0, :], self.phifar[0, :], lambda0=self.g_lambdaref)[0]

    @property
    def t_from_s(self):
        return -self.g_s / c0

    @property
    def lslice(self):
        return self.g_lambdaref * self.g_sample

    @property
    def nslice(self):
        return len(self.g_frequency)

    @property
    def slice_num(self):
        return np.arange(self.nslice) + 1

    @property
    def file_basename(self):
        return os.path.basename(self.h5_path)

    @property
    def seed_label(self):
        return self.file_basename.split(".")[1]

    @property
    def nslice_eff(self):
        astra2slices_log_fname = "ast2g4slices." + self.seed_label + ".log"
        try:
            return max_slice_index(os.path.join(self.cwd, astra2slices_log_fname)) + 1
        except Exception:
            return self.nslice - 100

    @property
    def zpower(self):
        return np.sum(self.power, axis=1)

    @property
    def peakpower(self):
        return np.max(self.power, axis=1)

    @property
    def zenergy(self):
        if "Global" in self._f["Field"]:
            return self.fld_g_energy
        return self.zpower * self.lslice / c0

    @property
    def zsigmat_fld(self):
        t = self.g_s / c0
        res = []
        for iz in range(len(self.zplot)):
            profile = self.intfar[iz, :]
            sigmat = rms_width(t, profile)["sigma"] if not np.all(profile == 0) else 0.0
            res.append(sigmat)
        return np.asarray(res) if self.as_array else res

    @property
    def zfwhm_fld(self):
        t = self.g_s / c0
        res = []
        for iz in range(len(self.zplot)):
            profile = self.intfar[iz, :]
            width = fwhm(t, profile)["width"] if not np.all(profile == 0) else 0.0
            res.append(width)
        return np.asarray(res) if self.as_array else res

    @property
    def mpisize(self):
        return int(self._f["/Meta/mpisize"][0])

    def attr2colregistry_name(self, key: str) -> str:
        if key in self.mapping:
            return self.mapping[key].split("/")[-1]
        match key:
            case "t_from_s" | "zsigmat_fld" | "zfwhm_fld":
                return "time"
            case "zpower":
                return "power"
            case "zenergy":
                return "energy"
            case _:
                if hasattr(self, key):
                    return key
                raise KeyError(f"MainResults has no attribute {key!r}")

    @property
    def raw_keys(self):
        return tuple(sorted(self.mapping.keys()))

    @property
    def derived_keys(self):
        return tuple(sorted(self.derived_field_names))

    @property
    def available_keys(self):
        return tuple(sorted(set(self.raw_keys) | set(self.derived_keys)))

    @property
    def colregistry_names(self):
        return self.available_keys


class FieldResults(GenesisH5File):
    expected_suffix = "fld.h5"

    mapping_v4 = dict(
        gridpoints="/gridpoints",
        gridsize="/gridsize",
        int_xy="/int_xy",
        int_xz="/int_xz",
        int_yz="/int_yz",
        refposition="/refposition",
        slicecount="/slicecount",
        slicespacing="slicespacing",
        wavelength="/wavelength",
    )
    cache: bool = True
    as_array: bool = True

    def __init__(self, fname: str):
        super().__init__(fname, mapping=self.mapping_v4, cache=self.cache, as_array=self.as_array)

    def get_slice_int_xy(self, slice_no: int, reshape_array=True, return_real_imag=False):
        if slice_no < 1 or slice_no > self.slicecount:
            raise ValueError(f"{slice_no} exceeds boundary: 1 to self.slicecount")
        slice_key = "slice" + f"{slice_no:0>6}"
        path_real = "/" + slice_key + "/field-real"
        path_imag = "/" + slice_key + "/field-imag"
        if not self.as_array:
            return self._get_obj(path_real), self._get_obj(path_imag)

        data_real = self._maybe_decode_strings(self._read_dataset(path_real))
        data_imag = self._maybe_decode_strings(self._read_dataset(path_imag))

        if reshape_array:
            data_real = data_real.reshape([self.gridpoints, self.gridpoints], order="F")
            data_imag = data_imag.reshape([self.gridpoints, self.gridpoints], order="F")

        if return_real_imag:
            return data_real, data_imag

        data_comp = data_real + 1j * data_imag
        intensity = np.abs(data_comp) ** 2
        phase = np.angle(data_comp)
        return intensity, phase

    def get_prj_int_xy(self, reshape_array=True):
        return np.asarray(self.int_xy).reshape([self.gridpoints, self.gridpoints], order="F")

    def get_int_onaxis(self):
        data = []
        idx_axis = self.gridpoints // 2
        for idx in range(self.slicecount):
            intensity = self.get_slice_int_xy(idx + 1, reshape_array=True, return_real_imag=False)[0]
            data.append(intensity[idx_axis, idx_axis])
        return np.asarray(data) if self.as_array else data

    def _get_int_onaxis_db(self):
        data = []
        idx_axis = self.gridpoints * self.gridpoints // 2
        for idx in range(self.slicecount):
            intensity = self.get_slice_int_xy(idx + 1, reshape_array=False, return_real_imag=False)[0]
            data.append(intensity[idx_axis])
        return np.asarray(data) if self.as_array else data

    @property
    def xgrids(self):
        width_range = self.gridsize * (self.gridpoints - 1)
        return np.linspace(-width_range / 2, width_range / 2, self.gridpoints)

    @property
    def ygrids(self):
        return self.xgrids

    @property
    def zgrids(self):
        return np.arange(0, self.slicespacing * self.slicecount, self.slicespacing) + self.slicespacing / 2


class ParticleResults(GenesisH5File):
    expected_suffix = "par.h5"

    mapping_v4 = dict(
        beamletsize="/beamletsize",
        one4one="/one4one",
        refposition="/refposition",
        slicecount="/slicecount",
        slicelength="/slicelength",
        slicespacing="/slicespacing",
    )
    cache: bool = True
    as_array: bool = True

    def __init__(self, fname: str):
        super().__init__(fname, mapping=self.mapping_v4, cache=self.cache, as_array=self.as_array)

    def _list_slice_groups(self) -> List[Tuple[int, str]]:
        result: List[Tuple[int, str]] = []
        for name in self._f.keys():
            if not name.startswith("slice"):
                continue
            suffix = name[5:]
            if len(suffix) == 6 and suffix.isdigit():
                result.append((int(suffix), name))
        result.sort(key=lambda x: x[0])
        return result

    @staticmethod
    def _theta_to_z(theta: np.ndarray, lambda_r: float) -> np.ndarray:
        theta = np.asarray(theta, dtype=float)
        return theta / (2.0 * np.pi) * float(lambda_r)

    def _compute_particle_charge(self, current: float, n_particles: int) -> float:
        if n_particles <= 0:
            raise ValueError("n_particles must be > 0.")
        slice_length = float(np.asarray(self.slicelength, dtype=float).reshape(-1)[0])
        q_slice = current * (slice_length / c0)
        return q_slice / float(n_particles)

    def get_slice_particles(
        self, slice_index: int, *, lambda_r: Optional[float] = None
    ) -> np.ndarray:
        group_name = f"slice{slice_index:06d}"
        if group_name not in self._f:
            raise KeyError(f"Slice group {group_name!r} not found in file.")

        grp = self._f[group_name]
        current = float(np.asarray(grp["current"][()]).reshape(()))
        x = np.asarray(grp["x"][()], dtype=float)
        y = np.asarray(grp["y"][()], dtype=float)
        gamma = np.asarray(grp["gamma"][()], dtype=float)
        px = np.asarray(grp["px"][()], dtype=float)
        py = np.asarray(grp["py"][()], dtype=float)
        theta = np.asarray(grp["theta"][()], dtype=float)

        n = x.shape[0]
        for arr, name in [(y, "y"), (gamma, "gamma"), (px, "px"), (py, "py"), (theta, "theta")]:
            if arr.shape[0] != n:
                raise ValueError(
                    f"Inconsistent array length in slice {slice_index}: "
                    f"x has {n}, but {name} has {arr.shape[0]}."
                )

        if n == 0:
            return np.empty((0, 8), dtype=float)

        if lambda_r is None:
            lambda_r = self.slicelength

        z = self._theta_to_z(theta, lambda_r=lambda_r)
        z_center = (float(slice_index) - 0.5) * self.slicespacing
        z += z_center

        p2 = gamma**2 - 1.0
        p_perp2 = px**2 + py**2
        pz = np.sqrt(np.maximum(p2 - p_perp2, 0.0))

        q_particle = self._compute_particle_charge(current=current, n_particles=n)
        q = np.full(n, q_particle, dtype=float)
        sliceid = np.full(n, float(slice_index), dtype=float)
        return np.column_stack([x, y, z, px, py, pz, q, sliceid])

    def get_all_particles(
        self,
        exclude_zero_current: bool = True,
        lambda_r: Optional[float] = None,
        zero_tol: float = 0.0,
    ) -> np.ndarray:
        chunks: list[np.ndarray] = []
        for idx, name in self._list_slice_groups():
            grp = self._f[name]
            current = float(np.asarray(grp["current"][()]).reshape(()))
            if exclude_zero_current and abs(current) <= zero_tol:
                continue
            slice_particles = self.get_slice_particles(slice_index=idx, lambda_r=lambda_r)
            if slice_particles.size != 0:
                chunks.append(slice_particles)
        if not chunks:
            return np.empty((0, 8), dtype=float)
        return np.vstack(chunks)

    def current(self):
        all_slices = self._list_slice_groups()
        current_path = [f"/{sl[1]}/current" for sl in all_slices]
        return np.asarray([self._f[p][0] for p in current_path], dtype=float)

    def recompute_current(
        self,
        bins: Optional[Union[int, np.ndarray]] = None,
        *,
        exclude_zero_current: bool = True,
        lambda_r: Optional[float] = None,
        zero_tol: float = 0.0,
    ) -> Tuple[np.ndarray, np.ndarray]:
        particles = self.get_all_particles(
            exclude_zero_current=exclude_zero_current,
            lambda_r=lambda_r,
            zero_tol=zero_tol,
        )
        if particles.size == 0:
            return np.empty((0,), dtype=float), np.empty((0,), dtype=float)

        z = particles[:, 2]
        q = particles[:, 6]
        if bins is None:
            all_slices = self._list_slice_groups()
            n_slices = len(all_slices)
            if n_slices == 0:
                return np.empty((0,), dtype=float), np.empty((0,), dtype=float)
            spacing = float(np.asarray(self.slicespacing, dtype=float).reshape(-1)[0])
            z_edges = np.linspace(0.0, n_slices * spacing, n_slices + 1)
        else:
            z_edges = bins

        q_hist, edges = np.histogram(z, bins=z_edges, weights=q)
        dz = edges[1:] - edges[:-1]
        dz_safe = np.where(dz == 0, np.nan, dz)
        current = q_hist * c0 / dz_safe
        z_centers = 0.5 * (edges[1:] + edges[:-1])
        return z_centers, current

    def recompute_bunching_factor(
        self,
        *,
        harmonic: int = 1,
        exclude_zero_current: bool = True,
        lambda_r: Optional[float] = None,
        zero_tol: float = 0.0,
        return_complex: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray]:
        particles = self.get_all_particles(
            exclude_zero_current=exclude_zero_current,
            lambda_r=lambda_r,
            zero_tol=zero_tol,
        )
        if particles.size == 0:
            dtype = complex if return_complex else float
            return np.empty((0,), dtype=float), np.empty((0,), dtype=dtype)

        z = particles[:, 2]
        q = particles[:, 6]
        if lambda_r is None:
            lambda_r = float(np.asarray(self.slicelength, dtype=float).reshape(-1)[0])
        else:
            lambda_r = float(lambda_r)

        all_slices = self._list_slice_groups()
        n_slices = len(all_slices)
        if n_slices == 0:
            dtype = complex if return_complex else float
            return np.empty((0,), dtype=float), np.empty((0,), dtype=dtype)

        spacing = float(np.asarray(self.slicespacing, dtype=float).reshape(-1)[0])
        z_edges = np.linspace(0.0, n_slices * spacing, n_slices + 1)
        z_centers = 0.5 * (z_edges[1:] + z_edges[:-1])
        k_h = 2.0 * np.pi * float(harmonic) / lambda_r

        bunching = np.zeros(n_slices, dtype=complex)
        for idx in range(n_slices):
            z_left, z_right = z_edges[idx], z_edges[idx + 1]
            if idx == n_slices - 1:
                mask = (z >= z_left) & (z <= z_right)
            else:
                mask = (z >= z_left) & (z < z_right)
            if not np.any(mask):
                continue
            z_bin = z[mask]
            q_bin = q[mask]
            q_sum = np.sum(q_bin)
            if q_sum == 0:
                continue
            theta = k_h * (z_bin - z_centers[idx])
            bunching[idx] = np.sum(q_bin * np.exp(1j * theta)) / q_sum

        if return_complex:
            return z_centers, bunching
        return z_centers, np.abs(bunching)
