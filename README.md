# postpro

`postpro` is a modular post-processing package under active refactor.

Current status:
- the package root has been rebuilt around `src/postpro`
- the only backend under active development is `postpro.backends.genesis`
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

## Current Genesis user API

```python
from postpro.api.genesis import (
    render_pulse_metrics,
    render_slice_diagnostics,
    render_spectrum,
    render_zoverview,
)

render_zoverview("g4.000.out.h5", save_to="z_overview.png")
render_pulse_metrics("g4.000.out.h5", save_to="pulse_metrics.png")
render_slice_diagnostics("g4.000.out.h5", save_to="slice_profiles.png")
render_spectrum("g4.000.out.h5", save_to="spectrum.png")
```

Top-level re-exports are also available:

```python
import postpro

postpro.render_zoverview("g4.000.out.h5", save_to="z_overview.png")
```

## Tests

```bash
pytest
```

## Notes

- `outputs/` is treated as generated local output and is ignored by Git.
- real Genesis simulation files are also ignored by Git via `*.out.h5`,
  `*.fld.h5`, and `*.par.h5`.
- the current roadmap is in [docs/roadmap.md](docs/roadmap.md).
