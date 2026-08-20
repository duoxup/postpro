from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

pytest.importorskip("partdist")

from postpro.backends.astra.models import AstraPhaseSpace, diagnostics_field_names
from postpro.backends.astra.adapters import (
    AstraResultAdapter,
    adapt_result,
    load_phase_space_result,
    require_phase_space,
    unwrap_result,
)
from postpro.backends.astra.metric_registry import build_diagnostics_metric_registry
from postpro.core.metric import compute_many


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
