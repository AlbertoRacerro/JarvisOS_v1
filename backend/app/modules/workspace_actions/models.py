"""166: typed workspace-action contract shared by Hermes, Relay and the Sidecar.

Models only *propose* these requests. ``workspace_actions.service`` validates them
against the canonical owner (Process draft, BLUECAD candidate ledger) at an explicit
base revision, classifies the policy tier and applies or records them.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_STRICT = ConfigDict(extra="forbid", allow_inf_nan=False)
Tag = Annotated[str, Field(min_length=1, max_length=64)]
Surface = Literal["process", "bluecad"]


# ---------------------------------------------------------------- surface context
class ProcessSelection(BaseModel):
    model_config = _STRICT
    kind: Literal["unit", "stream"]
    id: str | None = Field(default=None, max_length=64)
    tag: str | None = Field(default=None, max_length=64)


class SurfaceRef(BaseModel):
    """What the frontend says is on screen. Never trusted: the brief re-derives it from owners."""

    model_config = _STRICT
    route_id: str = Field(min_length=1, max_length=64)
    draft_id: str | None = Field(default=None, max_length=64)
    process_selection: list[ProcessSelection] = Field(default_factory=list, max_length=8)
    candidate_id: str | None = Field(default=None, max_length=64)
    bluecad_part_ids: list[str] = Field(default_factory=list, max_length=8)


class SurfaceBrief(BaseModel):
    """Bounded, owner-derived context for one turn. ``text`` is what a model sees."""

    model_config = _STRICT
    surface: Literal["process", "bluecad", "none"]
    route_id: str
    workspace_id: str
    base_revision: str | None = None  # draft revision, or candidate id for BLUECAD
    draft_id: str | None = None
    candidate_id: str | None = None
    selected: list[dict[str, object]] = Field(default_factory=list)
    summary: str  # one line for the context chip
    text: str = Field(max_length=6000)  # model-facing brief incl. vocabulary and limits
    actions: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)
    digest: str  # sha256:<hex> of canonical brief


# ---------------------------------------------------------------- Process actions
class Quantity(BaseModel):
    model_config = _STRICT
    value: float
    unit: str = Field(max_length=24)


class SetValue(BaseModel):
    model_config = _STRICT
    op: Literal["set_value"]
    target: Tag
    property: str = Field(min_length=1, max_length=64)
    value: Quantity | str | dict[str, float] | None


class SetUnitModel(BaseModel):
    model_config = _STRICT
    op: Literal["set_unit_model"]
    unit: Tag
    card: str = Field(min_length=1, max_length=200)  # a model card id or its exact name


class SetReaction(BaseModel):
    model_config = _STRICT
    op: Literal["set_reaction"]
    unit: Tag
    reaction_id: Tag
    reaction: dict[str, Any]


class AddUnit(BaseModel):
    model_config = _STRICT
    op: Literal["add_unit"]
    type: str = Field(min_length=1, max_length=48)
    tag: Tag | None = None
    near: Tag | None = None


class InsertUnitAfter(BaseModel):
    model_config = _STRICT
    op: Literal["insert_unit_after"]
    type: str = Field(min_length=1, max_length=48)
    after: Tag
    tag: Tag | None = None


class Connect(BaseModel):
    op: Literal["connect"]
    source: Tag = Field(alias="from")
    source_port: str | None = Field(default=None, alias="from_port", max_length=32)
    to: Tag
    to_port: str | None = Field(default=None, max_length=32)
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, populate_by_name=True)


class Disconnect(BaseModel):
    model_config = _STRICT
    op: Literal["disconnect"]
    stream: Tag


class Mirror(BaseModel):
    model_config = _STRICT
    op: Literal["mirror"]
    target: Tag
    axis: Literal["horizontal", "vertical"]


class MoveUnit(BaseModel):
    model_config = _STRICT
    op: Literal["move"]
    target: Tag
    dx: float = Field(ge=-2000, le=2000)
    dy: float = Field(ge=-2000, le=2000)


class Rename(BaseModel):
    model_config = _STRICT
    op: Literal["rename"]
    target: Tag
    new_tag: Tag


class DeleteObject(BaseModel):
    model_config = _STRICT
    op: Literal["delete"]
    target: Tag


ProcessAction = Annotated[
    SetValue | SetUnitModel | SetReaction | AddUnit | InsertUnitAfter | Connect | Disconnect | Mirror | MoveUnit | Rename | DeleteObject,
    Field(discriminator="op"),
]


# ---------------------------------------------------------------- BLUECAD actions
class DuplicatePart(BaseModel):
    model_config = _STRICT
    op: Literal["duplicate_part"]
    part: str = Field(min_length=1, max_length=64)
    placement: Literal["beside", "above", "along"] = "beside"
    gap_mm: float | None = Field(default=None, ge=0, le=5000)


class SetPartParam(BaseModel):
    model_config = _STRICT
    op: Literal["set_part_param"]
    part: str = Field(min_length=1, max_length=64)
    param: str = Field(min_length=1, max_length=32)
    value: float
    unit: Literal["mm", "m", "cm", "deg", "unitless"] = "mm"


class MovePart(BaseModel):
    model_config = _STRICT
    op: Literal["move_part"]
    part: str = Field(min_length=1, max_length=64)
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0
    unit: Literal["mm", "m", "cm"] = "mm"


class DeletePart(BaseModel):
    model_config = _STRICT
    op: Literal["delete_part"]
    part: str = Field(min_length=1, max_length=64)


BluecadAction = Annotated[DuplicatePart | SetPartParam | MovePart | DeletePart, Field(discriminator="op")]


# ---------------------------------------------------------------- requests and outcomes
class ActionRequest(BaseModel):
    """One atomic request: all actions apply together at ``base_revision`` or none do."""

    model_config = _STRICT
    surface: Surface
    base_revision: str = Field(min_length=1, max_length=64)  # draft revision or candidate id
    draft_id: str | None = Field(default=None, max_length=64)  # disambiguates identical revision hashes
    actions: list[ProcessAction | BluecadAction] = Field(min_length=1, max_length=8)
    rationale: str | None = Field(default=None, max_length=600)

    @model_validator(mode="after")
    def actions_match_surface(self) -> ActionRequest:
        bluecad_ops = {"duplicate_part", "set_part_param", "move_part", "delete_part"}
        expected_bluecad = self.surface == "bluecad"
        if any((action.op in bluecad_ops) != expected_bluecad for action in self.actions):
            raise ValueError(f"All actions must match the {self.surface} surface.")
        return self


class ActionOrigin(BaseModel):
    model_config = _STRICT
    kind: Literal["local", "relay"]
    thread_id: str
    interaction_id: str | None = None
    relay_run_id: str | None = None
    model: str | None = None  # human model name for provenance display


class ChangeLine(BaseModel):
    model_config = _STRICT
    label: str  # e.g. "S1 pressure", "tube_2 (new tube_run)"
    before: str | None = None
    after: str | None = None


ActionState = Literal["applied", "proposed", "refused", "stale", "dismissed", "undone"]


class ActionOutcome(BaseModel):
    model_config = _STRICT
    action_id: str
    workspace_id: str
    surface: Surface
    state: ActionState
    tier: Literal["immediate", "confirm", "none"]
    summary: str  # operator sentence, no JSON
    changes: list[ChangeLine] = Field(default_factory=list)
    base_revision: str
    result_revision: str | None = None  # Process draft revision after apply
    draft_id: str | None = None
    candidate_id: str | None = None  # BLUECAD base candidate
    child_candidate_id: str | None = None  # BLUECAD candidate created by apply
    reason_code: str | None = None
    reason: str | None = None  # plain text for refused/stale
    origin: ActionOrigin
    request_digest: str
    request: dict[str, object]  # canonical request, shown only under Technical details
    undo_available: bool = False
    created_at: str
    updated_at: str
