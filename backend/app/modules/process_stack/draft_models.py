"""Typed contracts and the supported registry for the Jarvis-owned process draft (spec 155).

The registry is the single source of what a draft may contain. Every entry names the
DWSIM type, its ports, and each parameter's SI storage key, DWSIM property and quantity
kind, so the draft schema, the inspector forms, the compiler and the read-back all derive
from one table. Anything absent here is unsupported and refused, never approximated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

COMPILER_VERSION = "155.1"
MAX_OBJECTS = 60
ID_PATTERN = r"^[a-z][a-z0-9_-]{0,39}$"
TAG_PATTERN = r"^[A-Za-z][A-Za-z0-9_-]{0,31}$"

COMPOUNDS: tuple[str, ...] = (
    "Water", "Methanol", "Ethanol", "Acetone", "Benzene", "Toluene", "Nitrogen", "Oxygen",
    "Carbon dioxide", "Methane", "Ethane", "Propane", "N-butane", "N-hexane", "Hydrogen",
    "Argon", "Ammonia", "Acetic acid", "Isopropanol",
)
PROPERTY_PACKAGES: tuple[str, ...] = (
    "NRTL", "Peng-Robinson (PR)", "Soave-Redlich-Kwong (SRK)", "Raoult's Law", "UNIQUAC",
    "Steam Tables (IAPWS-IF97)",
)

QuantityKind = Literal["temperature", "pressure", "pressure_difference", "mass_flow", "percent"]

# SI storage unit and the display units offered by inspectors, per quantity kind.
QUANTITY_UNITS: dict[str, tuple[str, tuple[str, ...]]] = {
    "temperature": ("K", ("degC", "K")),
    "pressure": ("Pa", ("bar", "kPa", "Pa", "psi")),
    "pressure_difference": ("Pa", ("bar", "kPa", "Pa", "psi")),
    "mass_flow": ("kg/s", ("kg/h", "kg/s", "t/h")),
    "percent": ("percent", ("percent",)),
}


@dataclass(frozen=True)
class ParamSpec:
    key: str
    label: str
    kind: QuantityKind
    dwsim_property: str
    modes: tuple[str, ...]
    default: float | None = None
    minimum_si: float | None = None
    maximum_si: float | None = None


@dataclass(frozen=True)
class UnitSpec:
    type: str
    label: str
    dwsim_type: str
    # Simulation class suffix in the saved native case (Mixer saves as NodeIn/Mixer).
    native_types: tuple[str, ...]
    inlets: tuple[str, ...]
    outlets: tuple[str, ...]
    required_inlets: int
    modes: dict[str, str] = field(default_factory=dict)
    params: tuple[ParamSpec, ...] = ()

    @property
    def default_mode(self) -> str | None:
        return next(iter(self.modes), None)

    def params_for(self, mode: str | None) -> tuple[ParamSpec, ...]:
        return tuple(item for item in self.params if mode in item.modes)


def _heat(label: str, dwsim_type: str) -> UnitSpec:
    return UnitSpec(
        type=dwsim_type, label=label, dwsim_type=dwsim_type, native_types=(dwsim_type,),
        inlets=("inlet",), outlets=("outlet",), required_inlets=1,
        modes={"outlet_temperature": "OutletTemperature"},
        params=(
            ParamSpec("outlet_temperature", "Outlet temperature", "temperature", "OutletTemperature",
                      ("outlet_temperature",), minimum_si=1.0),
            ParamSpec("pressure_drop", "Pressure drop", "pressure_difference", "DeltaP",
                      ("outlet_temperature",), default=0.0, minimum_si=0.0),
        ),
    )


UNIT_REGISTRY: dict[str, UnitSpec] = {
    "Heater": _heat("Heater", "Heater"),
    "Cooler": _heat("Cooler", "Cooler"),
    "Pump": UnitSpec(
        type="Pump", label="Pump", dwsim_type="Pump", native_types=("Pump",),
        inlets=("inlet",), outlets=("outlet",), required_inlets=1,
        modes={"outlet_pressure": "OutletPressure", "pressure_increase": "Delta_P"},
        params=(
            ParamSpec("outlet_pressure", "Outlet pressure", "pressure", "Pout", ("outlet_pressure",),
                      minimum_si=1.0),
            ParamSpec("pressure_increase", "Pressure increase", "pressure_difference", "DeltaP",
                      ("pressure_increase",), minimum_si=0.0),
            ParamSpec("efficiency", "Efficiency", "percent", "Efficiency",
                      ("outlet_pressure", "pressure_increase"), default=75.0, minimum_si=1.0, maximum_si=100.0),
        ),
    ),
    "Valve": UnitSpec(
        type="Valve", label="Valve", dwsim_type="Valve", native_types=("Valve",),
        inlets=("inlet",), outlets=("outlet",), required_inlets=1,
        modes={"outlet_pressure": "OutletPressure", "pressure_drop": "DeltaP"},
        params=(
            ParamSpec("outlet_pressure", "Outlet pressure", "pressure", "OutletPressure", ("outlet_pressure",),
                      minimum_si=1.0),
            ParamSpec("pressure_drop", "Pressure drop", "pressure_difference", "DeltaP", ("pressure_drop",),
                      minimum_si=0.0),
        ),
    ),
    "Mixer": UnitSpec(
        type="Mixer", label="Mixer", dwsim_type="Mixer", native_types=("Mixer", "NodeIn"),
        inlets=("inlet 1", "inlet 2", "inlet 3"), outlets=("outlet",), required_inlets=2,
    ),
    "Flash": UnitSpec(
        type="Flash", label="Flash vessel", dwsim_type="Vessel", native_types=("Vessel",),
        inlets=("feed",), outlets=("vapor", "liquid"), required_inlets=1,
    ),
}

UNSUPPORTED_TYPES: dict[str, str] = {
    "EnergyStream": "Units compute their own duty in 155; energy streams are not yet materialized.",
    "Splitter": "Split specifications are not yet in the supported registry.",
    "HeatExchanger": "Two-side exchanger specifications are not yet in the supported registry.",
    "DistillationColumn": "Columns are outside the 155 supported subset.",
    "Reactor": "Reactors are outside the 155 supported subset.",
    "Recycle": "Recycle loops are outside the 155 supported subset.",
}

# Feed-stream specification keys: SI storage and DWSIM MCP argument names.
STREAM_SPECS: dict[str, tuple[QuantityKind, str, str]] = {
    "temperature": ("temperature", "temperature_K", "Temperature"),
    "pressure": ("pressure", "pressure_Pa", "Pressure"),
    "mass_flow": ("mass_flow", "mass_flow_kg_s", "Mass flow"),
}


class DraftQuantity(BaseModel):
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=16)


class Endpoint(BaseModel):
    unit: str = Field(pattern=ID_PATTERN)
    port: int = Field(ge=0, le=7)


class _Op(BaseModel):
    model_config = {"extra": "forbid"}


class AddUnit(_Op):
    op: Literal["add_unit"]
    id: str | None = Field(default=None, pattern=ID_PATTERN)
    type: str
    tag: str = Field(pattern=TAG_PATTERN)
    x: int = Field(ge=-5000, le=5000)
    y: int = Field(ge=-5000, le=5000)


class AddStream(_Op):
    op: Literal["add_stream"]
    id: str | None = Field(default=None, pattern=ID_PATTERN)
    tag: str = Field(pattern=TAG_PATTERN)
    x: int = Field(ge=-5000, le=5000)
    y: int = Field(ge=-5000, le=5000)


class Delete(_Op):
    op: Literal["delete"]
    id: str = Field(pattern=ID_PATTERN)


class Move(_Op):
    op: Literal["move"]
    id: str = Field(pattern=ID_PATTERN)
    x: int = Field(ge=-5000, le=5000)
    y: int = Field(ge=-5000, le=5000)


class Rename(_Op):
    op: Literal["rename"]
    id: str = Field(pattern=ID_PATTERN)
    tag: str = Field(pattern=TAG_PATTERN)


class Connect(_Op):
    op: Literal["connect"]
    stream: str = Field(pattern=ID_PATTERN)
    end: Literal["source", "target"]
    unit: str = Field(pattern=ID_PATTERN)
    port: int = Field(ge=0, le=7)


class Disconnect(_Op):
    op: Literal["disconnect"]
    stream: str = Field(pattern=ID_PATTERN)
    end: Literal["source", "target"]


class SetStreamSpec(_Op):
    op: Literal["set_stream_spec"]
    stream: str = Field(pattern=ID_PATTERN)
    temperature: DraftQuantity | None = None
    pressure: DraftQuantity | None = None
    mass_flow: DraftQuantity | None = None
    composition: dict[str, float] | None = None
    clear: list[Literal["temperature", "pressure", "mass_flow", "composition"]] = Field(default_factory=list)

    @field_validator("composition")
    @classmethod
    def _fractions(cls, value: dict[str, float] | None) -> dict[str, float] | None:
        if value is not None and any(not 0.0 <= item <= 1.0 for item in value.values()):
            raise ValueError("composition mass fractions must be between 0 and 1")
        return value


class SetUnitParams(_Op):
    op: Literal["set_unit_params"]
    unit: str = Field(pattern=ID_PATTERN)
    mode: str | None = None
    values: dict[str, DraftQuantity] = Field(default_factory=dict)


class SetThermo(_Op):
    op: Literal["set_thermo"]
    compounds: list[str] | None = Field(default=None, max_length=12)
    property_package: str | None = None


DraftOp = Annotated[
    AddUnit | AddStream | Delete | Move | Rename | Connect | Disconnect | SetStreamSpec | SetUnitParams | SetThermo,
    Field(discriminator="op"),
]


class PatchRequest(BaseModel):
    expected_revision: str
    ops: list[DraftOp] = Field(min_length=1, max_length=64)


class CreateDraft(BaseModel):
    name: str = Field(default="Process draft", min_length=1, max_length=80)


class RestoreRequest(BaseModel):
    expected_revision: str
    source_revision: str


class ProposedChange(BaseModel):
    target: str = Field(min_length=1, max_length=32)
    property: str = Field(min_length=1, max_length=40)
    proposed: DraftQuantity | str | dict[str, float]


class ProposalRequest(BaseModel):
    base_revision: str
    changes: list[ProposedChange] = Field(min_length=1, max_length=12)
    rationale: str = Field(default="", max_length=600)
    source: str = Field(default="operator", max_length=80)


class ProposalDecision(BaseModel):
    accepted_changes: list[int] | None = None


class RunRequest(BaseModel):
    pass
