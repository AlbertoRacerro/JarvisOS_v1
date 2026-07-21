from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FlowGradeSubjectRead(BaseModel):
    id: str
    flow_id: str
    terminal_attempt_id: str | None = None
    subject_version: int
    flow_outcome_digest: str
    final_accounting_digest: str
    final_output_digest: str | None = None
    valid: bool
    invalidated_at: str | None = None
    created_at: str


class FlowGradeEventRead(BaseModel):
    id: str
    flow_id: str
    subject_id: str
    subject_version: int
    flow_outcome_digest: str
    event_index: int
    action: Literal["set", "withdraw"]
    grade: Literal["useful", "partly", "rework", "failed"] | None = None
    reason_codes: list[str] = Field(default_factory=list)
    note: str | None = None
    actor: str
    source: Literal["operator_ui", "operator_api"]
    supersedes_event_id: str | None = None
    idempotency_key: str
    created_at: str
    schema_version: str
    policy_version: str
    replayed: bool = False


class FlowGradeRead(BaseModel):
    flow_id: str
    subject: FlowGradeSubjectRead
    current_grade_event: FlowGradeEventRead | None = None
    latest_event: FlowGradeEventRead | None = None
    history: list[FlowGradeEventRead] = Field(default_factory=list)


class FlowGradeSetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grade: Literal["useful", "partly", "rework", "failed"]
    expected_subject_version: int = Field(ge=1, strict=True)
    expected_flow_outcome_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    idempotency_key: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$",
    )
    expected_current_grade_event_id: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$",
    )
    reason_codes: list[str] = Field(default_factory=list, max_length=5)
    note: str | None = Field(default=None, max_length=1000)


class FlowGradeWithdrawRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_subject_version: int = Field(ge=1, strict=True)
    expected_flow_outcome_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    expected_current_grade_event_id: str = Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$"
    )
    idempotency_key: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$",
    )
