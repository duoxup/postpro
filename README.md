# postpro

`postpro` is a modular post-processing package under active refactor.

Current status:
- the package root has been rebuilt around `src/postpro`
- the primary backend is `postpro.backends.genesis`
- an ASTRA backend collects phase-space dump diagnostics into scan tables
  (requires the optional `partdist` package)
- the `MainResults` path is the most complete and currently supports:
  - HDF5 result loading
  - study/metric integration
  - single-case plotting
  - user-facing rendering APIs

## Install

```bash
pip install -e .
```

Core dependencies are declared in `pyproject.toml`.

## Optional `paramstudy`

Single-case plotting can use `paramstudy` metadata and autoscaling when that
package is importable. `postpro` does not currently declare it as a hard
dependency, because it lives in a separate repository during this refactor.

## Optional `partdist`

The ASTRA backend reads phase-space dump files and computes beam diagnostics
through the `partdist` package. `postpro` does not declare it as a hard
dependency, because it lives in a separate repository during this refactor.
Genesis functionality works without it.

## Current Genesis user API

```python
from postpro.api.genesis import (
    collect_scan_table,
    render_pulse_metrics,
    render_pulse_structure,
    render_slice_diagnostics,
    render_spectrum,
    render_zoverview,
)

render_zoverview("g4.000.out.h5", save_to="z_overview.png")
render_pulse_metrics("g4.000.out.h5", save_to="pulse_metrics.png")
render_pulse_structure("g4.000.out.h5", x="t_from_s", y="intfar", save_to="pulse_structure.png")
render_slice_diagnostics("g4.000.out.h5", save_to="slice_profiles.png")
render_spectrum("g4.000.out.h5", save_to="spectrum.png")
```

Current scan API:

```python
from postpro.api.genesis import collect_scan_table

df = collect_scan_table(
    "path/to/scan",
    zs=[1.0],
    ratios2max=[1.0],
)
```

If your main result file is not stored at `outputs/g4.000.out.h5`, pass a
case-relative path explicitly:

```python
df = collect_scan_table(
    "path/to/scan",
    result_relpath="results/main_output.h5",
)
```

Top-level re-exports are also available:

```python
import postpro

postpro.render_zoverview("g4.000.out.h5", save_to="z_overview.png")
```

## Current ASTRA user API

ASTRA scan collection reads one phase-space dump per case (default
case-relative path `ast.dist`) and computes one row of beam diagnostics per
case via `partdist.compute_beam_diagnostics`:

```python
from postpro.api.astra import collect_scan_table

df = collect_scan_table("path/to/scan")

# subset of diagnostics fields, custom dump location, parallel evaluation
df = collect_scan_table(
    "path/to/scan",
    result_relpath="outputs/final.dist",
    fields=["nemit_x", "nemit_y", "sig_z", "sig_E_rel"],
    max_workers=8,
    skip_missing=True,
)
```

Statistic columns are the `BeamDiagnosticsResult` field names from `partdist`
prefixed with `stat_` (`stat_nemit_x`, `stat_sig_E_rel`, `stat_I_peak_smooth`,
...), which separates them from the `case_id` and manifest parameter columns;
selection via `fields=[...]` / `metric_names=[...]` still uses the unprefixed
names. The same `stat_` prefix applies to the Genesis `collect_scan_*` tables.
ASTRA functions are not re-exported at the top level; import them from
`postpro.api.astra`.

## Tests

```bash
pytest
```

## Notes

- `outputs/` is treated as generated local output and is ignored by Git.
- real Genesis simulation files are also ignored by Git via `*.out.h5`,
  `*.fld.h5`, and `*.par.h5`.
- the current roadmap is in [docs/roadmap.md](docs/roadmap.md).
