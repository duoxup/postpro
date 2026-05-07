"""Solver-agnostic core abstractions."""

from postpro.core.metric import Metric, MetricRegistry, compute_many
from postpro.core.result import MappingResultSet, ResultSet
from postpro.core.study import CaseRecord, Study

__all__ = [
    "CaseRecord",
    "MappingResultSet",
    "Metric",
    "MetricRegistry",
    "ResultSet",
    "Study",
    "compute_many",
]
