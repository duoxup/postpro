"""Adapters from Genesis backend models to core abstractions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from postpro.backends.genesis.models import FieldResults, MainResults, ParticleResults
from postpro.core.result import ResultSet

GenesisModel = MainResults | FieldResults | ParticleResults


@dataclass(slots=True)
class GenesisResultAdapter(ResultSet):
    """Thin ResultSet adapter over a Genesis backend model."""

    source: GenesisModel

    def get(self, name: str, default: Any = None) -> Any:
        if self.has(name):
            return getattr(self.source, name)
        return default

    def keys(self) -> Iterable[str]:
        if hasattr(self.source, "available_keys"):
            return tuple(getattr(self.source, "available_keys"))
        if hasattr(self.source, "colregistry_names"):
            return tuple(sorted(getattr(self.source, "colregistry_names")))
        return tuple(sorted(self.source.keys()))

    def has(self, name: str) -> bool:
        if hasattr(self.source, "available_keys"):
            return name in set(getattr(self.source, "available_keys"))
        keys = set(self.source.keys())
        if name in keys:
            return True
        return hasattr(self.source, name)

    def describe(self) -> dict[str, Any]:
        raw_keys = tuple(getattr(self.source, "raw_keys", tuple(sorted(self.source.keys()))))
        derived_keys = tuple(getattr(self.source, "derived_keys", ()))
        return {
            "kind": "genesis",
            "model_type": type(self.source).__name__,
            "h5_path": str(self.source.h5_path),
            "version": getattr(self.source, "version", None),
            "keys": tuple(self.keys()),
            "raw_keys": raw_keys,
            "derived_keys": derived_keys,
        }


GenesisResultLike = GenesisModel | GenesisResultAdapter


def adapt_result(source: GenesisModel) -> GenesisResultAdapter:
    """Wrap an existing Genesis model as a core ResultSet."""
    return GenesisResultAdapter(source=source)


def load_main_result(path: str | Path) -> GenesisResultAdapter:
    """Load a Genesis main-output file and wrap it as a ResultSet."""
    return GenesisResultAdapter(source=MainResults(path))


def unwrap_result(result: GenesisResultLike) -> GenesisModel:
    """Return the underlying Genesis model from a model or adapter."""
    if isinstance(result, GenesisResultAdapter):
        return result.source
    return result


def require_main_results(result: GenesisResultLike) -> MainResults:
    """Return a MainResults instance or raise for other Genesis model types."""
    source = unwrap_result(result)
    if isinstance(source, MainResults):
        return source
    raise TypeError(f"Expected MainResults, got {type(source).__name__}.")
