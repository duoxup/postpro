"""Modular post-processing package scaffold.

`postpro` is the new top-level package for solver-agnostic post-processing
code and solver-specific backend implementations.
"""

from postpro.backends.genesis import (
    FieldResults,
    MainResults,
    ParticleResults,
)
from postpro.api import (
    render_pulse_metrics,
    render_slice_diagnostics,
    render_spectrum,
    render_zoverview,
)

__all__ = [
    "FieldResults",
    "MainResults",
    "ParticleResults",
    "render_pulse_metrics",
    "render_slice_diagnostics",
    "render_spectrum",
    "render_zoverview",
]
