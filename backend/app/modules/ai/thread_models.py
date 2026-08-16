from typing import Literal

from pydantic import BaseModel, Field

PersistenceState = Literal["reserved", "dispatching", "captured", "capture_failed"]


class AIThreadCreate(BaseModel):
    workspace_id: str = Field(min_length=1, max_length=128)
    title: str | None = Field(default=None, max_length=120)


class AIThreadSubmit(BaseModel):
    request_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
    prompt: str = Field(min_length=1, max_length=12000)
    task_kind: str = Field(default="general", pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
    route_class: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$")
    max_tokens: int | None = Field(default=None, gt=0)


class AIThreadSummary(BaseModel):
    id: str
    workspace_id: str
    title: str | None = None
    created_at: str
    last_activity_at: str


class AIThreadInteractionRead(BaseModel):
    id: str
    request_id: str
    interaction_index: int
    user_text: str
    assistant_text: str | None = None
    assistant_text_truncated: bool
    flow_id: str
    persistence_state: PersistenceState
    persistence_error: str | None = None
    flow_state: str
    terminal_reason: str | None = None
    attempt_count: int
    terminal_attempt_id: str | None = None
    proposal_ids: list[str] = Field(default_factory=list)
    proposal_count: int = 0
    proposals_truncated: bool = False
    created_at: str
    updated_at: str


class AIThreadDetail(AIThreadSummary):
    interactions: list[AIThreadInteractionRead] = Field(default_factory=list)
    has_older: bool = False


class AIThreadList(BaseModel):
    threads: list[AIThreadSummary] = Field(default_factory=list)


class AIThreadSubmitRead(BaseModel):
    interaction: AIThreadInteractionRead
