from __future__ import annotations

import math

from app.modules.engineering_corpus.checkers.conservation import (
    check_element_conservation,
)
from app.modules.engineering_corpus.checkers.numeric import check_numeric
from app.modules.engineering_corpus.checkers.units import convert_unit


def test_unit_checker_performs_explicit_engineering_conversions() -> None:
    concentration = convert_unit(0.1, "mol/L", "mol/m^3")
    diffusivity = convert_unit(1e-5, "cm^2/s", "m^2/s")
    pressure = convert_unit(1.0, "atm", "Pa")
    temperature = convert_unit(25.0, "degC", "K")

    assert concentration.compatible and math.isclose(
        concentration.converted_value or 0.0, 100.0
    )
    assert diffusivity.compatible and math.isclose(
        diffusivity.converted_value or 0.0, 1e-9
    )
    assert pressure.compatible and math.isclose(
        pressure.converted_value or 0.0, 101325.0
    )
    assert temperature.compatible and math.isclose(
        temperature.converted_value or 0.0, 298.15
    )


def test_unit_checker_rejects_unknown_incompatible_and_offset_composite_units() -> None:
    incompatible = convert_unit(1.0, "mol/L", "kg/m^3")
    unknown = convert_unit(1.0, "furlong", "m")
    offset_composite = convert_unit(1.0, "degC/s", "K/s")

    assert (
        not incompatible.compatible
        and incompatible.error_code == "incompatible_dimensions"
    )
    assert not unknown.compatible and unknown.error_code == "unknown_unit"
    assert (
        not offset_composite.compatible
        and offset_composite.error_code == "offset_unit_in_composite"
    )


def test_conservation_checker_passes_balanced_reaction_and_rejects_unbalanced_reaction() -> None:
    composition = {
        "CH4": {"C": 1, "H": 4},
        "H2O": {"H": 2, "O": 1},
        "CO": {"C": 1, "O": 1},
        "H2": {"H": 2},
    }
    balanced = check_element_conservation(
        {"CH4": -1, "H2O": -1, "CO": 1, "H2": 3},
        composition,
    )
    unbalanced = check_element_conservation(
        {"CH4": -1, "H2O": -1, "CO": 1, "H2": 2},
        composition,
    )

    assert balanced.passed and balanced.residuals == {"C": 0, "H": 0, "O": 0}
    assert not unbalanced.passed and unbalanced.residuals["H"] == -2


def test_conservation_checker_fails_closed_on_missing_species_metadata() -> None:
    result = check_element_conservation({"A": -1, "B": 1}, {"A": {"C": 1}})

    assert not result.passed
    assert result.error_code == "missing_species_composition"


def test_numeric_checker_handles_vectors_shape_and_non_finite_values() -> None:
    good = check_numeric([1.0, 2.0], [1.0, 2.000001], rtol=1e-5)
    bad_shape = check_numeric([1.0], [1.0, 2.0])
    bad_non_finite = check_numeric(float("nan"), 1.0)

    assert good.passed
    assert not bad_shape.passed and bad_shape.failures[0].code == "shape_mismatch"
    assert not bad_non_finite.passed and bad_non_finite.failures[0].code == "non_finite"
