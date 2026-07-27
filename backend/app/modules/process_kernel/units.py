from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from math import isfinite
from types import MappingProxyType
from typing import Final

from pint import DimensionalityError, UndefinedUnitError, UnitRegistry

from .canonical import canonical_json_bytes, canonical_sha256
from .errors import ProcessKernelError

SEMANTIC_UNIT_REGISTRY_VERSION: Final = "process_semantic_units_v1"


@dataclass(frozen=True, slots=True)
class SemanticUnitDefinition:
    token: str
    pint_unit: str
    scale_to_si: float
    physical_dimension: str
    semantic_basis: str


@dataclass(frozen=True, slots=True)
class ResolvedUnit:
    token: str
    pint_unit: str
    physical_dimension: str
    semantic_basis: str | None


_SEMANTIC_DEFINITIONS = (
    SemanticUnitDefinition("gDW", "gram", 0.001, "mass", "dry_biomass"),
    SemanticUnitDefinition("kgDW", "kilogram", 1.0, "mass", "dry_biomass"),
    SemanticUnitDefinition("mgN", "milligram", 0.000001, "mass", "nitrogen"),
    SemanticUnitDefinition("gN", "gram", 0.001, "mass", "nitrogen"),
    SemanticUnitDefinition("mgP", "milligram", 0.000001, "mass", "phosphorus"),
    SemanticUnitDefinition("gP", "gram", 0.001, "mass", "phosphorus"),
    SemanticUnitDefinition("gC", "gram", 0.001, "mass", "carbon"),
    SemanticUnitDefinition("kgC", "kilogram", 1.0, "mass", "carbon"),
    SemanticUnitDefinition("mLCO2", "milliliter", 0.000001, "volume", "carbon_dioxide"),
    SemanticUnitDefinition("LCO2", "liter", 0.001, "volume", "carbon_dioxide"),
    SemanticUnitDefinition("EUR", "EUR", 1.0, "currency", "EUR"),
)
SEMANTIC_UNITS: Final = MappingProxyType({item.token: item for item in _SEMANTIC_DEFINITIONS})

_DIMENSION_REFERENCE_UNITS: Final = MappingProxyType(
    {
        "dimensionless": "dimensionless",
        "mass": "kilogram",
        "length": "meter",
        "area": "meter**2",
        "volume": "meter**3",
        "inverse_length": "1/meter",
        "volumetric_flow": "meter**3/second",
        "time": "second",
        "velocity": "meter/second",
        "acceleration": "meter/second**2",
        "density": "kilogram/meter**3",
        "dynamic_viscosity": "pascal*second",
        "pressure": "pascal",
        "power": "watt",
        "currency": "EUR",
    }
)


@lru_cache(maxsize=1)
def unit_registry() -> UnitRegistry:
    registry = UnitRegistry(autoconvert_offset_to_baseunit=True)
    try:
        registry.Unit("EUR")
    except UndefinedUnitError:
        registry.define("EUR = [currency]")
    return registry


def semantic_registry_payload() -> dict[str, object]:
    return {
        "version": SEMANTIC_UNIT_REGISTRY_VERSION,
        "definitions": [asdict(item) for item in sorted(_SEMANTIC_DEFINITIONS, key=lambda item: item.token)],
    }


def semantic_registry_bytes() -> bytes:
    return canonical_json_bytes(semantic_registry_payload())


def semantic_registry_sha256() -> str:
    return canonical_sha256(semantic_registry_payload())


def resolve_unit(token: str) -> ResolvedUnit:
    if not isinstance(token, str) or not token or token != token.strip():
        raise ProcessKernelError("unit_invalid", "Unit token must be a non-empty trimmed string.")
    semantic = SEMANTIC_UNITS.get(token)
    if semantic is not None:
        return ResolvedUnit(
            token=token,
            pint_unit=semantic.pint_unit,
            physical_dimension=semantic.physical_dimension,
            semantic_basis=semantic.semantic_basis,
        )

    registry = unit_registry()
    try:
        unit = registry.Unit(token)
    except (UndefinedUnitError, ValueError) as exc:
        raise ProcessKernelError("unit_unknown", f"Unknown unit token: {token}.") from exc
    physical_dimension = _physical_dimension_for(unit)
    return ResolvedUnit(
        token=token,
        pint_unit=str(unit),
        physical_dimension=physical_dimension,
        semantic_basis=None,
    )


def normalize_magnitude(
    value: float,
    *,
    source_unit: str,
    target_unit: str,
    physical_dimension: str,
    semantic_basis: str | None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not isfinite(float(value)):
        raise ProcessKernelError("quantity_value_invalid", "Quantity magnitude must be a finite number.")
    source = resolve_unit(source_unit)
    target = resolve_unit(target_unit)
    if source.physical_dimension != physical_dimension or target.physical_dimension != physical_dimension:
        raise ProcessKernelError(
            "quantity_dimension_mismatch",
            "Quantity unit does not match the contract physical dimension.",
        )
    if source.semantic_basis != target.semantic_basis or source.semantic_basis != semantic_basis:
        raise ProcessKernelError(
            "quantity_semantic_basis_mismatch",
            "Quantity semantic basis does not match the contract.",
        )

    number = float(value)
    if source_unit == target_unit:
        return number
    registry = unit_registry()
    try:
        converted = (number * registry.Unit(source.pint_unit)).to(registry.Unit(target.pint_unit))
    except DimensionalityError as exc:
        raise ProcessKernelError(
            "quantity_dimension_mismatch",
            "Quantity cannot be converted to the contract unit.",
        ) from exc
    magnitude = float(converted.magnitude)
    if not isfinite(magnitude):
        raise ProcessKernelError("quantity_value_invalid", "Converted quantity must be finite.")
    return magnitude


def _physical_dimension_for(unit: object) -> str:
    registry = unit_registry()
    dimensionality = registry.get_dimensionality(unit)
    for name, reference in _DIMENSION_REFERENCE_UNITS.items():
        if dimensionality == registry.get_dimensionality(reference):
            return name
    raise ProcessKernelError("unit_dimension_unsupported", "Unit dimension is outside PROCESS-KERNEL-1.")
