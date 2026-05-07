"""Default plotting metadata for Genesis main-output quantities."""

from __future__ import annotations

import re
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from postpro.backends.genesis.models import MainResults

MetaSpec = dict[str, dict[str, str | None]]


_DEFAULT_OVERRIDES: Mapping[str, dict[str, str | None]] = {
    "alphax": {"label": "Alpha x", "symbol": "alpha_x"},
    "alphay": {"label": "Alpha y", "symbol": "alpha_y"},
    "aw": {"label": "Undulator parameter", "symbol": "a_w"},
    "ax": {"label": "Undulator offset x", "symbol": "x_u", "unit": "m"},
    "ay": {"label": "Undulator offset y", "symbol": "y_u", "unit": "m"},
    "betax": {"label": "Beta x", "symbol": "beta_x", "unit": "m"},
    "betay": {"label": "Beta y", "symbol": "beta_y", "unit": "m"},
    "bunching": {"label": "Bunching factor", "symbol": "b"},
    "bunchingphase": {"label": "Bunching phase", "symbol": "phi_b", "unit": "rad"},
    "current": {"label": "Current", "symbol": "I", "unit": "A"},
    "cwd": {"label": "Working directory"},
    "dgrid": {"label": "Field half-grid size", "symbol": "d_grid", "unit": "m"},
    "dz": {"label": "Integration step", "symbol": "dz", "unit": "m"},
    "emitx": {"label": "Emittance x", "symbol": "epsilon_x", "unit": "m"},
    "emity": {"label": "Emittance y", "symbol": "epsilon_y", "unit": "m"},
    "file_basename": {"label": "File basename"},
    "fld_g_energy": {"label": "Field global energy", "symbol": "E_field", "unit": "J"},
    "fld_g_intfar": {"label": "Far-field global intensity", "symbol": "I_far"},
    "fld_g_intnear": {"label": "Near-field global intensity", "symbol": "I_near"},
    "fld_g_xdivergence": {"label": "Field global divergence x", "symbol": "theta_x", "unit": "rad"},
    "fld_g_xpointing": {"label": "Field global pointing x", "symbol": "theta_x0", "unit": "rad"},
    "fld_g_xsize": {"label": "Field global size x", "symbol": "sigma_x^field", "unit": "m"},
    "fld_g_ydivergence": {"label": "Field global divergence y", "symbol": "theta_y", "unit": "rad"},
    "fld_g_ypointing": {"label": "Field global pointing y", "symbol": "theta_y0", "unit": "rad"},
    "fld_g_ysize": {"label": "Field global size y", "symbol": "sigma_y^field", "unit": "m"},
    "fld_xposition": {"label": "Field centroid x", "symbol": "x_field", "unit": "m"},
    "fld_xsize": {"label": "Field size x", "symbol": "sigma_x^field", "unit": "m"},
    "fld_yposition": {"label": "Field centroid y", "symbol": "y_field", "unit": "m"},
    "fld_ysize": {"label": "Field size y", "symbol": "sigma_y^field", "unit": "m"},
    "g_frequency": {"label": "Frequency grid", "symbol": "f", "unit": "Hz"},
    "g_gamma0": {"label": "Reference gamma", "symbol": "gamma_0"},
    "g_lambdaref": {"label": "Reference wavelength", "symbol": "lambda_ref", "unit": "m"},
    "g_one4one": {"label": "One-for-one flag"},
    "g_s": {"label": "Bunch-frame position", "symbol": "s", "unit": "m"},
    "g_sample": {"label": "Slice sampling factor"},
    "g_scan": {"label": "Scan flag"},
    "g_slen": {"label": "Time-window length", "symbol": "L_s", "unit": "m"},
    "g_time": {"label": "Time-dependent flag"},
    "gridspacing": {"label": "Field grid spacing", "symbol": "Delta x", "unit": "m"},
    "HOST": {"label": "Host"},
    "InputFile": {"label": "Input file"},
    "intfar": {"label": "Far-field intensity", "symbol": "I_far"},
    "intnear": {"label": "Near-field intensity", "symbol": "I_near"},
    "ku": {"label": "Undulator wave number", "symbol": "k_u", "unit": "m^-1"},
    "LatticeFile": {"label": "Lattice file"},
    "lslice": {"label": "Slice length", "symbol": "Delta s", "unit": "m"},
    "mpisize": {"label": "MPI size"},
    "ngrid": {"label": "Grid points"},
    "nslice": {"label": "Number of slices"},
    "nslice_eff": {"label": "Effective number of slices"},
    "par_energy": {"label": "Beam mean energy", "symbol": "gamma"},
    "par_energyspread": {"label": "Beam energy spread", "symbol": "sigma_gamma"},
    "par_g_energy": {"label": "Beam global energy", "symbol": "gamma"},
    "par_g_energyspread": {"label": "Beam global energy spread", "symbol": "sigma_gamma"},
    "par_g_xposition": {"label": "Beam global centroid x", "symbol": "x_beam", "unit": "m"},
    "par_g_xsize": {"label": "Beam global size x", "symbol": "sigma_x^beam", "unit": "m"},
    "par_g_yposition": {"label": "Beam global centroid y", "symbol": "y_beam", "unit": "m"},
    "par_g_ysize": {"label": "Beam global size y", "symbol": "sigma_y^beam", "unit": "m"},
    "par_xposition": {"label": "Beam centroid x", "symbol": "x_beam", "unit": "m"},
    "par_xsize": {"label": "Beam size x", "symbol": "sigma_x^beam", "unit": "m"},
    "par_yposition": {"label": "Beam centroid y", "symbol": "y_beam", "unit": "m"},
    "par_ysize": {"label": "Beam size y", "symbol": "sigma_y^beam", "unit": "m"},
    "peakpower": {"label": "Peak power", "symbol": "P_peak", "unit": "W"},
    "phifar": {"label": "Far-field phase", "symbol": "phi_far", "unit": "rad"},
    "phinear": {"label": "Near-field phase", "symbol": "phi_near", "unit": "rad"},
    "power": {"label": "Radiation power", "symbol": "P", "unit": "W"},
    "seed_label": {"label": "Seed label"},
    "slice_num": {"label": "Slice index", "symbol": "i"},
    "slippage": {"label": "Slippage", "symbol": "Delta s_slip", "unit": "m"},
    "t_from_s": {"label": "Time coordinate", "symbol": "t", "unit": "s"},
    "TimeStamp": {"label": "Timestamp"},
    "User": {"label": "User"},
    "wavelength_spectra_int": {"label": "Spectral intensity", "symbol": "S_lambda", "unit": "a.u."},
    "wavelength_spectra_wl": {
        "label": "Wavelength",
        "symbol": "lambda",
        "unit": "m",
    },
    "xdivergence": {"label": "Field divergence x", "symbol": "theta_x", "unit": "rad"},
    "xpointing": {"label": "Field pointing x", "symbol": "theta_x0", "unit": "rad"},
    "ydivergence": {"label": "Field divergence y", "symbol": "theta_y", "unit": "rad"},
    "ypointing": {"label": "Field pointing y", "symbol": "theta_y0", "unit": "rad"},
    "z": {"label": "Lattice position", "symbol": "z", "unit": "m"},
    "zenergy": {"label": "Pulse energy", "symbol": "E_pulse", "unit": "J"},
    "zfwhm_fld": {"label": "Pulse duration FWHM", "symbol": "tau_FWHM", "unit": "s"},
    "zplot": {"label": "Undulator position", "symbol": "z", "unit": "m"},
    "zpower": {"label": "Integrated power", "symbol": "P_int", "unit": "W"},
    "zsigmat_fld": {"label": "Pulse duration RMS", "symbol": "sigma_t", "unit": "s"},
}

_TOKEN_LABELS: Mapping[str, str] = {
    "alphax": "alpha x",
    "alphay": "alpha y",
    "ax": "offset x",
    "ay": "offset y",
    "betax": "beta x",
    "betay": "beta y",
    "chic": "chicane",
    "cx": "corrector x",
    "cy": "corrector y",
    "dgrid": "grid half-size",
    "dz": "integration step",
    "efield": "electric field",
    "emax": "energy max",
    "emin": "energy min",
    "emitx": "emittance x",
    "emity": "emittance y",
    "energyspread": "energy spread",
    "frequency": "frequency",
    "gamma0": "reference gamma",
    "gradx": "gradient x",
    "grady": "gradient y",
    "gridspacing": "grid spacing",
    "intfar": "far-field intensity",
    "intnear": "near-field intensity",
    "ku": "undulator wave number",
    "kx": "roll-off x",
    "ky": "roll-off y",
    "lambdaref": "reference wavelength",
    "ngrid": "grid points",
    "phifar": "far-field phase",
    "phinear": "near-field phase",
    "phaseshift": "phase shift",
    "pxmax": "px max",
    "pxmin": "px min",
    "pxposition": "px centroid",
    "pymax": "py max",
    "pymin": "py min",
    "pyposition": "py centroid",
    "qf": "quadrupole strength",
    "qx": "quadrupole x",
    "qy": "quadrupole y",
    "sample": "sampling factor",
    "scan": "scan flag",
    "slen": "time-window length",
    "time": "time flag",
    "wakefield": "wakefield",
    "xdivergence": "divergence x",
    "xmax": "x max",
    "xmin": "x min",
    "xpointing": "pointing x",
    "xposition": "centroid x",
    "xsize": "size x",
    "ydivergence": "divergence y",
    "ymax": "y max",
    "ymin": "y min",
    "ypointing": "pointing y",
    "yposition": "centroid y",
    "ysize": "size y",
    "zplot": "undulator position",
}

_PREFIX_LABELS: tuple[tuple[str, str], ...] = (
    ("par_g_", "Beam global "),
    ("fld_g_", "Field global "),
    ("par_", "Beam "),
    ("fld_", "Field "),
    ("g_", "Global "),
)


def default_main_results_meta_spec() -> MetaSpec:
    """Return a broad default metadata spec for Genesis `MainResults`.

    Every raw and derived key exposed by `MainResults` is included. Known
    quantities get curated label/unit entries; the rest fall back to a
    generated label and leave unit fields empty for later manual refinement.
    """

    all_keys = sorted(set(MainResults.mapping_v4) | set(MainResults.derived_field_names))
    spec: MetaSpec = {}
    for key in all_keys:
        entry = {
            "label": _humanize_key(key),
            "symbol": None,
            "unit": None,
            "preferred_unit": None,
        }
        entry.update(_DEFAULT_OVERRIDES.get(key, {}))
        spec[key] = entry
    return spec


def build_default_main_results_meta(
    *,
    extra_spec: Mapping[str, Mapping[str, Any]] | None = None,
):
    """Return a `paramstudy.ColumnMetaRegistry` for Genesis `MainResults`.

    `paramstudy` is imported lazily so the rest of `postpro` can still be used
    without requiring it at import time.
    """

    from paramstudy import make_registry

    spec = default_main_results_meta_spec()
    if extra_spec is not None:
        for key, value in extra_spec.items():
            if isinstance(value, Mapping):
                merged = deepcopy(spec.get(key, {"label": _humanize_key(key)}))
                merged.update(value)
                spec[str(key)] = merged
            else:
                raise TypeError(
                    "extra_spec values must be JSON-style metadata mappings."
                )
    return make_registry(spec)


def _humanize_key(key: str) -> str:
    for prefix, label_prefix in _PREFIX_LABELS:
        if key.startswith(prefix):
            return label_prefix + _humanize_core(key[len(prefix) :])
    return _humanize_core(key)


def _humanize_core(text: str) -> str:
    if text in _TOKEN_LABELS:
        return _titlecase(_TOKEN_LABELS[text])

    text = text.replace("-", " ")
    text = re.sub(r"(?<!^)([A-Z])", r" \1", text)
    tokens = [token for token in text.split("_") if token]
    if not tokens:
        return text
    expanded = [_TOKEN_LABELS.get(token, token) for token in tokens]
    return _titlecase(" ".join(expanded))


def _titlecase(text: str) -> str:
    words = text.split()
    if not words:
        return text
    return " ".join(word[0].upper() + word[1:] if word else word for word in words)
