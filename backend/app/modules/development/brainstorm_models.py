from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

BrainstormLineageState = Literal["NEW", "DISCUSSED", "RECONCILED", "SUPERSEDED"]
BrainstormPromotionTarget = Literal["roadmap", "design", "coding"]


class StrictBrainstormModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BrainstormExactRef(StrictBrainstormModel):
    ref_type: str = Field(min_length=1, max_length=80)
    ref_id: str = Field(min_length=1, max_length=240)
    revision: int | None = Field(default=None, ge=1)

    @field_validator("ref_type", "ref_id")
    @classmethod
    def reject_blank_ref(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reference fields must contain non-whitespace characters")
        return value


class BrainstormRawCreate(StrictBrainstormModel):
    workspace_id: str = Field(min_length=1)
    content: str = Field(min_length=1, max_length=50_000)
    attachment_refs: list[BrainstormExactRef] = Field(default_factory=list, max_length=32)
    created_by: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=160)

    @field_validator("content")
    @classmethod
    def reject_blank_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must contain non-whitespace characters")
        return value


class BrainstormDiscussionRecord(StrictBrainstormModel):
    workspace_id: str = Field(min_length=1)
    target_type: Literal["raw", "idea"]
    target_id: str = Field(min_length=1)
    expected_revision: int | None = Field(default=None, ge=1)
    source_refs: list[BrainstormExactRef] = Field(min_length=1, max_length=128)
    actor: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=160)


class BrainstormReconcileCreate(StrictBrainstormModel):
    workspace_id: str = Field(min_length=1)
    idea_id: str | None = Field(default=None, min_length=1)
    expected_revision: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=500)
    takeaway: str = Field(min_length=1, max_length=4_000)
    synthesis: str = Field(min_length=1, max_length=50_000)
    source_refs: list[BrainstormExactRef] = Field(min_length=1, max_length=128)
    actor: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=160)

    @field_validator("title", "takeaway", "synthesis")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reconciled text must contain non-whitespace characters")
        return value


class BrainstormSupersedeRequest(StrictBrainstormModel):
    workspace_id: str = Field(min_length=1)
    idea_id: str = Field(min_length=1)
    expected_revision: int = Field(ge=1)
    successor_idea_id: str = Field(min_length=1)
    successor_revision: int = Field(ge=1)
    actor: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=160)


class BrainstormPromotionCreate(StrictBrainstormModel):
    workspace_id: str = Field(min_length=1)
    idea_id: str = Field(min_length=1)
    source_revision: int = Field(ge=1)
    target: BrainstormPromotionTarget
    payload: dict[str, object]
    actor: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=160)
