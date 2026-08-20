"""ASTRA backend result models built on the external partdist package."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from partdist.pd3d.analysis import BeamDiagnosticsResult
    from partdist.pd3d.core import ParticleDistribution3D

_PARTDIST_ERROR = (
    "The astra backend requires the 'partdist' package, which is not installed. "
    "Install it from its repository (e.g. 'pip install -e <path-to-partdist>')."
)


def _require_partdist():
    try:
        from partdist.pd3d import analysis, io
    except ImportError as exc:
        raise ImportError(_PARTDIST_ERROR) from exc
    return io, analysis


def diagnostics_field_names() -> tuple[str, ...]:
    """Field names of partdist's BeamDiagnosticsResult, in declaration order."""
    _, analysis = _require_partdist()
    return tuple(field.name for field in dataclasses.fields(analysis.BeamDiagnosticsResult))


class AstraPhaseSpace:
    """One ASTRA phase-space dump file, analyzed through partdist.

    Reading and analysis are lazy; the BeamDiagnosticsResult is computed once
    and cached so per-field metrics share a single diagnostics pass.
    """

    def __init__(self, path: str | Path, *, n_slices_energy: int = 50) -> None:
        self.path = Path(path)
        self.n_slices_energy = int(n_slices_energy)
        self._distribution: "ParticleDistribution3D | None" = None
        self._diagnostics: "BeamDiagnosticsResult | None" = None

    @property
    def distribution(self) -> "ParticleDistribution3D":
        if self._distribution is None:
            io, _ = _require_partdist()
            if not self.path.exists():
                raise FileNotFoundError(f"ASTRA distribution file not found: {self.path}")
            self._distribution = io.read_astra_distribution(self.path)
        return self._distribution

    @property
    def diagnostics(self) -> "BeamDiagnosticsResult":
        if self._diagnostics is None:
            _, analysis = _require_partdist()
            self._diagnostics = analysis.compute_beam_diagnostics(
                self.distribution, n_slices_energy=self.n_slices_energy
            )
        return self._diagnostics

    @property
    def available_keys(self) -> tuple[str, ...]:
        return diagnostics_field_names()
