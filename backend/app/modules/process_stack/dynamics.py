"""Single time/state owner for ODE models: SUNDIALS CVODE via scikit-sundae (103 role: dynamics).

A dynamic model supplies only ``rhs(t, y) -> dy/dt``; CVODE alone advances time
and accepts state. Callers that need discrete actions (harvest, cleaning)
integrate segment by segment and apply the action between calls, so no second
integrator ever owns the same state. Convergence is solver health, not validity.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal

from app.modules.engineering.evaluator_contracts import NumericalDiagnostics

MAX_STATES: Final = 256
MAX_OUTPUT_TIMES: Final = 100_000

Rhs = Callable[[float, tuple[float, ...]], Sequence[float]]


class OdeInputError(ValueError):
    """The problem definition is invalid before any integration is attempted."""


@dataclass(frozen=True, slots=True)
class OdeSolution:
    times: tuple[float, ...]
    states: tuple[tuple[float, ...], ...]
    success: bool
    message: str
    diagnostics: NumericalDiagnostics


def _finite_vector(values: Sequence[float], label: str) -> tuple[float, ...]:
    vector = tuple(float(value) for value in values)
    if not vector or not all(math.isfinite(value) for value in vector):
        raise OdeInputError(f"{label} must be a non-empty finite vector")
    return vector


def integrate_ode(
    rhs: Rhs,
    y0: Sequence[float],
    times: Sequence[float],
    *,
    rtol: float = 1e-6,
    atol: float = 1e-9,
    method: Literal["BDF", "Adams"] = "BDF",
    max_step: float = 0.0,
) -> OdeSolution:
    """Integrate ``dy/dt = rhs(t, y)`` and report states at exactly ``times``.

    Invalid problems raise ``OdeInputError``; solver failures return
    ``success=False`` with the native CVODE message and no states.
    """
    import numpy as np
    from sksundae.cvode import CVODE

    state0 = _finite_vector(y0, "y0")
    grid = _finite_vector(times, "times")
    if len(state0) > MAX_STATES or not 2 <= len(grid) <= MAX_OUTPUT_TIMES:
        raise OdeInputError(f"at most {MAX_STATES} states and 2..{MAX_OUTPUT_TIMES} output times")
    if any(later <= earlier for earlier, later in zip(grid, grid[1:], strict=False)):
        raise OdeInputError("times must be strictly increasing")
    if not (0.0 < rtol < 1.0 and 0.0 < atol and max_step >= 0.0):
        raise OdeInputError("tolerances must be positive (rtol < 1) and max_step non-negative")
    size = len(state0)

    def native_rhs(t: float, y: Any, yp: Any) -> None:
        derivative = rhs(float(t), tuple(float(value) for value in y))
        if len(derivative) != size:
            raise OdeInputError(f"rhs returned {len(derivative)} derivatives for {size} states")
        yp[:] = derivative

    started = time.perf_counter()
    result = CVODE(native_rhs, method=method, rtol=rtol, atol=atol, max_step=max_step).solve(
        np.asarray(grid, dtype=float), np.asarray(state0, dtype=float)
    )
    elapsed = time.perf_counter() - started
    states = tuple(tuple(float(value) for value in row) for row in result.y)
    success = bool(result.success) and len(states) == len(grid) and all(
        math.isfinite(value) for row in states for value in row
    )
    return OdeSolution(
        times=tuple(float(value) for value in result.t) if success else (),
        states=states if success else (),
        success=success,
        message=str(result.message),
        # CVODE reports RHS evaluations, the closest native work counter to "iterations".
        diagnostics=NumericalDiagnostics(converged=success, iterations=int(result.nfev), wall_time_s=elapsed),
    )
