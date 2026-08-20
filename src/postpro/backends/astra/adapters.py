"""Adapters from ASTRA backend models to core abstractions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from postpro.backends.astra.models import AstraPhaseSpace
from postpro.core.result import ResultSet


@dataclass(slots=True)
class AstraResultAdapter(ResultSet):
    """Thin ResultSet adapter over an ASTRA phase-space model."""

    source: AstraPhaseSpace

    def get(self, name: str, default: Any = None) -> Any:
        if self.has(name):
            return getattr(self.source.diagnostics, name)
        return default

    def keys(self) -> Iterable[str]:
        return self.source.available_keys

    def has(self, name: str) -> bool:
        return name in set(self.source.available_keys)

    def describe(self) -> dict[str, Any]:
        return {
            "kind": "astra",
            "model_type": type(self.source).__name__,
            "path": str(self.source.path),
            "n_slices_energy": self.source.n_slices_energy,
            "keys": tuple(self.keys()),
        }


AstraResultLike = AstraPhaseSpace | AstraResultAdapter


def adapt_result(source: AstraPhaseSpace) -> AstraResultAdapter:
    """Wrap an existing ASTRA model as a core ResultSet."""
    return AstraResultAdapter(source=source)


def load_phase_space_result(
    path: str | Path,
    *,
    n_slices_energy: int = 50,
) -> AstraResultAdapter:
    """Point at an ASTRA dump file and wrap it as a ResultSet (lazy read)."""
    return AstraResultAdapter(source=AstraPhaseSpace(path, n_slices_energy=n_slices_energy))


def unwrap_result(result: AstraResultLike) -> AstraPhaseSpace:
    """Return the underlying ASTRA model from a model or adapter."""
    if isinstance(result, AstraResultAdapter):
        return result.source
    return result


def require_phase_space(result: AstraResultLike) -> AstraPhaseSpace:
    """Return an AstraPhaseSpace instance or raise for other inputs."""
    source = unwrap_result(result)
    if isinstance(source, AstraPhaseSpace):
        return source
    raise TypeError(f"Expected AstraPhaseSpace, got {type(source).__name__}.")
