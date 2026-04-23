#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from pathlib import Path
from importlib import resources
from typing import Union

import numpy as np
import matplotlib.pyplot as plt

from xtils import get_autoscale

from .core import MainResults
from .vizdfscan import ColumnMetaRegistry

prj_dir = resources.files("postgenesis")
colmr = ColumnMetaRegistry.from_json(os.path.join(prj_dir, "gcmr_2.json"))

_ARB_UNITS = {"a.u.", "au", "a.u", "arb.", "arb", "arb. unit", "arb units"}


def _autoscale(values: np.ndarray, unit: str) -> tuple[float, str]:
    u = (unit or "").strip()
    if not u or u.lower() in _ARB_UNITS:
        return 1.0, ""
    return get_autoscale(np.asarray(values).flatten())


def _auto_label(gmr: MainResults) -> str:
    parts = gmr.file_basename.split(".")
    if len(parts) >= 2:
        return parts[1]
    return gmr.file_basename


def _load_case(x) -> MainResults:
    if isinstance(x, (str, Path)):
        return MainResults(x)
    if isinstance(x, MainResults):
        return x
    raise TypeError(
        f"Expected str, Path, or MainResults, got {type(x).__name__}"
    )


class CaseComparison:
    """Compare multiple MainResults files with overlay plots."""

    def __init__(
        self,
        cases: list,
        labels: list[str] | None = None,
    ) -> None:
        self.cases: list[MainResults] = [_load_case(c) for c in cases]
        if labels is None:
            self.labels: list[str] = [_auto_label(gmr) for gmr in self.cases]
        else:
            if len(labels) != len(self.cases):
                raise ValueError(
                    f"labels length ({len(labels)}) does not match "
                    f"cases length ({len(self.cases)})"
                )
            self.labels = list(labels)
