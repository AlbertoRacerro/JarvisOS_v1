from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ModelSpecCreate(BaseModel):
    title: str = Field(min_length=1)
    engineering_question: str = Field(min_length=1)
    scope: str | None = None
    status: str = "draft"
    maturity_status: str = "draft"
    assumptions_summary: str | None = None
    inputs_summary: str | None = None
    outputs_summary: str | None = None
    raw_payload: str | None = None


class ModelSpecRead(ModelSpecCreate):
    id: str
    workspace_id: str
    schema_version: int
    created_at: str
    updated_at: str


class AssumptionCreate(BaseModel):
    statement: str = Field(min_length=1)
    scope: str | None = None
    confidence: Literal["low", "medium", "high"] | None = None
    status: Literal["proposed", "accepted", "rejected", "superseded"] = "proposed"
    source_ref: str | None = None
    notes: str | None = None


class AssumptionRead(AssumptionCreate):
    id: str
    workspace_id: str
    created_at: str
    updated_at: str


class ParameterCreate(BaseModel):
    name: str = Field(min_length=1)
    symbol: str | None = None
    value: str | None = None
    unit: str = Field(min_length=1)
    value_status: Literal["candidate", "literature", "measured", "validated", "accepted"] = "candidate"
    value_min: float | None = None
    value_max: float | None = None
    source_ref: str | None = None
    confidence: float | None = None
    status: str = "draft"
    notes: str | None = None
    supersedes_parameter_id: str | None = None

    @model_validator(mode="after")
    def validate_uncertainty_bounds(self) -> "ParameterCreate":
        if self.value_min is not None and self.value_max is not None and self.value_min > self.value_max:
            raise ValueError("value_min must be less than or equal to value_max")
        if self.supersedes_parameter_id is not None and self.status != "proposed":
            raise ValueError("Parameter replacements must be created with proposed status.")
        return self


class ParameterRead(ParameterCreate):
    id: str
    workspace_id: str
    created_at: str
    updated_at: str


class RequirementCreate(BaseModel):
    statement: str = Field(min_length=1)
    rationale: str | None = None
    status: Literal["draft", "active", "retired"] = "draft"
    notes: str | None = None


class RequirementUpdate(BaseModel):
    statement: str | None = Field(default=None, min_length=1)
    rationale: str | None = None
    status: Literal["draft", "active", "retired"] | None = None
    notes: str | None = None


class RequirementRead(RequirementCreate):
    id: str
    workspace_id: str
    schema_version: int
    created_at: str
    updated_at: str


class SimulationRunCreate(BaseModel):
    model_version_id: str | None = None
    run_label: str | None = None
    status: str = "planned"
    input_payload: str | None = None
    parameter_payload: str | None = None
    output_payload: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    notes: str | None = None


class SimulationRunRead(SimulationRunCreate):
    id: str
    workspace_id: str
    created_at: str


class DecisionCreate(BaseModel):
    title: str = Field(min_length=1)
    decision_text: str = Field(min_length=1)
    rationale: str | None = None
    status: str = "draft"
    linked_run_id: str | None = None
    notes: str | None = None


class DecisionRead(DecisionCreate):
    id: str
    workspace_id: str
    created_at: str
    updated_at: str
