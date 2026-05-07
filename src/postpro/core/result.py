"""Backend-agnostic result-set abstractions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ResultSet(Protocol):
    """Minimal protocol for a single-case result object."""

    def get(self, name: str, default: Any = None) -> Any:
        """Return a named value from the result set."""

    def keys(self) -> Iterable[str]:
        """Return the available value names."""

    def has(self, name: str) -> bool:
        """Return whether *name* is available."""

    def describe(self) -> dict[str, Any]:
        """Return lightweight metadata about the result set."""


@dataclass(slots=True)
class MappingResultSet:
    """Simple in-memory ResultSet backed by a mapping.

    This is mainly useful for tests, glue code, and future adapters.
    """

    data: Mapping[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, name: str, default: Any = None) -> Any:
        return self.data.get(name, default)

    def keys(self) -> Iterable[str]:
        return self.data.keys()

    def has(self, name: str) -> bool:
        return name in self.data

    def describe(self) -> dict[str, Any]:
        return {
            "kind": "mapping",
            "keys": tuple(self.data.keys()),
            **self.metadata,
        }
