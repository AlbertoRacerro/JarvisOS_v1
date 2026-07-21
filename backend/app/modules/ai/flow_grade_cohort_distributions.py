from __future__ import annotations

import math


def numeric_distribution(values: list[int]) -> dict[str, int | None]:
    if not values:
        return {
            "count": 0,
            "minimum": None,
            "p50": None,
            "p95": None,
            "maximum": None,
        }
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "minimum": ordered[0],
        "p50": _nearest_rank(ordered, 0.50),
        "p95": _nearest_rank(ordered, 0.95),
        "maximum": ordered[-1],
    }


def _nearest_rank(ordered: list[int], percentile: float) -> int:
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]
