from typing import Literal

from pydantic import BaseModel, Field, model_validator

OwnerKind = Literal["requirement", "decision", "assumption", "parameter", "model_spec", "requirement_applicability"]
OperationKind = Literal["create", "update", "retire", "set_applicability", "retire_applicability"]
ParentKind = Literal["reconciled", "working"]


class ProjectKnowledgeOperation(BaseModel):
    operation_id: str | None = None
    owner_kind: OwnerKind
    operation_kind: OperationKind
    owner_id: str | None = None
    expected_updated_at: str | None = None
    provisional_ref: str | None = None
    fields: dict[str, object] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list, max_length=64)
    proposal_id: str | None = None
    dependency_add: list[tuple[str, str, str]] = Field(default_factory=list, max_length=128)
    dependency_remove: list[tuple[str, str, str]] = Field(default_factory=list, max_length=128)

    @model_validator(mode="after")
    def validate_identity(self) -> "ProjectKnowledgeOperation":
        if self.operation_kind == "create":
            if self.owner_kind not in {"requirement", "decision"}:
                raise ValueError("V0 create is limited to Requirement-backed Project Basis records and Decisions.")
            if self.owner_id is not None or self.expected_updated_at is not None:
                raise ValueError("Create operations cannot bind an existing owner identity.")
        elif self.operation_kind in {"update", "retire"}:
            if not self.owner_id or not self.expected_updated_at:
                raise ValueError("Existing-owner mutations require owner_id and expected_updated_at.")
        elif self.operation_kind in {"set_applicability", "retire_applicability"}:
            if self.owner_kind != "requirement_applicability":
                raise ValueError("Applicability operations must use requirement_applicability owner kind.")
        return self


class DraftCreate(BaseModel):
    workspace_id: str
    parent_kind: ParentKind = "reconciled"
    parent_revision_id: str | None = None
    operations: list[ProjectKnowledgeOperation] = Field(default_factory=list, max_length=128)


class DraftUpdate(BaseModel):
    workspace_id: str
    expected_revision_token: str
    operations: list[ProjectKnowledgeOperation] = Field(max_length=128)


class DraftRead(BaseModel):
    id: str
    workspace_id: str
    parent_revision_id: str | None
    parent_kind: ParentKind
    revision_token: str
    operations: list[ProjectKnowledgeOperation]
    preview_digest: str | None
    created_at: str
    updated_at: str


class ImpactPreview(BaseModel):
    draft_id: str
    draft_revision_token: str
    parent_kind: ParentKind
    parent_revision_id: str | None
    ancestor_revision_ids: list[str]
    affected_refs: list[str]
    owner_tokens: dict[str, str]
    applicability_refs: list[str]
    recomputation_required: list[str]
    diagnostics: list[str]
    complete: bool
    digest: str


class ApprovalRequest(BaseModel):
    workspace_id: str
    approval_request_key: str = Field(min_length=1, max_length=200)
    draft_id: str
    expected_draft_revision_token: str
    expected_preview_digest: str
    origin: str = Field(default="operator", min_length=1, max_length=80)


class ApprovalRead(BaseModel):
    request_id: str
    state: Literal["pending", "success", "failed"]
    outcome: str | None
    working_revision_id: str | None
    failure_code: str | None = None


class WorkingRevisionRead(BaseModel):
    id: str
    workspace_id: str
    parent_revision_id: str | None
    parent_kind: ParentKind
    state: Literal["working", "discarded", "superseded", "reconciled"]
    change_set_digest: str
    operations: list[ProjectKnowledgeOperation]
    projected_state_digest: str
    origin: str
    created_at: str
    accepted_at: str
    superseded_by_revision_id: str | None
    reconciled_snapshot_id: str | None


class ApplicabilityMutation(BaseModel):
    requirement_id: str
    target_kind: Literal["workspace", "model_spec", "model_version"]
    target_id: str
    effect: Literal["include", "exclude"]
    expected_updated_at: str | None = None


class ScalarAdmissionRequest(BaseModel):
    workspace_id: str
    run_id: str
    output_name: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1, max_length=200)
    unit: str = Field(max_length=100)
    source_payload_digest: str = Field(min_length=64, max_length=64)
    extractor_id: str = Field(min_length=1, max_length=120)
    extractor_version: str = Field(min_length=1, max_length=80)


class ScalarResultRead(BaseModel):
    id: str
    run_id: str
    output_name: str
    value: str
    unit: str
    source_payload_digest: str
    extractor_id: str
    extractor_version: str
    created_at: str


class ValidationRequest(BaseModel):
    workspace_id: str
    working_revision_id: str
    requirement_id: str
    expected_requirement_updated_at: str
    validated_basis_digest: str
    applicability_set_digest: str
    source_run_id: str | None = None
    source_output_name: str | None = None
    expected_predecessor_validation_id: str | None = None


class ValidationRead(BaseModel):
    id: str
    working_revision_id: str
    requirement_id: str
    outcome: Literal["pass", "fail", "not_evaluable", "no_material_effect", "recomputation_required"]
    reason_code: str
    source_run_id: str | None
    source_scalar_id: str | None
    supersedes_validation_id: str | None
    created_at: str


class RevalidationRead(BaseModel):
    working_revision_id: str
    complete: bool
    mandatory_requirement_ids: list[str]
    current_validation_ids: list[str]
    blocking_requirement_ids: list[str]
    known_fail_requirement_ids: list[str]
    recomputation_required: list[str]
    selected_validation_set_digest: str
    diagnostics: list[str]


class ReconcileRequest(BaseModel):
    workspace_id: str
    idempotency_key: str = Field(min_length=1, max_length=200)
    working_revision_id: str
    expected_target_snapshot_id: str | None = None
    expected_target_digest: str
    expected_selected_validation_set_digest: str
    known_fail_acknowledgement: str | None = Field(default=None, max_length=1000)
    policy_identity: str | None = Field(default=None, max_length=120)


class ReconcileRead(BaseModel):
    request_id: str
    state: Literal["pending", "success", "failed"]
    outcome: str | None
    resulting_snapshot_id: str | None
    canonical_id_map: dict[str, str]
    failure_code: str | None = None


class SnapshotRead(BaseModel):
    id: str
    workspace_id: str
    reconciled_revision_id: str
    parent_snapshot_id: str | None
    manifest_version: str
    owner_manifest: list[dict[str, object]]
    owner_manifest_digest: str
    edge_manifest: list[dict[str, object]]
    graph_digest: str
    graph_complete: bool
    canonical_id_map: dict[str, str]
    selected_validation_set_digest: str
    created_at: str


class RevisionStateCommand(BaseModel):
    workspace_id: str
    action: Literal["discard", "supersede"]
    superseded_by_revision_id: str | None = None
