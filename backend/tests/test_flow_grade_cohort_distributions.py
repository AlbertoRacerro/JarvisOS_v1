from __future__ import annotations

from app.modules.ai.flow_grade_cohort_distributions import numeric_distribution


def test_empty_numeric_distribution_is_explicit() -> None:
    assert numeric_distribution([]) == {
        "count": 0,
        "minimum": None,
        "p50": None,
        "p95": None,
        "maximum": None,
    }


def test_numeric_distribution_uses_deterministic_nearest_rank() -> None:
    assert numeric_distribution([100, 0, 10, 20, 30, 40, 50, 60, 70, 80]) == {
        "count": 10,
        "minimum": 0,
        "p50": 40,
        "p95": 100,
        "maximum": 100,
    }
