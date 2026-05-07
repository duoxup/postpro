from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "paramstudy" / "src"))

from postpro.backends.genesis import (
    MainResults,
    build_default_main_results_meta,
    default_main_results_meta_spec,
)


def test_default_meta_spec_covers_all_main_results_keys() -> None:
    spec = default_main_results_meta_spec()
    expected = set(MainResults.mapping_v4) | set(MainResults.derived_field_names)

    assert set(spec) == expected
    assert spec["zenergy"]["unit"] == "J"
    assert spec["zsigmat_fld"]["preferred_unit"] == "fs"
    assert spec["wavelength_spectra_wl"]["preferred_unit"] == "nm"
    assert spec["bunching"]["unit"] is None


def test_build_default_main_results_meta_supports_overrides() -> None:
    registry = build_default_main_results_meta(
        extra_spec={
            "zenergy": {"label": "Pulse energy custom", "preferred_unit": "uJ"},
            "custom_metric": {"label": "Custom metric", "unit": "W"},
        }
    )

    zenergy = registry.get("zenergy")
    custom = registry.get("custom_metric")
    bunching = registry.get("bunching")

    assert zenergy.label == "Pulse energy custom"
    assert zenergy.unit is not None and zenergy.unit.render() == "J"
    assert zenergy.preferred_unit is not None and zenergy.preferred_unit.render() == "uJ"

    assert custom.label == "Custom metric"
    assert custom.unit is not None and custom.unit.render() == "W"

    assert bunching.label == "Bunching factor"
    assert bunching.unit is None
