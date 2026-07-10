from __future__ import annotations

from collections.abc import Sequence
from math import isfinite
from typing import TypeAlias

from pydantic import BaseModel, Field

NumericValue: TypeAlias = float | int | Sequence["NumericValue"]


class NumericFailure(BaseModel):
    path: str
    code: str
    actual: float | None = None


class NumericCheckResult(BaseModel):
    passed: bool
    rtol: float
    atol: float
    max_absolute_error: float | None = None
    max_relative_error: float | None = None
    failures: list[NumericFailure] = Field(default_factory=list)


def _is_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(
        value, str | bytes | bytearray
    )


def _walk_pairs(actual: NumericValue, expected: NumericValue, path: str = "$"):
    if _is_sequence(actual) or _is_sequence(expected):
        if not (_is_sequence(actual) and _is_sequence(expected)):
            yield path, None, None, "shape_mismatch"
            return
        actual_sequence = list(actual)
        expected_sequence = list(expected)
        if len(actual_sequence) != len(expected_sequence):
            yield path, None, None, "shape_mismatch"
            return
        for index, (actual_item, expected_item) in enumerate(
            zip(actual_sequence, expected_sequence, strict=True)
        ):
            yield from _walk_pairs(actual_item, expected_item, f"{path}[{index}]")
        return
    try:
        actual_float = float(actual)
        expected_float = float(expected)
    except (TypeError, ValueError):
        yield path, None, None, "not_numeric"
        return
    yield path, actual_float, expected_float, None


def check_numeric(
    actual: NumericValue,
    expected: NumericValue,
    *,
    rtol: float = 1e-6,
    atol: float = 0.0,
) -> NumericCheckResult:
    if not isfinite(rtol) or not isfinite(atol) or rtol < 0 or atol < 0:
        return NumericCheckResult(
            passed=False,
            rtol=rtol,
            atol=atol,
            failures=[NumericFailure(path="$", code="invalid_tolerance")],
        )

    failures: list[NumericFailure] = []
    absolute_errors: list[float] = []
    relative_errors: list[float] = []
    for path, actual_value, expected_value, error_code in _walk_pairs(actual, expected):
        if error_code is not None:
            failures.append(NumericFailure(path=path, code=error_code))
            continue
        assert actual_value is not None
        assert expected_value is not None
        if not isfinite(actual_value) or not isfinite(expected_value):
            failures.append(
                NumericFailure(path=path, code="non_finite", actual=actual_value)
            )
            continue
        absolute_error = abs(actual_value - expected_value)
        absolute_errors.append(absolute_error)
        if expected_value == 0:
            relative_error = 0.0 if absolute_error == 0 else float("inf")
        else:
            relative_error = absolute_error / abs(expected_value)
        relative_errors.append(relative_error)
        if absolute_error > atol + rtol * abs(expected_value):
            failures.append(
                NumericFailure(path=path, code="outside_tolerance", actual=actual_value)
            )

    return NumericCheckResult(
        passed=not failures,
        rtol=rtol,
        atol=atol,
        max_absolute_error=max(absolute_errors) if absolute_errors else None,
        max_relative_error=max(relative_errors) if relative_errors else None,
        failures=failures,
    )
