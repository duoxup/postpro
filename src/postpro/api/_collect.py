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
