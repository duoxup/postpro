"""One-dimensional intensity profile helpers."""

from __future__ import annotations

from typing import Any

import numpy as np


def rms_width(x: np.ndarray, intensity: np.ndarray) -> dict[str, float]:
    """Return RMS width statistics for a 1D intensity profile."""

    x_arr, i_arr = _validate_profile(x, intensity)
    weight_sum = float(np.sum(i_arr))
    if weight_sum <= 0.0:
        return {"mean": float("nan"), "sigma": 0.0}

    mean = float(np.sum(x_arr * i_arr) / weight_sum)
    variance = float(np.sum(i_arr * (x_arr - mean) ** 2) / weight_sum)
    variance = max(variance, 0.0)
    return {"mean": mean, "sigma": float(np.sqrt(variance))}


def fwhm(x: np.ndarray, intensity: np.ndarray) -> dict[str, float]:
    """Return FWHM statistics for a 1D intensity profile."""

    x_arr, i_arr = _validate_profile(x, intensity)
    if i_arr.size == 0:
        return {"width": 0.0}

    peak = float(np.max(i_arr))
    if peak <= 0.0:
        return {"width": 0.0}

    half_max = 0.5 * peak
    above = i_arr >= half_max
    indices = np.flatnonzero(above)
    if indices.size == 0:
        return {"width": 0.0}

    left_idx = int(indices[0])
    right_idx = int(indices[-1])

    left_x = _interpolate_crossing(x_arr, i_arr, left_idx, direction=-1, threshold=half_max)
    right_x = _interpolate_crossing(x_arr, i_arr, right_idx, direction=1, threshold=half_max)
    return {"width": float(max(right_x - left_x, 0.0))}


def _validate_profile(x: np.ndarray, intensity: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x_arr = np.asarray(x, dtype=float).reshape(-1)
    i_arr = np.asarray(intensity, dtype=float).reshape(-1)

    if x_arr.shape != i_arr.shape:
        raise ValueError("x and intensity must have the same shape.")
    if x_arr.ndim != 1:
        raise ValueError("x and intensity must be one-dimensional.")
    if x_arr.size == 0:
        return x_arr, i_arr

    mask = np.isfinite(x_arr) & np.isfinite(i_arr)
    x_arr = x_arr[mask]
    i_arr = i_arr[mask]
    i_arr = np.clip(i_arr, 0.0, None)

    if x_arr.size == 0:
        return x_arr, i_arr

    order = np.argsort(x_arr)
    return x_arr[order], i_arr[order]


def _interpolate_crossing(
    x: np.ndarray,
    intensity: np.ndarray,
    idx: int,
    *,
    direction: int,
    threshold: float,
) -> float:
    if direction not in {-1, 1}:
        raise ValueError("direction must be -1 or 1.")

    neighbor = idx + direction
    if neighbor < 0 or neighbor >= len(x):
        return float(x[idx])

    x0 = float(x[idx])
    y0 = float(intensity[idx])
    x1 = float(x[neighbor])
    y1 = float(intensity[neighbor])

    if (y0 - threshold) == 0.0:
        return x0
    if y0 == y1:
        return x0

    if direction == -1:
        x_low, y_low, x_high, y_high = x1, y1, x0, y0
    else:
        x_low, y_low, x_high, y_high = x0, y0, x1, y1

    if y_high == y_low:
        return x0

    frac = (threshold - y_low) / (y_high - y_low)
    frac = min(max(frac, 0.0), 1.0)
    return float(x_low + frac * (x_high - x_low))
