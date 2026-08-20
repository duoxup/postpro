# ASTRA Scan Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `postpro.api.astra.collect_scan_rows/collect_scan_table` that turn a scan directory of ASTRA cases into a one-row-per-case beam-diagnostics table, mirroring the Genesis scan API.

**Architecture:** A new `postpro.backends.astra` package wraps `partdist`'s ASTRA reader and `compute_beam_diagnostics` behind the existing core abstractions (`ResultSet`, `MetricRegistry`, `Study`). Solver-agnostic pieces currently living in the Genesis backend (scan-manifest loading, parallel study evaluation) are lifted into shared modules first, then both backends use them.

**Tech Stack:** Python >= 3.10, numpy, pandas, pytest; external soft dependency `partdist` (sibling repo at `/home/duoxup/git_agent/partdist`, already importable in this environment).

**Spec:** `docs/superpowers/specs/2026-08-20-astra-scan-backend-design.md`

## Global Constraints

- `partdist` is NOT added to `pyproject.toml`; it is lazy-imported inside `postpro/backends/astra/models.py` only, and a missing install raises `ImportError` mentioning "partdist".
- ASTRA scan table column names are the `BeamDiagnosticsResult` field names verbatim (`nemit_x`, `sig_E_rel`, `I_peak_smooth`, ...); no renaming.
- Default ASTRA dump location per case: `result_relpath = "ast.dist"`.
- No top-level re-export of ASTRA functions: `postpro.collect_scan_*` keeps pointing at Genesis; ASTRA usage is `from postpro.api.astra import collect_scan_table`.
- All refactors of existing Genesis code must be behavior-preserving: the full existing test suite (25 tests) must stay green after every task.
- Test files follow the repo convention: `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))` before `postpro` imports; ASTRA tests additionally guard with `pytest.importorskip("partdist")`.
- Commit message style: imperative sentence without conventional-commit prefixes (matches `git log`), ending with the `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` trailer.

## Reference: external `partdist` API used by this plan

- `from partdist.pd3d import io, analysis` (the `partdist.pd3d` package imports both submodules).
- `io.read_astra_distribution(path) -> ParticleDistribution3D` — reads an ASTRA text dump. File format: 10 whitespace-separated columns `x[m] y[m] z[m] px[eV/c] py[eV/c] pz[eV/c] t[ns] Q[nC] species status`; row 0 is the reference particle in absolute values, rows 1+ are relative to it (except Q, absolute); the reference particle is included as the first particle of the returned distribution; `species`/`status` become integer extras.
- `analysis.compute_beam_diagnostics(dist, n_slices_energy=50) -> BeamDiagnosticsResult` — a frozen-style dataclass of 41 scalar fields (`n_total`, `n_alive`, `n_lost`, `Q_total_C`, ..., `nemit_x`, ..., `brightness_6d`) with `.to_dict()`. Particles with `status < 0` are treated as lost.
- `analysis.BeamDiagnosticsResult` — use `dataclasses.fields(...)` to enumerate field names.

---

### Task 1: Shared scan-manifest module `postpro/io/manifest.py`

**Files:**
- Create: `src/postpro/io/manifest.py`
- Modify: `src/postpro/backends/genesis/scan.py`
- Test: `tests/test_scan_manifest.py`

**Interfaces:**
- Consumes: `postpro.core.study.CaseRecord`, `postpro.core.study.ResultLoader` (existing).
- Produces (used by Tasks 6):
  - `load_scan_manifest(cluster_dir: str | Path) -> pd.DataFrame`
  - `build_case_records(cluster_dir: str | Path, df: pd.DataFrame, *, result_relpath: str | Path, result_loader: ResultLoader) -> list[CaseRecord]`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_scan_manifest.py`:

```python
from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from postpro.core.study import CaseRecord
from postpro.io.manifest import build_case_records, load_scan_manifest


def _dummy_loader(case: CaseRecord):
    raise AssertionError("loader should not be called by these tests")


def test_load_scan_manifest_reads_cases_csv(tmp_path: Path) -> None:
    (tmp_path / "cases.csv").write_text(
        "case_id,directory,param_a\n1,case001,42\n2,case002,84\n",
        encoding="utf-8",
    )
    df = load_scan_manifest(tmp_path)
    assert df["case_id"].tolist() == [1, 2]
    assert df["directory"].tolist() == ["case001", "case002"]
    assert df["param_a"].tolist() == [42, 84]


def test_load_scan_manifest_missing_cluster_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_scan_manifest(tmp_path / "does-not-exist")


def test_load_scan_manifest_missing_manifest_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_scan_manifest(tmp_path)


def test_load_scan_manifest_missing_columns_raises(tmp_path: Path) -> None:
    (tmp_path / "cases.csv").write_text("case_id,param_a\n1,42\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_scan_manifest(tmp_path)


def test_build_case_records_builds_paths_and_params(tmp_path: Path) -> None:
    (tmp_path / "cases.csv").write_text(
        "case_id,directory,param_a,param_b\n1,case001,42,0.1\n2,case002,84,0.2\n",
        encoding="utf-8",
    )
    df = load_scan_manifest(tmp_path)
    records = build_case_records(
        tmp_path, df, result_relpath="out/ast.dist", result_loader=_dummy_loader
    )
    assert [r.case_id for r in records] == ["1", "2"]
    assert records[0].params == {"param_a": 42, "param_b": 0.1}
    assert records[0].artifact_path == tmp_path / "case001" / "out" / "ast.dist"
    assert records[0].result_loader is _dummy_loader


def test_build_case_records_rejects_absolute_relpath(tmp_path: Path) -> None:
    (tmp_path / "cases.csv").write_text(
        "case_id,directory\n1,case001\n", encoding="utf-8"
    )
    df = load_scan_manifest(tmp_path)
    with pytest.raises(ValueError):
        build_case_records(
            tmp_path, df, result_relpath="/abs/ast.dist", result_loader=_dummy_loader
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_scan_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'postpro.io.manifest'`

- [ ] **Step 3: Create `src/postpro/io/manifest.py`**

The bodies are moved verbatim from `src/postpro/backends/genesis/scan.py` (`_load_cases_df` and the generic part of `load_case_records`):

```python
"""Shared scan-manifest loading for backend scan directories."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from postpro.core.study import CaseRecord, ResultLoader


def load_scan_manifest(cluster_dir: str | Path) -> pd.DataFrame:
    """Load and validate the `cases.csv` manifest of a scan directory."""
    cluster_path = Path(cluster_dir)
    if not cluster_path.exists():
        raise FileNotFoundError("Cluster directory not found.")

    path = cluster_path / "cases.csv"
    if not path.exists():
        raise FileNotFoundError(f"Expected scan manifest at {path}.")

    df = pd.read_csv(path)
    required = {"case_id", "directory"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"cases.csv is missing required columns: {sorted(missing)}")
    return df


def build_case_records(
    cluster_dir: str | Path,
    df: pd.DataFrame,
    *,
    result_relpath: str | Path,
    result_loader: ResultLoader,
) -> list[CaseRecord]:
    """Build one CaseRecord per manifest row, pointing at a case-relative artifact."""
    cluster_path = Path(cluster_dir)
    artifact_relpath = Path(result_relpath)
    if artifact_relpath.is_absolute():
        raise ValueError("result_relpath must be relative to each case directory.")

    df_params = df.drop(columns=["case_id", "directory"])
    records: list[CaseRecord] = []
    for idx in range(len(df)):
        casefolder = str(df.loc[idx, "directory"])
        case_id = str(df.loc[idx, "case_id"])
        caseargs = df_params.loc[idx].to_dict()
        records.append(
            CaseRecord(
                case_id=case_id,
                params=caseargs,
                artifact_path=cluster_path / casefolder / artifact_relpath,
                result_loader=result_loader,
            )
        )
    return records
```

- [ ] **Step 4: Rewire `src/postpro/backends/genesis/scan.py` to delegate**

Replace the whole file content with:

```python
"""Case discovery and manifest loading for Genesis scan directories."""

from __future__ import annotations

from pathlib import Path

from postpro.backends.genesis.adapters import load_main_result
from postpro.core.study import CaseRecord, Study
from postpro.io.manifest import build_case_records, load_scan_manifest


def discover_case_directories(cluster_dir: str | Path) -> list[str]:
    df = load_scan_manifest(cluster_dir)
    return [str(directory) for directory in df["directory"].tolist()]


def load_case_records(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = "outputs/g4.000.out.h5",
) -> list[CaseRecord]:
    df = load_scan_manifest(cluster_dir)
    return build_case_records(
        cluster_dir,
        df,
        result_relpath=result_relpath,
        result_loader=_load_case_result,
    )


def load_study(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = "outputs/g4.000.out.h5",
    eager: bool = False,
) -> Study:
    study = Study(cases=load_case_records(cluster_dir, result_relpath=result_relpath))
    if eager:
        return study.materialize()
    return study


def _load_case_result(case: CaseRecord):
    if case.artifact_path is None:
        raise ValueError(f"Case {case.case_id!r} does not define an artifact path.")
    return load_main_result(case.artifact_path)
```

- [ ] **Step 5: Run the new tests and the full suite**

Run: `python -m pytest tests/test_scan_manifest.py -v && python -m pytest -q`
Expected: new tests PASS; full suite 25 + 6 passed (no failures).

- [ ] **Step 6: Commit**

```bash
git add src/postpro/io/manifest.py src/postpro/backends/genesis/scan.py tests/test_scan_manifest.py
git commit -m "Extract shared scan-manifest layer into postpro.io.manifest

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Shared study-evaluation helpers `postpro/api/_collect.py`

**Files:**
- Create: `src/postpro/api/_collect.py`
- Modify: `src/postpro/api/genesis.py`

**Interfaces:**
- Consumes: `postpro.core.metric.MetricRegistry`, `compute_many`; `postpro.core.study.CaseRecord`, `Study` (existing).
- Produces (used by Task 7):
  - `evaluate_study_rows(study: Study, names: tuple[str, ...], registry: MetricRegistry, *, include_params: bool, max_workers: int | None, progress: bool, skip_missing: bool = False) -> list[dict[str, object]]`

This is a behavior-preserving move of `_evaluate_study`, `_evaluate_case_row`, and `_close_result` out of `api/genesis.py`. The only change: `_close_result` no longer special-cases `GenesisResultAdapter`; it unwraps via `getattr(result, "source", result)`, which is equivalent for Genesis (the adapter's `source` attribute) and also works for the ASTRA adapter added later. The test cycle for this task is the existing suite.

- [ ] **Step 1: Create `src/postpro/api/_collect.py`**

```python
"""Shared scan-collection helpers for user-facing backend APIs."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tqdm import tqdm

from postpro.core.metric import MetricRegistry, compute_many
from postpro.core.study import CaseRecord, Study


def evaluate_study_rows(
    study: Study,
    names: tuple[str, ...],
    registry: MetricRegistry,
    *,
    include_params: bool,
    max_workers: int | None,
    progress: bool,
    skip_missing: bool = False,
) -> list[dict[str, object]]:
    cases = study.cases
    if not cases:
        return []

    def work(case: CaseRecord) -> dict[str, object] | None:
        return _evaluate_case_row(case, names, registry, include_params, skip_missing)

    if max_workers is None or max_workers <= 1:
        iterator = map(work, cases)
        if progress:
            iterator = tqdm(iterator, total=len(cases))
        rows = list(iterator)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            iterator = executor.map(work, cases)
            if progress:
                iterator = tqdm(iterator, total=len(cases))
            rows = list(iterator)
    return [row for row in rows if row is not None]


def _evaluate_case_row(
    case: CaseRecord,
    names: tuple[str, ...],
    registry: MetricRegistry,
    include_params: bool,
    skip_missing: bool = False,
) -> dict[str, object] | None:
    if skip_missing and case.result is None and case.artifact_path is not None:
        if not Path(case.artifact_path).exists():
            return None
    try:
        own_result = case.result is None
        result = case.load_result()
    except ValueError:
        return None
    except FileNotFoundError:
        if skip_missing:
            return None
        raise
    try:
        row: dict[str, object] = {"case_id": case.case_id}
        if include_params:
            row.update(case.params)
        row.update(compute_many(result, names, registry))
        return row
    finally:
        if own_result:
            _close_result(result)


def _close_result(result: object) -> None:
    target = getattr(result, "source", result)
    close = getattr(target, "close", None)
    if not callable(close):
        return
    try:
        close()
    except Exception:
        pass
```

- [ ] **Step 2: Rewire `src/postpro/api/genesis.py`**

In `src/postpro/api/genesis.py`:

1. Delete the three functions `_evaluate_study`, `_evaluate_case_row`, `_close_result` (lines 270-339) — they now live in `_collect.py`.
2. Replace the call `return _evaluate_study(` inside `collect_scan_rows` with `return evaluate_study_rows(` (arguments unchanged).
3. Update imports at the top of the file. After the move the exact changes are:
   - Remove `from concurrent.futures import ThreadPoolExecutor` (only used by `_evaluate_study`).
   - Remove `from tqdm import tqdm` (only used by `_evaluate_study`).
   - In the `postpro.backends.genesis.adapters` import, remove `GenesisResultAdapter` (only used by `_close_result`); keep `GenesisResultLike` and `require_main_results`.
   - Change `from postpro.core.metric import MetricRegistry, compute_many` to `from postpro.core.metric import MetricRegistry` (`compute_many` only used by `_evaluate_case_row`).
   - Delete `from postpro.core.study import CaseRecord, Study` entirely (`CaseRecord` only used by the moved functions; `Study` was only a type annotation on `_evaluate_study`).
   - Add `from postpro.api._collect import evaluate_study_rows`.

- [ ] **Step 3: Run the full suite**

Run: `python -m pytest -q`
Expected: all tests pass (31 at this point). If an unused-import slips through, tests still pass — additionally run `python -c "import postpro.api.genesis"` to confirm the module imports cleanly.

- [ ] **Step 4: Commit**

```bash
git add src/postpro/api/_collect.py src/postpro/api/genesis.py
git commit -m "Extract shared study-evaluation helpers into postpro.api._collect

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: ASTRA phase-space model `postpro/backends/astra/models.py`

**Files:**
- Create: `src/postpro/backends/astra/__init__.py` (empty placeholder for now; filled in Task 6)
- Create: `src/postpro/backends/astra/models.py`
- Test: `tests/test_astra_scan_api.py` (new file; later tasks append to it)

**Interfaces:**
- Consumes: `partdist.pd3d.io.read_astra_distribution`, `partdist.pd3d.analysis.compute_beam_diagnostics` / `BeamDiagnosticsResult` (external, lazy).
- Produces (used by Tasks 4-7):
  - `class AstraPhaseSpace: __init__(path: str | Path, *, n_slices_energy: int = 50)`; attributes `path: Path`, `n_slices_energy: int`; cached properties `distribution`, `diagnostics`; property `available_keys: tuple[str, ...]`
  - `diagnostics_field_names() -> tuple[str, ...]`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_astra_scan_api.py` with the shared dump-writer fixture and model tests:

```python
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

pytest.importorskip("partdist")

from postpro.backends.astra.models import AstraPhaseSpace, diagnostics_field_names


def _write_astra_dump(path: Path, *, n: int = 200, seed: int = 7, n_lost: int = 1) -> None:
    """Write a synthetic ASTRA dump: reference row + a Gaussian cloud.

    Columns: x[m] y[m] z[m] px[eV/c] py[eV/c] pz[eV/c] t[ns] Q[nC] species status.
    Row 0 is the absolute reference particle; remaining rows are relative.
    """
    rng = np.random.default_rng(seed)
    ref = np.array([[0.0, 0.0, 0.5, 0.0, 0.0, 20.0e6, 0.0, -0.001, 1, 5]])
    x = rng.normal(0.0, 1.0e-4, n)
    y = rng.normal(0.0, 1.0e-4, n)
    z = rng.normal(0.0, 1.0e-3, n)
    px = rng.normal(0.0, 1.0e3, n)
    py = rng.normal(0.0, 1.0e3, n)
    pz = rng.normal(0.0, 2.0e4, n)
    t_ns = -(z / 2.998e8) * 1.0e9
    q_nc = np.full(n, -0.001)
    species = np.ones(n)
    status = np.full(n, 5.0)
    status[:n_lost] = -1.0
    body = np.column_stack([x, y, z, px, py, pz, t_ns, q_nc, species, status])
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(path, np.vstack([ref, body]), fmt=["%.6E"] * 8 + ["%d"] * 2)


def test_diagnostics_field_names_cover_known_fields() -> None:
    names = diagnostics_field_names()
    assert isinstance(names, tuple)
    for expected in ("n_total", "nemit_x", "sig_E_rel", "I_peak_smooth", "brightness_6d"):
        assert expected in names


def test_phase_space_computes_and_caches_diagnostics(tmp_path: Path) -> None:
    dump = tmp_path / "ast.dist"
    _write_astra_dump(dump)
    ps = AstraPhaseSpace(dump)

    diag = ps.diagnostics
    assert diag is ps.diagnostics  # cached, computed once
    assert diag.n_total == 201  # 200 body particles + reference
    assert diag.n_lost == 1
    assert diag.n_alive == 200
    assert 1.8e7 < diag.mean_E_kin_eV < 2.1e7  # ~19.5 MeV kinetic energy
    assert diag.nemit_x > 0.0
    assert ps.available_keys == diagnostics_field_names()


def test_phase_space_is_lazy_and_reports_missing_file(tmp_path: Path) -> None:
    ps = AstraPhaseSpace(tmp_path / "missing.dist")  # construction must not raise
    with pytest.raises(FileNotFoundError):
        _ = ps.diagnostics


def test_phase_space_passes_n_slices_energy_through(tmp_path: Path) -> None:
    dump = tmp_path / "ast.dist"
    _write_astra_dump(dump)
    coarse = AstraPhaseSpace(dump, n_slices_energy=5)
    assert coarse.n_slices_energy == 5
    assert np.isfinite(coarse.diagnostics.sig_E_uncorr_eV)


def test_missing_partdist_raises_actionable_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A module set to None in sys.modules makes `from partdist.pd3d import ...`
    # raise ImportError, simulating a missing install.
    monkeypatch.setitem(sys.modules, "partdist.pd3d", None)
    ps = AstraPhaseSpace(tmp_path / "ast.dist")
    with pytest.raises(ImportError, match="partdist"):
        _ = ps.available_keys
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_astra_scan_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'postpro.backends.astra'`

- [ ] **Step 3: Create the package and model**

Create `src/postpro/backends/astra/__init__.py` containing only a docstring for now (exports are added in Task 6):

```python
"""ASTRA backend for `postpro` (phase-space dump analysis via partdist)."""
```

Create `src/postpro/backends/astra/models.py`:

```python
"""ASTRA backend result models built on the external partdist package."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from partdist.pd3d.analysis import BeamDiagnosticsResult
    from partdist.pd3d.core import ParticleDistribution3D

_PARTDIST_ERROR = (
    "The astra backend requires the 'partdist' package, which is not installed. "
    "Install it from its repository (e.g. 'pip install -e <path-to-partdist>')."
)


def _require_partdist():
    try:
        from partdist.pd3d import analysis, io
    except ImportError as exc:
        raise ImportError(_PARTDIST_ERROR) from exc
    return io, analysis


def diagnostics_field_names() -> tuple[str, ...]:
    """Field names of partdist's BeamDiagnosticsResult, in declaration order."""
    _, analysis = _require_partdist()
    return tuple(field.name for field in dataclasses.fields(analysis.BeamDiagnosticsResult))


class AstraPhaseSpace:
    """One ASTRA phase-space dump file, analyzed through partdist.

    Reading and analysis are lazy; the BeamDiagnosticsResult is computed once
    and cached so per-field metrics share a single diagnostics pass.
    """

    def __init__(self, path: str | Path, *, n_slices_energy: int = 50) -> None:
        self.path = Path(path)
        self.n_slices_energy = int(n_slices_energy)
        self._distribution: "ParticleDistribution3D | None" = None
        self._diagnostics: "BeamDiagnosticsResult | None" = None

    @property
    def distribution(self) -> "ParticleDistribution3D":
        if self._distribution is None:
            io, _ = _require_partdist()
            if not self.path.exists():
                raise FileNotFoundError(f"ASTRA distribution file not found: {self.path}")
            self._distribution = io.read_astra_distribution(self.path)
        return self._distribution

    @property
    def diagnostics(self) -> "BeamDiagnosticsResult":
        if self._diagnostics is None:
            _, analysis = _require_partdist()
            self._diagnostics = analysis.compute_beam_diagnostics(
                self.distribution, n_slices_energy=self.n_slices_energy
            )
        return self._diagnostics

    @property
    def available_keys(self) -> tuple[str, ...]:
        return diagnostics_field_names()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_astra_scan_api.py -v && python -m pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/postpro/backends/astra/ tests/test_astra_scan_api.py
git commit -m "Add ASTRA phase-space model backed by partdist diagnostics

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: ASTRA result adapter `postpro/backends/astra/adapters.py`

**Files:**
- Create: `src/postpro/backends/astra/adapters.py`
- Test: `tests/test_astra_scan_api.py` (append)

**Interfaces:**
- Consumes: `AstraPhaseSpace`, `diagnostics_field_names` (Task 3); `postpro.core.result.ResultSet`.
- Produces (used by Tasks 5-7):
  - `class AstraResultAdapter(ResultSet)` with attribute `source: AstraPhaseSpace` and methods `get(name, default=None)`, `keys()`, `has(name)`, `describe()`
  - `AstraResultLike = AstraPhaseSpace | AstraResultAdapter`
  - `adapt_result(source: AstraPhaseSpace) -> AstraResultAdapter`
  - `load_phase_space_result(path: str | Path, *, n_slices_energy: int = 50) -> AstraResultAdapter`
  - `unwrap_result(result: AstraResultLike) -> AstraPhaseSpace`
  - `require_phase_space(result: AstraResultLike) -> AstraPhaseSpace`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_astra_scan_api.py`:

```python
from postpro.backends.astra.adapters import (
    AstraResultAdapter,
    adapt_result,
    load_phase_space_result,
    require_phase_space,
    unwrap_result,
)


def test_adapter_exposes_diagnostics_fields(tmp_path: Path) -> None:
    dump = tmp_path / "ast.dist"
    _write_astra_dump(dump)
    adapter = load_phase_space_result(dump)

    assert isinstance(adapter, AstraResultAdapter)
    assert adapter.has("nemit_x")
    assert not adapter.has("no_such_field")
    assert adapter.get("no_such_field", default=-1) == -1
    assert adapter.get("n_total") == 201
    assert set(adapter.keys()) == set(diagnostics_field_names())

    described = adapter.describe()
    assert described["kind"] == "astra"
    assert described["model_type"] == "AstraPhaseSpace"
    assert described["path"] == str(dump)


def test_adapter_unwrap_and_require(tmp_path: Path) -> None:
    dump = tmp_path / "ast.dist"
    _write_astra_dump(dump)
    model = AstraPhaseSpace(dump)
    adapter = adapt_result(model)

    assert unwrap_result(adapter) is model
    assert unwrap_result(model) is model
    assert require_phase_space(adapter) is model
    with pytest.raises(TypeError):
        require_phase_space(object())  # type: ignore[arg-type]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_astra_scan_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'postpro.backends.astra.adapters'`

- [ ] **Step 3: Create `src/postpro/backends/astra/adapters.py`**

Mirrors `backends/genesis/adapters.py`; `get` reads fields from the cached diagnostics object:

```python
"""Adapters from ASTRA backend models to core abstractions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from postpro.backends.astra.models import AstraPhaseSpace
from postpro.core.result import ResultSet


@dataclass(slots=True)
class AstraResultAdapter(ResultSet):
    """Thin ResultSet adapter over an ASTRA phase-space model."""

    source: AstraPhaseSpace

    def get(self, name: str, default: Any = None) -> Any:
        if self.has(name):
            return getattr(self.source.diagnostics, name)
        return default

    def keys(self) -> Iterable[str]:
        return self.source.available_keys

    def has(self, name: str) -> bool:
        return name in set(self.source.available_keys)

    def describe(self) -> dict[str, Any]:
        return {
            "kind": "astra",
            "model_type": type(self.source).__name__,
            "path": str(self.source.path),
            "n_slices_energy": self.source.n_slices_energy,
            "keys": tuple(self.keys()),
        }


AstraResultLike = AstraPhaseSpace | AstraResultAdapter


def adapt_result(source: AstraPhaseSpace) -> AstraResultAdapter:
    """Wrap an existing ASTRA model as a core ResultSet."""
    return AstraResultAdapter(source=source)


def load_phase_space_result(
    path: str | Path,
    *,
    n_slices_energy: int = 50,
) -> AstraResultAdapter:
    """Point at an ASTRA dump file and wrap it as a ResultSet (lazy read)."""
    return AstraResultAdapter(source=AstraPhaseSpace(path, n_slices_energy=n_slices_energy))


def unwrap_result(result: AstraResultLike) -> AstraPhaseSpace:
    """Return the underlying ASTRA model from a model or adapter."""
    if isinstance(result, AstraResultAdapter):
        return result.source
    return result


def require_phase_space(result: AstraResultLike) -> AstraPhaseSpace:
    """Return an AstraPhaseSpace instance or raise for other inputs."""
    source = unwrap_result(result)
    if isinstance(source, AstraPhaseSpace):
        return source
    raise TypeError(f"Expected AstraPhaseSpace, got {type(source).__name__}.")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_astra_scan_api.py -v && python -m pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/postpro/backends/astra/adapters.py tests/test_astra_scan_api.py
git commit -m "Add ASTRA ResultSet adapter

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: ASTRA metric registry `postpro/backends/astra/metric_registry.py`

**Files:**
- Create: `src/postpro/backends/astra/metric_registry.py`
- Test: `tests/test_astra_scan_api.py` (append)

**Interfaces:**
- Consumes: `require_phase_space` (Task 4), `diagnostics_field_names` (Task 3), `postpro.core.metric.MetricRegistry`.
- Produces (used by Task 7):
  - `build_diagnostics_metric_registry(*, fields: list[str] | tuple[str, ...] | None = None) -> MetricRegistry`
  - `class DiagnosticsFieldMetric` (frozen dataclass; attribute `field: str`; property `name -> str` returning the field name; `compute(result) -> Any`)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_astra_scan_api.py`:

```python
from postpro.backends.astra.metric_registry import build_diagnostics_metric_registry
from postpro.core.metric import compute_many


def test_default_registry_has_one_metric_per_diagnostics_field() -> None:
    registry = build_diagnostics_metric_registry()
    assert registry.names() == diagnostics_field_names()


def test_registry_fields_subset_and_unknown_field(tmp_path: Path) -> None:
    dump = tmp_path / "ast.dist"
    _write_astra_dump(dump)
    adapter = load_phase_space_result(dump)

    registry = build_diagnostics_metric_registry(fields=["nemit_x", "sig_z"])
    assert registry.names() == ("nemit_x", "sig_z")
    values = compute_many(adapter, registry.names(), registry)
    assert values["nemit_x"] == adapter.get("nemit_x")
    assert values["sig_z"] == adapter.get("sig_z")

    with pytest.raises(ValueError):
        build_diagnostics_metric_registry(fields=["nemit_x", "no_such_field"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_astra_scan_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'postpro.backends.astra.metric_registry'`

- [ ] **Step 3: Create `src/postpro/backends/astra/metric_registry.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_astra_scan_api.py -v && python -m pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/postpro/backends/astra/metric_registry.py tests/test_astra_scan_api.py
git commit -m "Add ASTRA diagnostics metric registry

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: ASTRA scan module and backend exports

**Files:**
- Create: `src/postpro/backends/astra/scan.py`
- Modify: `src/postpro/backends/astra/__init__.py`
- Test: `tests/test_astra_scan_api.py` (append)

**Interfaces:**
- Consumes: `load_scan_manifest`, `build_case_records` (Task 1); `AstraResultAdapter`, `AstraPhaseSpace` (Tasks 3-4); `postpro.core.study.CaseRecord`, `Study`.
- Produces (used by Task 7):
  - `DEFAULT_RESULT_RELPATH = "ast.dist"` (module constant)
  - `load_case_records(cluster_dir: str | Path, *, result_relpath: str | Path = DEFAULT_RESULT_RELPATH, n_slices_energy: int = 50) -> list[CaseRecord]`
  - `load_study(cluster_dir: str | Path, *, result_relpath: str | Path = DEFAULT_RESULT_RELPATH, n_slices_energy: int = 50, eager: bool = False) -> Study`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_astra_scan_api.py` (also add the scan-directory fixture helper used by Task 7):

```python
from postpro.backends.astra.scan import load_case_records, load_study


def _write_astra_scan_dir(cluster_dir: Path, *, n_cases: int = 2) -> None:
    lines = ["case_id,directory,param_a,param_b"]
    for idx in range(n_cases):
        directory = f"case{idx:03d}"
        lines.append(f"{idx},{directory},{10 * (idx + 1)},{0.1 * (idx + 1):.1f}")
        _write_astra_dump(cluster_dir / directory / "ast.dist", seed=idx)
    (cluster_dir / "cases.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_load_case_records_uses_default_relpath(tmp_path: Path) -> None:
    _write_astra_scan_dir(tmp_path)
    records = load_case_records(tmp_path)
    assert [record.case_id for record in records] == ["0", "1"]
    assert records[0].artifact_path == tmp_path / "case000" / "ast.dist"
    assert records[1].params == {"param_a": 20, "param_b": 0.2}


def test_load_study_evaluates_diagnostics_metrics(tmp_path: Path) -> None:
    _write_astra_scan_dir(tmp_path)
    study = load_study(tmp_path)
    registry = build_diagnostics_metric_registry(fields=["n_total", "nemit_x"])
    rows = study.evaluate(("n_total", "nemit_x"), registry)
    assert [row["case_id"] for row in rows] == ["0", "1"]
    assert all(row["n_total"] == 201 for row in rows)
    assert all(row["nemit_x"] > 0.0 for row in rows)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_astra_scan_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'postpro.backends.astra.scan'`

- [ ] **Step 3: Create `src/postpro/backends/astra/scan.py`**

```python
"""Case discovery and manifest loading for ASTRA scan directories."""

from __future__ import annotations

from pathlib import Path

from postpro.backends.astra.adapters import AstraResultAdapter
from postpro.backends.astra.models import AstraPhaseSpace
from postpro.core.study import CaseRecord, Study
from postpro.io.manifest import build_case_records, load_scan_manifest

DEFAULT_RESULT_RELPATH = "ast.dist"


def load_case_records(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = DEFAULT_RESULT_RELPATH,
    n_slices_energy: int = 50,
) -> list[CaseRecord]:
    df = load_scan_manifest(cluster_dir)

    def load_case_result(case: CaseRecord) -> AstraResultAdapter:
        if case.artifact_path is None:
            raise ValueError(f"Case {case.case_id!r} does not define an artifact path.")
        return AstraResultAdapter(
            source=AstraPhaseSpace(case.artifact_path, n_slices_energy=n_slices_energy)
        )

    return build_case_records(
        cluster_dir,
        df,
        result_relpath=result_relpath,
        result_loader=load_case_result,
    )


def load_study(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = DEFAULT_RESULT_RELPATH,
    n_slices_energy: int = 50,
    eager: bool = False,
) -> Study:
    study = Study(
        cases=load_case_records(
            cluster_dir,
            result_relpath=result_relpath,
            n_slices_energy=n_slices_energy,
        )
    )
    if eager:
        return study.materialize()
    return study
```

- [ ] **Step 4: Fill `src/postpro/backends/astra/__init__.py` exports**

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_astra_scan_api.py -v && python -m pytest -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/postpro/backends/astra/scan.py src/postpro/backends/astra/__init__.py tests/test_astra_scan_api.py
git commit -m "Add ASTRA scan loading and backend exports

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: User API `postpro/api/astra.py`

**Files:**
- Create: `src/postpro/api/astra.py`
- Test: `tests/test_astra_scan_api.py` (append)

**Interfaces:**
- Consumes: `evaluate_study_rows` (Task 2); `build_diagnostics_metric_registry` (Task 5); `DEFAULT_RESULT_RELPATH`, `load_study` (Task 6); `postpro.core.metric.MetricRegistry`.
- Produces (public API):
  - `collect_scan_rows(cluster_dir, *, result_relpath="ast.dist", registry=None, metric_names=None, fields=None, n_slices_energy=50, include_params=True, eager=False, max_workers=None, progress=False, skip_missing=False) -> list[dict[str, object]]`
  - `collect_scan_table(...) -> pd.DataFrame` (same parameters)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_astra_scan_api.py`:

```python
from postpro.api.astra import collect_scan_rows, collect_scan_table


def test_collect_scan_table_returns_one_row_per_case(tmp_path: Path) -> None:
    _write_astra_scan_dir(tmp_path)
    df = collect_scan_table(tmp_path)

    assert len(df) == 2
    assert df["case_id"].tolist() == ["0", "1"]
    assert df["param_a"].tolist() == [10, 20]
    for column in ("n_total", "nemit_x", "sig_E_rel", "I_peak_smooth"):
        assert column in df.columns
    assert df["n_total"].tolist() == [201, 201]
    assert (df["nemit_x"] > 0.0).all()


def test_collect_scan_rows_fields_subset(tmp_path: Path) -> None:
    _write_astra_scan_dir(tmp_path, n_cases=1)
    rows = collect_scan_rows(tmp_path, fields=["nemit_x", "sig_z"], include_params=False)
    assert len(rows) == 1
    assert set(rows[0].keys()) == {"case_id", "nemit_x", "sig_z"}


def test_collect_scan_rows_explicit_registry_wins_over_fields(tmp_path: Path) -> None:
    _write_astra_scan_dir(tmp_path, n_cases=1)
    registry = build_diagnostics_metric_registry(fields=["n_total"])
    rows = collect_scan_rows(
        tmp_path, registry=registry, fields=["nemit_x"], include_params=False
    )
    assert set(rows[0].keys()) == {"case_id", "n_total"}


def test_collect_scan_rows_parallel_matches_serial(tmp_path: Path) -> None:
    _write_astra_scan_dir(tmp_path, n_cases=4)
    serial = collect_scan_rows(tmp_path, fields=["n_total", "nemit_x"])
    parallel = collect_scan_rows(tmp_path, fields=["n_total", "nemit_x"], max_workers=2)
    assert parallel == serial


def test_collect_scan_rows_missing_dump_raises_or_skips(tmp_path: Path) -> None:
    _write_astra_scan_dir(tmp_path, n_cases=3)
    (tmp_path / "case001" / "ast.dist").unlink()

    with pytest.raises(FileNotFoundError):
        collect_scan_rows(tmp_path, fields=["n_total"])

    rows = collect_scan_rows(tmp_path, fields=["n_total"], skip_missing=True)
    assert [row["case_id"] for row in rows] == ["0", "2"]


def test_collect_scan_table_supports_custom_result_relpath(tmp_path: Path) -> None:
    lines = ["case_id,directory,param_a", "1,case001,42"]
    _write_astra_dump(tmp_path / "case001" / "outputs" / "final.dist")
    (tmp_path / "cases.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    df = collect_scan_table(tmp_path, result_relpath="outputs/final.dist")
    assert df["case_id"].tolist() == ["1"]
    assert df["n_total"].tolist() == [201]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_astra_scan_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'postpro.api.astra'`

- [ ] **Step 3: Create `src/postpro/api/astra.py`**

```python
"""User-facing ASTRA scan-collection APIs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from postpro.api._collect import evaluate_study_rows
from postpro.backends.astra.metric_registry import build_diagnostics_metric_registry
from postpro.backends.astra.scan import DEFAULT_RESULT_RELPATH, load_study
from postpro.core.metric import MetricRegistry


def collect_scan_rows(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = DEFAULT_RESULT_RELPATH,
    registry: MetricRegistry | None = None,
    metric_names: list[str] | tuple[str, ...] | None = None,
    fields: list[str] | tuple[str, ...] | None = None,
    n_slices_energy: int = 50,
    include_params: bool = True,
    eager: bool = False,
    max_workers: int | None = None,
    progress: bool = False,
    skip_missing: bool = False,
) -> list[dict[str, object]]:
    study = load_study(
        cluster_dir,
        result_relpath=result_relpath,
        n_slices_energy=n_slices_energy,
        eager=eager,
    )
    metric_registry = (
        registry
        if registry is not None
        else build_diagnostics_metric_registry(fields=fields)
    )
    names = tuple(metric_names) if metric_names is not None else metric_registry.names()
    return evaluate_study_rows(
        study,
        names,
        metric_registry,
        include_params=include_params,
        max_workers=max_workers,
        progress=progress,
        skip_missing=skip_missing,
    )


def collect_scan_table(
    cluster_dir: str | Path,
    *,
    result_relpath: str | Path = DEFAULT_RESULT_RELPATH,
    registry: MetricRegistry | None = None,
    metric_names: list[str] | tuple[str, ...] | None = None,
    fields: list[str] | tuple[str, ...] | None = None,
    n_slices_energy: int = 50,
    include_params: bool = True,
    eager: bool = False,
    max_workers: int | None = None,
    progress: bool = False,
    skip_missing: bool = False,
) -> pd.DataFrame:
    rows = collect_scan_rows(
        cluster_dir,
        result_relpath=result_relpath,
        registry=registry,
        metric_names=metric_names,
        fields=fields,
        n_slices_energy=n_slices_energy,
        include_params=include_params,
        eager=eager,
        max_workers=max_workers,
        progress=progress,
        skip_missing=skip_missing,
    )
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_astra_scan_api.py -v && python -m pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/postpro/api/astra.py tests/test_astra_scan_api.py
git commit -m "Add ASTRA collect_scan_rows and collect_scan_table APIs

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: Documentation update

**Files:**
- Modify: `README.md`
- Modify: `docs/roadmap.md`

**Interfaces:**
- Consumes: the public API from Task 7 (documentation only).
- Produces: nothing consumed by other tasks.

- [ ] **Step 1: Update `README.md`**

1. In the "Current status" list at the top, add a bullet:

```markdown
- an ASTRA backend collects phase-space dump diagnostics into scan tables
  (requires the optional `partdist` package)
```

2. After the "Optional `paramstudy`" section, add:

```markdown
## Optional `partdist`

The ASTRA backend reads phase-space dump files and computes beam diagnostics
through the `partdist` package. `postpro` does not declare it as a hard
dependency, because it lives in a separate repository during this refactor.
Genesis functionality works without it.
```

3. After the Genesis scan API examples, add:

```markdown
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

Column names are the `BeamDiagnosticsResult` field names from `partdist`
(`nemit_x`, `sig_E_rel`, `I_peak_smooth`, ...). ASTRA functions are not
re-exported at the top level; import them from `postpro.api.astra`.
```

- [ ] **Step 2: Update `docs/roadmap.md`**

In the "已完成" milestone list, append a new numbered item after item 10:

```markdown
11. ASTRA backend 起步
- 已实现 `postpro.backends.astra`（模型 / adapter / metric registry / scan）
- 已实现 `postpro.api.astra.collect_scan_rows / collect_scan_table`
- 统计量来自 `partdist.compute_beam_diagnostics`（软依赖）
- scan manifest 与并行评估逻辑已提升为 genesis / astra 共享层
```

- [ ] **Step 3: Run the full suite one last time**

Run: `python -m pytest -q`
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/roadmap.md
git commit -m "Document ASTRA scan API and partdist soft dependency

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
