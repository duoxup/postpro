"""ASTRA backend for `postpro`.

This namespace analyzes ASTRA phase-space dump files through the external
`partdist` package and exposes them via the solver-agnostic core layer.
"""

from postpro.backends.astra.adapters import (
    AstraResultAdapter,
    adapt_result,
    load_phase_space_result,
    require_phase_space,
    unwrap_result,
)
from postpro.backends.astra.metric_registry import (
    DiagnosticsFieldMetric,
    build_diagnostics_metric_registry,
)
from postpro.backends.astra.models import AstraPhaseSpace, diagnostics_field_names
from postpro.backends.astra.scan import (
    DEFAULT_RESULT_RELPATH,
    load_case_records,
    load_study,
)

__all__ = [
    "AstraPhaseSpace",
    "AstraResultAdapter",
    "DEFAULT_RESULT_RELPATH",
    "DiagnosticsFieldMetric",
    "adapt_result",
    "build_diagnostics_metric_registry",
    "diagnostics_field_names",
    "load_case_records",
    "load_phase_space_result",
    "load_study",
    "require_phase_space",
    "unwrap_result",
]
