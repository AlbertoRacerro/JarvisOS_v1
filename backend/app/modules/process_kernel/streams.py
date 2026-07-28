from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isclose, isfinite
from types import MappingProxyType

from .components import COMPONENT_CATALOG
from .errors import ProcessKernelError

_COMPOSITION_TOLERANCE = 1e-12
_FLOW_ABS_TOLERANCE = 1e-15
_FLOW_REL_TOLERANCE = 1e-12


@dataclass(frozen=True, slots=True)
class MaterialStream:
    id: str
    composition: Mapping[str, float] | None = None
    density_kg_m3: float | None = None
    dynamic_viscosity_Pa_s: float | None = None
    mass_flow_kg_s: float | None = None
    volumetric_flow_m3_s: float | None = None
    temperature_K: float | None = None
    pressure_Pa: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ProcessKernelError("stream_identity_invalid", "Stream id must be a non-empty string.")
        if self.composition is not None:
            composition = _validate_composition(self.composition)
            object.__setattr__(self, "composition", MappingProxyType(composition))
        _positive_optional(self.density_kg_m3, "stream_density_invalid")
        _positive_optional(self.dynamic_viscosity_Pa_s, "stream_viscosity_invalid")
        _positive_optional(self.temperature_K, "stream_temperature_invalid")
        _positive_optional(self.pressure_Pa, "stream_pressure_invalid")
        _nonnegative_optional(self.mass_flow_kg_s, "stream_mass_flow_invalid")
        _nonnegative_optional(self.volumetric_flow_m3_s, "stream_volumetric_flow_invalid")

        density = self.density_kg_m3
        mass_flow = self.mass_flow_kg_s
        volumetric_flow = self.volumetric_flow_m3_s
        if density is not None and mass_flow is None and volumetric_flow is not None:
            object.__setattr__(self, "mass_flow_kg_s", density * volumetric_flow)
        elif density is not None and volumetric_flow is None and mass_flow is not None:
            object.__setattr__(self, "volumetric_flow_m3_s", mass_flow / density)
        elif density is not None and mass_flow is not None and volumetric_flow is not None:
            expected = density * volumetric_flow
            if not isclose(mass_flow, expected, rel_tol=_FLOW_REL_TOLERANCE, abs_tol=_FLOW_ABS_TOLERANCE):
                raise ProcessKernelError(
                    "stream_flow_inconsistent",
                    "Mass and volumetric flow are inconsistent with density.",
                )

    def with_flow(self, *, volumetric_flow_m3_s: float) -> MaterialStream:
        if self.density_kg_m3 is None:
            raise ProcessKernelError("stream_density_required", "Density is required to derive mass flow.")
        return MaterialStream(
            id=self.id,
            composition=self.composition,
            density_kg_m3=self.density_kg_m3,
            dynamic_viscosity_Pa_s=self.dynamic_viscosity_Pa_s,
            volumetric_flow_m3_s=volumetric_flow_m3_s,
            temperature_K=self.temperature_K,
            pressure_Pa=self.pressure_Pa,
        )

    def require(self, *field_names: str) -> None:
        for field_name in field_names:
            if not hasattr(self, field_name):
                raise ProcessKernelError("stream_requirement_unknown", f"Unknown stream field: {field_name}.")
            if getattr(self, field_name) is None:
                raise ProcessKernelError(
                    "stream_requirement_missing",
                    f"Stream field is required: {field_name}.",
                    context={"field": field_name},
                )


def _validate_composition(values: Mapping[str, float]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for component_id, raw_fraction in values.items():
        if component_id not in COMPONENT_CATALOG:
            raise ProcessKernelError("stream_component_unknown", "Composition references an unknown component.")
        fraction = float(raw_fraction)
        if not isfinite(fraction) or fraction < 0:
            raise ProcessKernelError("stream_composition_invalid", "Composition fractions must be finite and nonnegative.")
        normalized[component_id] = fraction
    if abs(sum(normalized.values()) - 1.0) > _COMPOSITION_TOLERANCE:
        raise ProcessKernelError("stream_composition_invalid", "Composition fractions must sum to one.")
    return dict(sorted(normalized.items()))


def _positive_optional(value: float | None, code: str) -> None:
    if value is not None and (not isfinite(value) or value <= 0):
        raise ProcessKernelError(code, "Stream property must be positive and finite.")


def _nonnegative_optional(value: float | None, code: str) -> None:
    if value is not None and (not isfinite(value) or value < 0):
        raise ProcessKernelError(code, "Stream flow must be nonnegative and finite.")
