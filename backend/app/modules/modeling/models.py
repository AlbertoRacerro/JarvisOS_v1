from pydantic import BaseModel, Field


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
    confidence: float | None = None
    status: str = "draft"
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
    unit: str | None = None
    source_ref: str | None = None
    confidence: float | None = None
    status: str = "draft"
    notes: str | None = None


class ParameterRead(ParameterCreate):
    id: str
    workspace_id: str
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
