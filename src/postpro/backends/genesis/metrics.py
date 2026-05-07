"""Numerical helpers used by the Genesis backend."""

from __future__ import annotations

import numpy as np
from scipy.constants import c as c0


def calc_spectrum(
    intensity,
    phase=None,
    *,
    lambda0: float = 100e-6,
    sample: float = 1,
    freq0: float | None = None,
):
    """Calculate a spectrum from sampled intensity/phase or complex field."""
    if phase is not None:
        signal_comp = np.sqrt(intensity) * (np.cos(phase) + np.sin(phase) * 1j)
    elif np.iscomplexobj(intensity):
        signal_comp = intensity
    else:
        raise ValueError("phase is required unless intensity contains complex fields.")

    nsample = len(signal_comp)
    axis = 0
    spectrum = np.abs(np.fft.fftshift(np.fft.fft(signal_comp, nsample, axis), axis))
    spectrum = spectrum * spectrum

    if freq0 is None:
        freq0 = c0 / (lambda0 / sample)

    freq = np.arange(-nsample / 2, nsample / 2) / nsample * freq0 + freq0
    wavelength = c0 / freq
    return wavelength, spectrum


def nearest_index(a: np.ndarray, x, tie_break: str = "left"):
    """Return the index or indices of the nearest value in a sorted array."""
    a = np.asarray(a)
    x = np.asarray(x)

    i = np.searchsorted(a, x, side="left")
    i_left = np.clip(i - 1, 0, len(a) - 1)
    i_right = np.clip(i, 0, len(a) - 1)

    d_left = np.abs(x - a[i_left])
    d_right = np.abs(a[i_right] - x)

    if tie_break == "left":
        pick_right = d_right < d_left
    elif tie_break == "right":
        pick_right = d_right <= d_left
    else:
        raise ValueError("tie_break must be 'left' or 'right'.")

    idx = np.where(pick_right, i_right, i_left)
    if idx.ndim == 0:
        return int(idx)
    return idx


def nearest_value(a: np.ndarray, x, tie_break: str = "left"):
    """Return the nearest value or values in a sorted array."""
    idx = nearest_index(a, x, tie_break=tie_break)
    return a[idx]
