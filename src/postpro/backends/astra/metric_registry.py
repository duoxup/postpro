"""ASTRA-specific metrics built on top of the core metric abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from postpro.backends.astra.adapters import require_phase_space
from postpro.backends.astra.models import diagnostics_field_names
from postpro.core.metric import MetricRegistry
from postpro.core.result import ResultSet


def build_diagnostics_metric_registry(
    *,
    fields: list[str] | tuple[str, ...] | None = None,
) -> MetricRegistry:
    """Build a registry with one metric per beam-diagnostics field.

    All metrics read from the model's cached BeamDiagnosticsResult, so the
    diagnostics computation runs once per case regardless of field count.
    """
    known = diagnostics_field_names()
    if fields is None:
        selected = known
    else:
        unknown = [name for name in fields if name not in set(known)]
        if unknown:
            raise ValueError(f"Unknown diagnostics fields: {unknown}")
        selected = tuple(fields)
    return MetricRegistry.from_metrics(
        [DiagnosticsFieldMetric(field=name) for name in selected]
    )


@dataclass(frozen=True, slots=True)
class DiagnosticsFieldMetric:
    """Metric returning one field of the cached BeamDiagnosticsResult."""

    field: str

    @property
    def name(self) -> str:
        return self.field

    def compute(self, result: ResultSet) -> Any:
        return getattr(require_phase_space(result).diagnostics, self.field)
