# ASTRA Scan Backend Design

Date: 2026-08-20
Status: approved for implementation planning

## Goal

Add ASTRA support to `postpro` so that a scan directory of ASTRA cases can be
collected into a one-row-per-case statistics table, mirroring the existing
Genesis `collect_scan_rows(...)` / `collect_scan_table(...)` user API.

Per-case statistics come from ASTRA phase-space dump files, read and analyzed
by the external `partdist` package:

- `partdist.pd3d.read_astra_distribution(path)` -> `ParticleDistribution`
- `partdist.pd3d.compute_beam_diagnostics(dist, n_slices_energy=...)`
  -> `BeamDiagnosticsResult` (a dataclass of ~40 scalar fields with
  `to_dict()`)

## Non-goals

- No ASTRA single-case plotting API in this iteration.
- No reading of ASTRA `*.Xemit.*` / `*.Yemit.*` / `*.Zemit.*` evolution files.
- No glob/z-based dump selection; the dump location is a fixed case-relative
  path.
- No changes to the top-level `postpro` namespace: `postpro.collect_scan_*`
  keeps pointing at the Genesis implementation. ASTRA users import explicitly
  from `postpro.api.astra`.

## Confirmed requirements

- Data source: ASTRA phase-space dump files only.
- Statistics: exactly what `compute_beam_diagnostics` provides; column names
  use the `BeamDiagnosticsResult` field names verbatim (`nemit_x`,
  `sig_E_rel`, `I_peak_smooth`, ...).
- Scan layout: identical to Genesis — a top-level `cases.csv` manifest with
  `case_id`, `directory`, and parameter columns; one subdirectory per case.
- Dump location: fixed case-relative path, default `"ast.dist"`.

## Architecture

New modules and touched files:

```text
src/postpro/
  io/
    manifest.py          # NEW: shared scan-manifest layer
  backends/
    astra/               # NEW backend
      __init__.py
      models.py          # AstraPhaseSpace
      adapters.py        # AstraResultAdapter
      metric_registry.py # per-field diagnostics metrics
      scan.py            # load_case_records / load_study
  api/
    _collect.py          # NEW: shared parallel evaluation helpers
    astra.py             # NEW: collect_scan_rows / collect_scan_table
    genesis.py           # CHANGED: delegate to shared _collect.py
  backends/genesis/
    scan.py              # CHANGED: delegate to shared io/manifest.py
```

### Shared-layer extraction (behavior-preserving)

1. `postpro/io/manifest.py`
   - `load_scan_manifest(cluster_dir) -> pd.DataFrame`: current
     `_load_cases_df` from `backends/genesis/scan.py` (reads `cases.csv`,
     validates `case_id` / `directory` columns) moved verbatim.
   - `build_case_records(cluster_dir, df, result_relpath, result_loader)
     -> list[CaseRecord]`: the solver-agnostic part of the current Genesis
     `load_case_records` (relative-path validation, params extraction,
     `CaseRecord` construction).
   - `backends/genesis/scan.py` and `backends/astra/scan.py` both call these,
     each supplying only its `result_loader` and default `result_relpath`.

2. `postpro/api/_collect.py`
   - `_evaluate_study`, `_evaluate_case_row`, `_close_result` move here from
     `api/genesis.py` (parallel evaluation via `ThreadPoolExecutor`,
     `tqdm` progress, `skip_missing` handling).
   - One generalization: `_close_result` currently special-cases
     `GenesisResultAdapter`; it becomes backend-neutral via
     `target = getattr(result, "source", result)` before attempting
     `close()`. Equivalent behavior for both backends.

### ASTRA backend internals

`models.py` — `AstraPhaseSpace`

- Wraps one ASTRA phase-space dump file.
- `__init__(path, *, n_slices_energy: int = 50)`; no file I/O at
  construction (lazy).
- `.distribution`: cached on first access via
  `partdist.pd3d.read_astra_distribution(path)`.
- `.diagnostics`: cached `BeamDiagnosticsResult` computed on first access via
  `compute_beam_diagnostics(self.distribution,
  n_slices_energy=self.n_slices_energy)`. Caching is the mechanism that lets
  ~40 per-field metrics share one diagnostics computation.
- `available_keys`: the `BeamDiagnosticsResult` field names, derived from
  `dataclasses.fields(...)` (no hand-written list).
- `partdist` is imported lazily inside methods; a missing install raises
  `ImportError` with a clear "the astra backend requires partdist" message.

`adapters.py` — `AstraResultAdapter(ResultSet)`

- Same shape as `GenesisResultAdapter`: `get` / `keys` / `has` / `describe`
  over `AstraPhaseSpace` diagnostics fields.
- `load_phase_space_result(path, *, n_slices_energy=50)` and
  `require_phase_space(result)` helpers mirroring the Genesis naming.

`metric_registry.py`

- `DiagnosticsFieldMetric(field)`: `compute` returns
  `getattr(require_phase_space(result).diagnostics, field)`.
- `build_diagnostics_metric_registry(fields=None) -> MetricRegistry`:
  defaults to one metric per `BeamDiagnosticsResult` field; `fields`
  selects a subset. Unknown field names raise `ValueError`.

`scan.py`

- `load_case_records(cluster_dir, *, result_relpath="ast.dist",
  n_slices_energy=50)` and `load_study(...)` built on `io/manifest.py`;
  the `result_loader` returns
  `AstraResultAdapter(AstraPhaseSpace(path, n_slices_energy=...))`.

## User API

`postpro/api/astra.py`:

```python
def collect_scan_rows(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = "ast.dist",
    registry: MetricRegistry | None = None,
    metric_names: list[str] | tuple[str, ...] | None = None,
    fields: list[str] | None = None,       # subset for the default registry
    n_slices_energy: int = 50,             # passed to compute_beam_diagnostics
    include_params: bool = True,
    eager: bool = False,
    max_workers: int | None = None,
    progress: bool = False,
    skip_missing: bool = False,
) -> list[dict[str, object]]: ...

def collect_scan_table(...) -> pd.DataFrame:   # same params, DataFrame wrapper
```

- Correspondence with the Genesis API: `zs` / `ratios2max` (Genesis-specific)
  are replaced by `fields` / `n_slices_energy` (ASTRA-specific); all other
  parameters match.
- When `registry` is passed explicitly it wins and `fields` is ignored —
  same precedence rule as Genesis `registry` vs `zs` / `ratios2max`.
- No top-level re-export; usage is
  `from postpro.api.astra import collect_scan_table`.

## Dependencies

- `partdist` is NOT added to `pyproject.toml` (sibling-repository soft
  dependency, same precedent as `paramstudy`).
- Lazy import inside `backends/astra/models.py`; README gains a short
  "Optional `partdist`" note and an ASTRA usage section.

## Error handling

Aligned with Genesis behavior:

- Missing `cases.csv` or missing manifest columns -> `FileNotFoundError` /
  `ValueError` (existing shared manifest behavior).
- Missing per-case dump file -> row silently skipped when
  `skip_missing=True`, otherwise `FileNotFoundError` propagates.
- Degenerate beams: `compute_beam_diagnostics` already returns `nan` for
  undefined quantities (e.g. brightness); no extra wrapping.
- Missing `partdist` -> `ImportError` at first ASTRA model use, with an
  actionable message.

## Testing

New `tests/test_astra_scan_api.py` guarded by
`pytest.importorskip("partdist")`:

- Fixture: a synthetic dump written with
  `partdist.pd3d.write_astra_distribution` (guarantees on-disk format), a
  temporary scan directory with `cases.csv` and 2–3 case subdirectories.
- Coverage:
  - `collect_scan_table` column structure (`case_id` + params + diagnostics
    fields);
  - `fields` subset selection;
  - `skip_missing` behavior with one missing dump;
  - parallel path (`max_workers=2`) equals serial results.
- The full existing Genesis test suite must stay green, which validates that
  the shared-layer extraction is behavior-preserving.
