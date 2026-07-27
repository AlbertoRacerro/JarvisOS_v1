from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from .streams import MaterialStream


@dataclass(frozen=True, slots=True)
class MaterialPort:
    name: str
    required_stream_fields: tuple[str, ...] = ()
    composition_required: bool = False


@dataclass(frozen=True, slots=True)
class ScalarPort:
    name: str
    unit: str
    physical_dimension: str
    semantic_basis: str | None = None


@dataclass(frozen=True, slots=True)
class BlockResult:
    material_outputs: Mapping[str, MaterialStream] = field(default_factory=dict)
    scalar_outputs: Mapping[str, float] = field(default_factory=dict)
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "material_outputs", MappingProxyType(dict(self.material_outputs)))
        object.__setattr__(self, "scalar_outputs", MappingProxyType(dict(self.scalar_outputs)))
        object.__setattr__(self, "diagnostics", MappingProxyType(dict(self.diagnostics)))


@runtime_checkable
class UnitOperation(Protocol):
    block_id: str
    material_inlets: Mapping[str, MaterialPort]
    scalar_inlets: Mapping[str, ScalarPort]
    material_outlets: Mapping[str, MaterialPort]
    scalar_outlets: Mapping[str, ScalarPort]
    caller_parameters: tuple[str, ...]
    profile_constants: tuple[str, ...]

    def solve(
        self,
        material_inputs: Mapping[str, MaterialStream],
        scalar_inputs: Mapping[str, float],
        caller_parameter_values: Mapping[str, float],
        profile_constant_values: Mapping[str, float],
    ) -> BlockResult: ...
