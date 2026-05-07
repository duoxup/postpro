"""Genesis-specific metrics built on top of the core metric abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from postpro.backends.genesis.adapters import require_main_results
from postpro.backends.genesis.stats import (
    statistics_at_max,
    statistics_at_z,
)
from postpro.core.metric import MetricRegistry
from postpro.core.result import ResultSet

AtZQuantity = Literal["peak_frequency", "sigma_t", "fwhm", "energy"]
AtMaxQuantity = Literal["peak_frequency", "sigma_t", "fwhm", "z"]


def build_stat_metric_registry(
    *,
    zs: list[float] | None = None,
    ratios2max: list[float] | None = None,
) -> MetricRegistry:
    metrics = [MaxEnergyMetric(), MaxPowerMetric(), MaxPeakPowerMetric()]

    for z in zs or []:
        metrics.extend(
            [
                AtZMetric(z=z, quantity="peak_frequency"),
                AtZMetric(z=z, quantity="sigma_t"),
                AtZMetric(z=z, quantity="fwhm"),
                AtZMetric(z=z, quantity="energy"),
            ]
        )

    for ratio in ratios2max or []:
        metrics.extend(
            [
                AtMaxMetric(ratio=ratio, quantity="peak_frequency"),
                AtMaxMetric(ratio=ratio, quantity="sigma_t"),
                AtMaxMetric(ratio=ratio, quantity="fwhm"),
                AtMaxMetric(ratio=ratio, quantity="z"),
            ]
        )

    return MetricRegistry.from_metrics(metrics)


@dataclass(frozen=True, slots=True)
class MaxEnergyMetric:
    name: str = "max_energy"

    def compute(self, result: ResultSet) -> Any:
        gmr = require_main_results(result)
        return float(np.max(gmr.zenergy))


@dataclass(frozen=True, slots=True)
class MaxPowerMetric:
    name: str = "max_power"

    def compute(self, result: ResultSet) -> Any:
        gmr = require_main_results(result)
        return float(np.max(gmr.zpower))


@dataclass(frozen=True, slots=True)
class MaxPeakPowerMetric:
    name: str = "max_ppower"

    def compute(self, result: ResultSet) -> Any:
        gmr = require_main_results(result)
        return float(np.max(np.max(gmr.power, axis=1)))


@dataclass(frozen=True, slots=True)
class AtZMetric:
    z: float
    quantity: AtZQuantity

    @property
    def name(self) -> str:
        return f"{self.quantity}@{self.z:.2f}m"

    def compute(self, result: ResultSet) -> Any:
        gmr = require_main_results(result)
        return statistics_at_z(gmr, self.z)[self.name]


@dataclass(frozen=True, slots=True)
class AtMaxMetric:
    ratio: float
    quantity: AtMaxQuantity

    @property
    def name(self) -> str:
        if self.quantity == "z":
            return f"z@{self.ratio * 100:.0f}%_max_energy"
        return f"{self.quantity}@{self.ratio * 100:.0f}%_max_energy"

    def compute(self, result: ResultSet) -> Any:
        gmr = require_main_results(result)
        return statistics_at_max(gmr, self.ratio)[self.name]
