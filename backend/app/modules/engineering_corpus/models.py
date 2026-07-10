from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class EngineeringCorpusSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    course_ids: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    exclude_roles: list[str] = Field(default_factory=list)
    top_k: int = Field(default=8, ge=1, le=50)
    excerpt_chars: int = Field(default=1200, ge=200, le=2000)
    evaluation_mode: bool = False

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("query must contain non-whitespace characters")
        return normalized


class EngineeringCorpusSearchHit(BaseModel):
    segment_id: str
    content_id: str
    course_id: str | None
    role: str
    filename: str
    page: int | None
    heading: str | None
    excerpt: str
    text_sha256: str
    source_ref: str


class EngineeringCorpusSearchResponse(BaseModel):
    query: str
    snapshot_sha256: str
    evaluation_mode: bool
    effective_excluded_roles: list[str]
    hits: list[EngineeringCorpusSearchHit]
