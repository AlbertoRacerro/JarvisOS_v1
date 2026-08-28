from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.modules.ai.context_builder import DEFAULT_CONTEXT_BUDGET_CHARS

JarvisActionClass = Literal[
    "PRESENTATION",
    "READ",
    "CONTEXT",
    "PROPOSE",
    "COMMIT",
    "EXECUTE",
    "NAVIGATE",
]
JarvisResolutionState = Literal["current", "stale", "unavailable", "unknown"]

CANONICAL_ROUTE_PAIRS: dict[str, str] = {
    "design-process": "/design/process",
    "design-bluecad": "/design/bluecad",
    "memory-project-basis": "/memory/project-basis",
    "memory-models": "/memory/models",
    "memory-literature": "/memory/literature",
    "development-roadmap-timeline": "/development/roadmap/timeline",
    "development-roadmap-calendar": "/development/roadmap/calendar",
    "development-brainstorm": "/development/brainstorm",
    "coding-repository": "/coding/repository",
    "coding-runtime": "/coding/runtime",
    "settings-appearance": "/settings/appearance",
    "settings-ai": "/settings/ai",
    "settings-system": "/settings/system",
    "runs": "/runs",
    "engineering-data": "/engineering-data",
    "review": "/review",
    "ai-threads": "/ai-threads",
}


class JarvisRouteDescriptor(BaseModel):
    route_id: str = Field(min_length=1, max_length=96)
    canonical_path: str = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def validate_frozen_pair(self) -> JarvisRouteDescriptor:
        if CANONICAL_ROUTE_PAIRS.get(self.route_id) != self.canonical_path:
            raise ValueError("route_id and canonical_path must match one frozen canonical route pair")
        return self


class JarvisCapabilityDescriptor(BaseModel):
    capability_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$",
    )
    route_id: str = Field(min_length=1, max_length=96)
    action_class: JarvisActionClass
    label: str | None = Field(default=None, max_length=160)

    @model_validator(mode="after")
    def require_canonical_route_id(self) -> JarvisCapabilityDescriptor:
        if self.route_id not in CANONICAL_ROUTE_PAIRS:
            raise ValueError("capability route_id must be one frozen canonical route id")
        return self


class JarvisExactRef(BaseModel):
    workspace_id: str = Field(min_length=1, max_length=128)
    owner: str = Field(min_length=1, max_length=96, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
    kind: str = Field(min_length=1, max_length=96, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
    id: str = Field(min_length=1, max_length=256)
    version: str | None = Field(default=None, min_length=1, max_length=256)
    revision: str | None = Field(default=None, min_length=1, max_length=256)
    immutable_ref: str | None = Field(default=None, min_length=1, max_length=512)
    content_digest: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def require_exact_identity(self) -> JarvisExactRef:
        if not any((self.version, self.revision, self.immutable_ref, self.content_digest)):
            raise ValueError("exact context ref requires version, revision, immutable_ref, or content_digest")
        return self


class JarvisContextRequest(BaseModel):
    workspace_id: str = Field(min_length=1, max_length=128)
    route: JarvisRouteDescriptor
    selected_refs: list[JarvisExactRef] = Field(default_factory=list, max_length=50)
    added_context_refs: list[JarvisExactRef] = Field(default_factory=list, max_length=50)
    budget_chars: int = Field(
        default=DEFAULT_CONTEXT_BUDGET_CHARS,
        ge=0,
        le=DEFAULT_CONTEXT_BUDGET_CHARS,
    )


class JarvisResolvedRef(BaseModel):
    ref: JarvisExactRef
    state: JarvisResolutionState
    content: dict[str, object] | list[object] | str | int | float | bool | None = None
    provenance: dict[str, object] = Field(default_factory=dict)
    action_classes: list[JarvisActionClass] = Field(default_factory=list)
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def enforce_inert_content(self) -> JarvisResolvedRef:
        if self.state != "current" and self.content is not None:
            raise ValueError("non-current exact refs cannot expose context content")
        return self


class JarvisContextRefOutcome(BaseModel):
    ref: JarvisExactRef
    state: JarvisResolutionState
    included: bool = False
    dropped_for_budget: bool = False
    reason: str | None = None
    provenance: dict[str, object] = Field(default_factory=dict)


class JarvisContextPreview(BaseModel):
    request: JarvisContextRequest
    blocks: list[dict[str, object]] = Field(default_factory=list)
    context_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    context_sources_manifest: list[dict[str, object]] = Field(default_factory=list)
    ref_outcomes: list[JarvisContextRefOutcome] = Field(default_factory=list)
    dispatchable: bool
    included_count: int
    dropped_count: int
    char_count: int
    estimated_token_count: int
    budget_chars: int
