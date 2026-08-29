from __future__ import annotations

import hashlib
import json

from app.core.bootstrap import initialize_storage
from app.core.database import open_sqlite_connection
from app.modules.project_knowledge.models import ProjectKnowledgeOperation
from app.modules.project_knowledge.service import _run_binding_matches_revision


def _change_set(operation: ProjectKnowledgeOperation | None) -> tuple[str, str]:
    payload = [] if operation is None else [operation.model_dump()]
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return raw, hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _insert_revision(
    connection,
    *,
    revision_id: str,
    parent_revision_id: str | None,
    parent_kind: str,
    operation: ProjectKnowledgeOperation | None,
    projected_state_digest: str,
) -> None:
    raw, digest = _change_set(operation)
    connection.execute(
        """
        INSERT INTO project_knowledge_revisions (
            id, workspace_id, parent_revision_id, parent_kind, state,
            change_set_digest, change_set_json, projected_state_digest,
            origin, created_at, accepted_at
        ) VALUES (?, 'bluerev', ?, ?, 'working', ?, ?, ?, 'user', ?, ?)
        """,
        (
            revision_id,
            parent_revision_id,
            parent_kind,
            digest,
            raw,
            projected_state_digest,
            "2026-08-29T18:00:00+00:00",
            "2026-08-29T18:00:00+00:00",
        ),
    )


def test_scalar_reuse_accepts_only_exact_sibling_validation_basis() -> None:
    initialize_storage(seed_default=True)
    requirement_change = ProjectKnowledgeOperation(
        owner_kind="requirement",
        operation_kind="create",
        fields={"statement": "criterion-only change"},
    )
    other_requirement_change = ProjectKnowledgeOperation(
        owner_kind="requirement",
        operation_kind="create",
        fields={"statement": "another criterion-only change"},
    )
    input_change = ProjectKnowledgeOperation(
        owner_kind="parameter",
        operation_kind="create",
        fields={"name": "feed_temperature", "value": "350", "unit": "K"},
    )

    with open_sqlite_connection() as connection:
        _insert_revision(
            connection,
            revision_id="basis-parent",
            parent_revision_id=None,
            parent_kind="reconciled",
            operation=None,
            projected_state_digest="parent-basis",
        )
        _insert_revision(
            connection,
            revision_id="source-revision",
            parent_revision_id="basis-parent",
            parent_kind="working",
            operation=requirement_change,
            projected_state_digest="source-projection",
        )
        _insert_revision(
            connection,
            revision_id="target-criterion-only",
            parent_revision_id="basis-parent",
            parent_kind="working",
            operation=other_requirement_change,
            projected_state_digest="target-projection",
        )
        _insert_revision(
            connection,
            revision_id="target-input-change",
            parent_revision_id="basis-parent",
            parent_kind="working",
            operation=input_change,
            projected_state_digest="input-changed-projection",
        )
        connection.commit()

        assert _run_binding_matches_revision(
            connection,
            workspace_id="bluerev",
            run_revision_id="source-revision",
            working_revision_id="target-criterion-only",
            working_basis_digest="target-projection",
        )
        assert not _run_binding_matches_revision(
            connection,
            workspace_id="bluerev",
            run_revision_id="source-revision",
            working_revision_id="target-input-change",
            working_basis_digest="input-changed-projection",
        )

        connection.execute(
            "UPDATE project_knowledge_revisions SET change_set_json = '[]' WHERE id = 'basis-parent'"
        )
        assert not _run_binding_matches_revision(
            connection,
            workspace_id="bluerev",
            run_revision_id="source-revision",
            working_revision_id="target-criterion-only",
            working_basis_digest="target-projection",
        )
