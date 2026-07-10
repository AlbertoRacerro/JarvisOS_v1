from __future__ import annotations

from math import isfinite

from pydantic import BaseModel, Field


class ConservationCheckResult(BaseModel):
    passed: bool
    residuals: dict[str, float] = Field(default_factory=dict)
    tolerance: float
    error_code: str | None = None


def check_element_conservation(
    stoichiometry: dict[str, float],
    composition: dict[str, dict[str, int]],
    *,
    tolerance: float = 1e-12,
) -> ConservationCheckResult:
    if not isfinite(tolerance) or tolerance < 0:
        return ConservationCheckResult(
            passed=False, tolerance=tolerance, error_code="invalid_tolerance"
        )
    if not stoichiometry:
        return ConservationCheckResult(
            passed=False, tolerance=tolerance, error_code="empty_stoichiometry"
        )

    missing_species = set(stoichiometry) - set(composition)
    if missing_species:
        return ConservationCheckResult(
            passed=False, tolerance=tolerance, error_code="missing_species_composition"
        )

    for coefficient in stoichiometry.values():
        if not isfinite(coefficient):
            return ConservationCheckResult(
                passed=False, tolerance=tolerance, error_code="non_finite_coefficient"
            )
    for element_counts in composition.values():
        for count in element_counts.values():
            if not isinstance(count, int) or count < 0:
                return ConservationCheckResult(
                    passed=False,
                    tolerance=tolerance,
                    error_code="invalid_element_count",
                )

    elements = sorted(
        {element for species in stoichiometry for element in composition[species]}
    )
    residuals = {
        element: sum(
            stoichiometry[species] * composition[species].get(element, 0)
            for species in stoichiometry
        )
        for element in elements
    }
    passed = all(abs(residual) <= tolerance for residual in residuals.values())
    return ConservationCheckResult(
        passed=passed, residuals=residuals, tolerance=tolerance
    )
