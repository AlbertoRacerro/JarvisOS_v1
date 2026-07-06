from typing import Literal

from pydantic import BaseModel, Field

MemoryRecordKind = Literal["assumption", "parameter", "decision"]
MemoryStatus = Literal["proposed", "accepted", "rejected", "superseded"]
MemoryOrigin = Literal["user", "ai_proposed", "calc"]


class MemoryProposalCreate(BaseModel):
    record_kind: MemoryRecordKind
    workspace_id: str = Field(min_length=1)
    source_ai_job_id: str | None = None
    statement: str | None = None
    scope: str | None = None
    confidence: str | float | None = None
    name: str | None = None
    symbol: str | None = None
    value: str | None = None
    unit: str = "unspecified"
    value_status: str = "candidate"
    value_min: float | None = None
    value_max: float | None = None
    source_ref: str | None = None
    title: str | None = None
    decision_text: str | None = None
    rationale: str | None = None
    linked_run_id: str | None = None
    notes: str | None = None


class CalcParameterProposalCreate(BaseModel):
    workspace_id: str = Field(min_length=1)
    runner_job_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    symbol: str | None = None
    value: str | None = None
    unit: str = Field(default="unspecified", min_length=1)
    value_status: str = "candidate"
    value_min: float | None = None
    value_max: float | None = None
    confidence: float | None = None
    notes: str | None = None


class MemoryRecordRead(BaseModel):
    id: str
    record_kind: MemoryRecordKind
    workspace_id: str
    status: MemoryStatus
    origin: MemoryOrigin
    source_ai_job_id: str | None = None
    promoted_at: str | None = None
    created_at: str
    updated_at: str
    title: str | None = None
    statement: str | None = None
    decision_text: str | None = None
    name: str | None = None
    source_ref: str | None = None
    notes: str | None = None


class MemoryTransitionRead(BaseModel):
    record: MemoryRecordRead
