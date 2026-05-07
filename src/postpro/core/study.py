"""Study-level abstractions over collections of cases."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from postpro.core.metric import MetricRegistry, compute_many
from postpro.core.result import ResultSet

ResultLoader = Callable[["CaseRecord"], ResultSet]


@dataclass(frozen=True, slots=True)
class CaseRecord:
    """One case in a parameter study."""

    case_id: str
    params: dict[str, Any] = field(default_factory=dict)
    artifact_path: Path | None = None
    result: ResultSet | None = None
    result_loader: ResultLoader | None = None

    def with_result(self, result: ResultSet) -> "CaseRecord":
        return CaseRecord(
            case_id=self.case_id,
            params=dict(self.params),
            artifact_path=self.artifact_path,
            result=result,
            result_loader=self.result_loader,
        )

    def load_result(self, loader: ResultLoader | None = None) -> ResultSet:
        if self.result is not None:
            return self.result
        result_loader = loader or self.result_loader
        if result_loader is None:
            raise ValueError(f"Case {self.case_id!r} does not have a loaded result or result loader.")
        return result_loader(self)


@dataclass(slots=True)
class Study:
    """A collection of parameter-study cases."""

    cases: list[CaseRecord]

    def case_ids(self) -> tuple[str, ...]:
        return tuple(case.case_id for case in self.cases)

    def iter_results(
        self,
        loader: ResultLoader | None = None,
    ) -> Iterable[tuple[CaseRecord, ResultSet]]:
        for case in self.cases:
            try:
                yield case, case.load_result(loader)
            except ValueError:
                continue

    def materialize(self, loader: ResultLoader | None = None) -> "Study":
        return Study(cases=[case.with_result(case.load_result(loader)) for case in self.cases])

    def evaluate(
        self,
        metrics: Iterable[str],
        registry: MetricRegistry,
        *,
        include_params: bool = True,
        loader: ResultLoader | None = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for case, result in self.iter_results(loader):
            row: dict[str, Any] = {"case_id": case.case_id}
            if include_params:
                row.update(case.params)
            row.update(compute_many(result, metrics, registry))
            rows.append(row)
        return rows
