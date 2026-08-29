from __future__ import annotations

import hashlib

import pytest

from app.core.bootstrap import initialize_storage
from app.modules.modeling.models import SimulationRunCreate
from app.modules.modeling.service import create_simulation_run
from app.modules.project_knowledge.models import (
    ApprovalRequest,
    DraftCreate,
    ProjectKnowledgeOperation,
    RevisionStateCommand,
    ScalarAdmissionRequest,
)
from app.modules.project_knowledge.revision_lifecycle import change_revision_state
from app.modules.project_knowledge.service import (
    ProjectKnowledgeError,
    admit_scalar_result,
    approve_draft,
    create_draft,
    preview_impact,
)


def _approve(*, key: str, parent_revision_id: str | None = None) -> str:
    draft = create_draft(
        DraftCreate(
            workspace_id="bluerev",
            parent_kind="working" if parent_revision_id else "reconciled",
            parent_revision_id=parent_revision_id,
            operations=[
                ProjectKnowledgeOperation(
                    owner_kind="requirement",
                    operation_kind="create",
                    fields={
                        "statement": f"criterion {key}",
                        "status": "active",
                        "basis_kind": "requirement",
                        "reconciliation_gate": "advisory",
                    },
                )
            ],
        )
    )
    preview = preview_impact("bluerev", draft.id)
    approval = approve_draft(
        ApprovalRequest(
            workspace_id="bluerev",
            approval_request_key=key,
            draft_id=draft.id,
            expected_draft_revision_token=draft.revision_token,
            expected_preview_digest=preview.digest,
        )
    )
    assert approval.working_revision_id is not None
    return approval.working_revision_id


def test_scalar_admission_rejects_client_authored_value_without_owner_proof() -> None:
    """A valid payload digest must not authorize a caller-invented scalar value."""
    initialize_storage(seed_default=True)
    output_payload = '{"pressure_bar":10.0}'
    run = create_simulation_run(
        "bluerev",
        SimulationRunCreate(status="completed", output_payload=output_payload),
    )
    source_digest = hashlib.sha256(output_payload.encode("utf-8")).hexdigest()

    with pytest.raises(ProjectKnowledgeError):
        admit_scalar_result(
            ScalarAdmissionRequest(
                workspace_id="bluerev",
                run_id=run.id,
                output_name="pressure_bar",
                value="999",
                unit="bar",
                source_payload_digest=source_digest,
                extractor_id="caller-claimed-extractor",
                extractor_version="1",
            )
        )


def test_superseded_parent_does_not_strand_exact_direct_successor() -> None:
    """The accepted direct successor must remain traversable after superseding its parent."""
    initialize_storage(seed_default=True)
    source_id = _approve(key="semantic-supersede-source")
    successor_id = _approve(key="semantic-supersede-successor", parent_revision_id=source_id)

    change_revision_state(
        source_id,
        RevisionStateCommand(
            workspace_id="bluerev",
            action="supersede",
            superseded_by_revision_id=successor_id,
        ),
    )

    continuation = create_draft(
        DraftCreate(
            workspace_id="bluerev",
            parent_kind="working",
            parent_revision_id=successor_id,
            operations=[],
        )
    )
    preview = preview_impact("bluerev", continuation.id)
    assert successor_id in preview.ancestor_revision_ids
    assert source_id in preview.ancestor_revision_ids
