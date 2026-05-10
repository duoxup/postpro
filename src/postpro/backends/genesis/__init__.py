"""Genesis backend for `postpro`.

This namespace contains Genesis-specific readers, analysis helpers, and
plotting primitives. Keeping them here prevents solver details from leaking
into the future solver-agnostic core layer.
"""

from postpro.backends.genesis.batch import cluster_statistics
from postpro.backends.genesis.adapters import (
    GenesisResultAdapter,
    adapt_result,
    load_main_result,
    require_main_results,
    unwrap_result,
)
from postpro.backends.genesis.metric_registry import build_stat_metric_registry
from postpro.backends.genesis.models import FieldResults, MainResults, ParticleResults
from postpro.backends.genesis.plot_series import (
    PlotSeries,
    SeriesCurve,
    slice_profile_series,
    spectrum_series,
    z_energy_series,
    z_field_size_series,
    z_particle_size_series,
    z_pulse_length_series,
)
from postpro.backends.genesis.plot_axes import (
    plot_pulse_structure,
    plot_slice_bunching,
    plot_slice_current,
    plot_spectrum,
    plot_z_energy,
    plot_z_field_size,
    plot_z_particle_size,
    plot_z_pulse_length,
)
from postpro.backends.genesis.plot_figures import (
    pulse_metrics_figure,
    pulse_structure_figure,
    slice_diagnostics,
    spectrum_figure,
    zoverview,
)
from postpro.backends.genesis.plot_meta import (
    build_default_main_results_meta,
    default_main_results_meta_spec,
)
from postpro.backends.genesis.scan import discover_case_directories, load_case_records, load_study
from postpro.backends.genesis.stats import statistics_at_max, statistics_at_z, statistics_maxs

__all__ = [
    "FieldResults",
    "GenesisResultAdapter",
    "MainResults",
    "PlotSeries",
    "ParticleResults",
    "SeriesCurve",
    "adapt_result",
    "build_stat_metric_registry",
    "cluster_statistics",
    "build_default_main_results_meta",
    "default_main_results_meta_spec",
    "discover_case_directories",
    "load_main_result",
    "require_main_results",
    "plot_slice_bunching",
    "plot_slice_current",
    "plot_pulse_structure",
    "plot_spectrum",
    "plot_z_energy",
    "plot_z_field_size",
    "plot_z_particle_size",
    "plot_z_pulse_length",
    "pulse_metrics_figure",
    "pulse_structure_figure",
    "slice_profile_series",
    "slice_diagnostics",
    "spectrum_series",
    "spectrum_figure",
    "load_case_records",
    "load_study",
    "statistics_at_max",
    "statistics_at_z",
    "statistics_maxs",
    "unwrap_result",
    "z_energy_series",
    "z_field_size_series",
    "z_particle_size_series",
    "z_pulse_length_series",
    "zoverview",
]
