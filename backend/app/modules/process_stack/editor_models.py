"""Typed HTTP contracts for the revisioned DWSIM process editor."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RevisionRead(BaseModel):
    seq: int
    case_sha256: str
    revision: str
    parent_revision: str | None = None
    command_kind: str
    created_at: str
    readback: dict[str, object] = Field(default_factory=dict)


class EditorObjectRead(BaseModel):
    native_id: str | None = None
    tag: str | None = None
    type: str | None = None
    category: Literal["unit", "material_stream", "energy_stream", "other"]
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    calculated: bool | None = None
    errors: str = ""
    results: dict[str, object] | None = None


class EditorConnectionRead(BaseModel):
    source_native_id: str
    source_port: int
    target_native_id: str
    target_port: int
    kind: Literal["material", "energy"]


class EditorProjectionRead(BaseModel):
    workspace_id: str
    case_id: str
    revision: str
    case_sha256: str
    dwsim_version: str
    mcp_sha256: str
    availability: Literal["available"] = "available"
    objects: list[EditorObjectRead]
    connections: list[EditorConnectionRead]
    compounds: list[str]
    property_package: str | None = None
    last_solve: dict[str, object] | None = None
    editable_commands: list[str]
    unsupported_commands: dict[str, str]


class EditorCaseRead(BaseModel):
    workspace_id: str
    case_id: str
    revision: str
    case_sha256: str
    dwsim_version: str
    created_at: str


class EditorUnavailableRead(BaseModel):
    code: str
    message: str


class CommandBase(BaseModel):
    kind: str
    expected_revision: str


class EditorQuantity(BaseModel):
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=64)


class CreateUnit(CommandBase):
    kind: Literal["create_unit"]
    unit_type: str
    tag: str
    x: int
    y: int


class CreateMaterialStream(CommandBase):
    kind: Literal["create_material_stream"]
    tag: str
    x: int = 0
    y: int = 0
    temperature: EditorQuantity | None = None
    pressure: EditorQuantity | None = None
    mass_flow: EditorQuantity | None = None
    composition: dict[str, float] | None = None

    @field_validator("composition")
    @classmethod
    def validate_composition(cls, value: dict[str, float] | None) -> dict[str, float] | None:
        if value is None:
            return value
        if not value or any(not name or not 0 <= fraction <= 1 for name, fraction in value.items()):
            raise ValueError("composition must contain nonnegative mass fractions")
        if abs(sum(value.values()) - 1.0) > 1e-8:
            raise ValueError("composition mass fractions must sum to one")
        return value


class CreateEnergyStream(CommandBase):
    kind: Literal["create_energy_stream"]
    tag: str
    x: int = 0
    y: int = 0


class Connect(CommandBase):
    kind: Literal["connect"]
    unit: str
    stream: str
    role: Literal["feed", "product", "energy_feed", "energy_product"]
    port: int = Field(ge=0)


class Move(CommandBase):
    kind: Literal["move"]
    object: str
    x: int
    y: int


class Rename(CommandBase):
    kind: Literal["rename"]
    object: str
    new_tag: str = Field(min_length=1)


class SetStreamConditions(CommandBase):
    kind: Literal["set_stream_conditions"]
    stream: str
    temperature: EditorQuantity | None = None
    pressure: EditorQuantity | None = None
    mass_flow: EditorQuantity | None = None
    molar_flow: EditorQuantity | None = None
    composition: dict[str, float] | None = None

    @field_validator("composition")
    @classmethod
    def validate_composition(cls, value: dict[str, float] | None) -> dict[str, float] | None:
        if value is None:
            return value
        if not value or any(not name or not 0 <= fraction <= 1 for name, fraction in value.items()):
            raise ValueError("composition must contain nonnegative mass fractions")
        if abs(sum(value.values()) - 1.0) > 1e-8:
            raise ValueError("composition mass fractions must sum to one")
        return value


class SetUnitProperties(CommandBase):
    kind: Literal["set_unit_properties"]
    unit: str
    properties: dict[str, object]


class AddCompounds(CommandBase):
    kind: Literal["add_compounds"]
    compounds: list[str] = Field(min_length=1)


class SetPropertyPackage(CommandBase):
    kind: Literal["set_property_package"]
    name: str


class Solve(CommandBase):
    kind: Literal["solve"]


class DeleteObject(CommandBase):
    kind: Literal["delete_object"]
    object: str


class Disconnect(CommandBase):
    kind: Literal["disconnect"]
    unit: str
    stream: str
    role: Literal["feed", "product", "energy_feed", "energy_product"]
    port: int = Field(ge=0)


class UnsupportedCommand(CommandBase):
    kind: Literal[
        "controller_set",
        "event_add",
        "event_remove",
        "dynamics_run",
        "state_save",
        "state_restore",
    ]
    parameters: dict[str, object] = Field(default_factory=dict)


EditorCommand = (
    CreateUnit
    | CreateMaterialStream
    | CreateEnergyStream
    | Connect
    | Move
    | Rename
    | SetStreamConditions
    | SetUnitProperties
    | AddCompounds
    | SetPropertyPackage
    | Solve
    | DeleteObject
    | Disconnect
    | UnsupportedCommand
)


class CommandResult(BaseModel):
    case: EditorCaseRead
    projection: EditorProjectionRead
    readback: dict[str, object]
