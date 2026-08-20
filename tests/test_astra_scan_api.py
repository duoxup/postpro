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
from postpro.api.astra import collect_scan_rows, collect_scan_table
from postpro.backends.astra.metric_registry import build_diagnostics_metric_registry
from postpro.backends.astra.scan import load_case_records, load_study
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
