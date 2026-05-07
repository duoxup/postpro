"""Single-case statistics for Genesis result objects."""

from __future__ import annotations

import numpy as np

from postpro.backends.genesis.models import MainResults
from postpro.numerics.c1d import maximum_from_left
from postpro.numerics.intensity import fwhm, rms_width


def statistics_at_z(gmr: MainResults, z: float):
    t = gmr.t_from_s
    intfar, _ = gmr.get_data_at_z("intfar", z=z)
    ww, fspec = gmr.get_spectrum(z=z)
    freq_peak = ww[fspec == np.max(fspec)][0]
    ids = np.argsort(t)
    sigma_t = rms_width(t[ids], intfar[ids])["sigma"]
    width = fwhm(t[ids], intfar[ids])["width"]
    energy, _ = gmr.get_data_at_z("zenergy", z=z)
    return {
        f"peak_frequency@{z:.2f}m": freq_peak,
        f"sigma_t@{z:.2f}m": sigma_t,
        f"fwhm@{z:.2f}m": width,
        f"energy@{z:.2f}m": energy,
    }


def statistics_at_max(gmr: MainResults, ratio2max=1):
    z, _ = maximum_from_left(gmr.zplot, gmr.zenergy, ratio2max)
    res = {}
    stat_z = statistics_at_z(gmr, z)
    for k, v in stat_z.items():
        attrname, _ = k.split("@")
        if not attrname.endswith("energy"):
            nkey = attrname + f"@{ratio2max * 100:.0f}%_max_energy"
            res.update({nkey: v})
    res.update({f"z@{ratio2max * 100:.0f}%_max_energy": z})
    return res


def statistics_maxs(gmr: MainResults):
    max_energy = np.max(gmr.zenergy)
    max_power = np.max(gmr.zpower)
    ppower = np.max(gmr.power, axis=1)
    max_ppower = np.max(ppower)
    return {
        "max_energy": max_energy,
        "max_power": max_power,
        "max_ppower": max_ppower,
    }
