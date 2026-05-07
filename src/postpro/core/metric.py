"""Metric abstractions for derived quantities."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from postpro.core.result import ResultSet


class Metric(Protocol):
    """Protocol for a derived quantity computed from a ResultSet."""

    name: str

    def compute(self, result: ResultSet) -> Any:
        """Compute the metric from a result set."""


@dataclass(slots=True)
class MetricRegistry:
    """Registry of named metric objects."""

    metrics: dict[str, Metric]

    def get(self, name: str) -> Metric:
        try:
            return self.metrics[name]
        except KeyError as exc:
            raise KeyError(f"Unknown metric {name!r}.") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(self.metrics.keys())

    @classmethod
    def from_metrics(cls, metrics: Iterable[Metric]) -> "MetricRegistry":
        return cls(metrics={metric.name: metric for metric in metrics})


def compute_many(
    result: ResultSet,
    metrics: Iterable[str],
    registry: MetricRegistry,
) -> dict[str, Any]:
    """Compute several named metrics against one result set."""

    return {name: registry.get(name).compute(result) for name in metrics}
