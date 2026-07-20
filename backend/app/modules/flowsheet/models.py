from typing import Literal

from pydantic import BaseModel, Field

NodeKind = Literal[
    "model_spec",
    "model_version",
    "simulation_run",
    "runner_job",
    "artifact",
    "assumption",
    "parameter",
    "decision",
    "requirement",
    "ai_job",
    "bluecad_candidate",
    "bluecad_attempt",
    "evidence",
]
EdgeClass = Literal["dependency", "provenance"]
DiagnosticCode = Literal[
    "malformed_reference",
    "unsupported_reference",
    "dangling_reference",
    "payload_invalid",
    "payload_reference_invalid",
    "context_manifest_invalid",
]


class FlowsheetNodeRead(BaseModel):
    ref: str
    kind: NodeKind
    id: str
    label: str = Field(max_length=120)
    status: str | None = None
    origin: str | None = None
    created_at: str | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class FlowsheetEdgeRead(BaseModel):
    id: str
    upstream_ref: str
    downstream_ref: str
    relation: str
    edge_class: EdgeClass
    authorities: list[str]
    source_fields: list[str]


class FlowsheetUnresolvedReferenceRead(BaseModel):
    owner_ref: str
    source_field: str
    code: DiagnosticCode
    raw_ref: str | None = Field(default=None, max_length=256)


class FlowsheetDiagnosticsRead(BaseModel):
    unsupported_reference_count: int = 0
    malformed_reference_count: int = 0
    dangling_reference_count: int = 0
    cycle_count: int = 0
    manual_binding_count: int = 0
    unresolved_references: list[FlowsheetUnresolvedReferenceRead] = Field(default_factory=list)
    cycles: list[list[str]] = Field(default_factory=list)


class FlowsheetGraphRead(BaseModel):
    workspace_id: str
    nodes: list[FlowsheetNodeRead]
    edges: list[FlowsheetEdgeRead]
    topological_order: list[str] | None
    is_acyclic: bool
    diagnostics: FlowsheetDiagnosticsRead
