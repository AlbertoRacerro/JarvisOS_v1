from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Final

from .canonical import canonical_json_bytes, canonical_sha256
from .errors import ProcessKernelError


@dataclass(frozen=True, slots=True)
class Component:
    id: str
    name: str
    phase_hint: str | None = None
    molecular_formula: Mapping[str, float] | None = None
    scientific_molar_mass_kg_per_mol: float | None = None
    scientific_molar_mass_authority: str | None = None
    elemental_mass_fractions: Mapping[str, float] | None = None

    def __post_init__(self) -> None:
        if not self.id or not self.name:
            raise ProcessKernelError("component_identity_invalid", "Component id and name are required.")
        if self.molecular_formula is not None:
            normalized_formula = _finite_nonnegative_mapping(self.molecular_formula, "component_formula_invalid")
            object.__setattr__(self, "molecular_formula", MappingProxyType(normalized_formula))
        if self.elemental_mass_fractions is not None:
            fractions = _finite_nonnegative_mapping(
                self.elemental_mass_fractions,
                "component_mass_fractions_invalid",
            )
            if abs(sum(fractions.values()) - 1.0) > 1e-12:
                raise ProcessKernelError(
                    "component_mass_fractions_invalid",
                    "Elemental mass fractions must sum to one.",
                )
            object.__setattr__(self, "elemental_mass_fractions", MappingProxyType(fractions))
        if self.scientific_molar_mass_kg_per_mol is not None:
            value = self.scientific_molar_mass_kg_per_mol
            if not isfinite(value) or value <= 0 or not self.scientific_molar_mass_authority:
                raise ProcessKernelError(
                    "component_molar_mass_invalid",
                    "Scientific molar mass requires a positive value and pinned authority.",
                )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "phase_hint": self.phase_hint,
            "molecular_formula": dict(self.molecular_formula) if self.molecular_formula is not None else None,
            "scientific_molar_mass_kg_per_mol": self.scientific_molar_mass_kg_per_mol,
            "scientific_molar_mass_authority": self.scientific_molar_mass_authority,
            "elemental_mass_fractions": (
                dict(self.elemental_mass_fractions) if self.elemental_mass_fractions is not None else None
            ),
        }


@dataclass(frozen=True, slots=True)
class ScreeningMassConstants:
    carbon_g_per_mol: float = 12.0
    oxygen_g_per_mol: float = 16.0
    carbon_dioxide_g_per_mol: float = 44.0
    carbon_dioxide_to_carbon_ratio: float = 44.0 / 12.0
    authority: str = "merged 048 rounded screening constants"

    def canonical_payload(self) -> dict[str, object]:
        return {
            "carbon_g_per_mol": self.carbon_g_per_mol,
            "oxygen_g_per_mol": self.oxygen_g_per_mol,
            "carbon_dioxide_g_per_mol": self.carbon_dioxide_g_per_mol,
            "carbon_dioxide_to_carbon_ratio": self.carbon_dioxide_to_carbon_ratio,
            "authority": self.authority,
        }


def _finite_nonnegative_mapping(values: Mapping[str, float], code: str) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for key, raw_value in values.items():
        if not isinstance(key, str) or not key:
            raise ProcessKernelError(code, "Mapping keys must be non-empty strings.")
        value = float(raw_value)
        if not isfinite(value) or value < 0:
            raise ProcessKernelError(code, "Mapping values must be finite and nonnegative.")
        normalized[key] = value
    return dict(sorted(normalized.items()))


SCREENING_MASS_CONSTANTS_V0: Final = ScreeningMassConstants()
COMPONENT_CATALOG: Final = MappingProxyType(
    {
        "water": Component("water", "Water", phase_hint="liquid", molecular_formula={"H": 2.0, "O": 1.0}),
        "carbon_dioxide": Component(
            "carbon_dioxide",
            "Carbon dioxide",
            phase_hint="gas",
            molecular_formula={"C": 1.0, "O": 2.0},
        ),
        "oxygen": Component("oxygen", "Oxygen", phase_hint="gas", molecular_formula={"O": 2.0}),
        "fixture_biomass": Component("fixture_biomass", "Fixture biomass pseudo-component"),
    }
)


def screening_mass_constants_payload() -> dict[str, object]:
    return SCREENING_MASS_CONSTANTS_V0.canonical_payload()


def screening_mass_constants_sha256() -> str:
    return canonical_sha256(screening_mass_constants_payload())


def component_catalog_payload() -> dict[str, object]:
    return {
        "components": [COMPONENT_CATALOG[key].canonical_payload() for key in sorted(COMPONENT_CATALOG)],
        "screening_mass_constants_v0": screening_mass_constants_payload(),
    }


def component_catalog_bytes() -> bytes:
    return canonical_json_bytes(component_catalog_payload())


def component_catalog_sha256() -> str:
    return canonical_sha256(component_catalog_payload())
