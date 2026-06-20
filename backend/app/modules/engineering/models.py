from pydantic import BaseModel, Field


class EntityCreate(BaseModel):
    entity_type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: str = "active"
    maturity_status: str = "draft"
    raw_payload: str | None = None


class EntityRead(EntityCreate):
    id: str
    workspace_id: str
    schema_version: int
    created_at: str
    updated_at: str


class EntityLinkCreate(BaseModel):
    source_entity_id: str
    target_entity_id: str
    link_type: str = Field(min_length=1)
    confidence: float | None = None
    notes: str | None = None


class EntityLinkRead(EntityLinkCreate):
    id: str
    workspace_id: str
    created_at: str


class EngineeringBoundary(BaseModel):
    id: str
    entity_type: str
    title: str
    maturity: str = "draft"
