from pathlib import Path

import pytest

from app.core.config import get_settings
from app.core.database import initialize_database
from app.modules.development.brainstorm_models import BrainstormExactRef, BrainstormRawCreate
from app.modules.development.brainstorm_service import create_raw
from app.modules.development.service import DevelopmentError
from app.modules.files.models import ArtifactCreate
from app.modules.files.service import create_artifact_record
from app.modules.workspaces.models import WorkspaceCreate
from app.modules.workspaces.service import create_workspace


def _initialize(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    get_settings.cache_clear()
    initialize_database()


def _workspace(slug: str):
    return create_workspace(WorkspaceCreate(name=slug, slug=slug, description=None, status="active"))


def test_generic_artifact_ref_is_workspace_bound(monkeypatch, tmp_path: Path) -> None:
    _initialize(monkeypatch, tmp_path)
    left = _workspace("brainstorm-generic-left")
    right = _workspace("brainstorm-generic-right")
    artifact = create_artifact_record(
        right.id,
        ArtifactCreate(
            filename="evidence.txt",
            stored_path="artifacts/evidence.txt",
            artifact_type="text",
        ),
    )
    ref = BrainstormExactRef(ref_type="generic_artifact", ref_id=artifact.id)

    accepted = create_raw(
        BrainstormRawCreate(
            workspace_id=right.id,
            content="Bound evidence",
            attachment_refs=[ref],
            created_by="tester",
            idempotency_key="generic-right",
        )
    )
    assert accepted["attachment_refs"] == [
        {"ref_type": "generic_artifact", "ref_id": artifact.id, "revision": None}
    ]

    with pytest.raises(DevelopmentError) as foreign:
        create_raw(
            BrainstormRawCreate(
                workspace_id=left.id,
                content="Foreign evidence",
                attachment_refs=[ref],
                created_by="tester",
                idempotency_key="generic-left",
            )
        )
    assert foreign.value.code == "brainstorm_ref_not_found"


def test_generic_artifact_ref_rejects_revision(monkeypatch, tmp_path: Path) -> None:
    _initialize(monkeypatch, tmp_path)
    workspace = _workspace("brainstorm-generic-revision")
    artifact = create_artifact_record(
        workspace.id,
        ArtifactCreate(
            filename="evidence.txt",
            stored_path="artifacts/evidence.txt",
            artifact_type="text",
        ),
    )

    with pytest.raises(DevelopmentError) as invalid:
        create_raw(
            BrainstormRawCreate(
                workspace_id=workspace.id,
                content="Versioned evidence",
                attachment_refs=[
                    BrainstormExactRef(ref_type="generic_artifact", ref_id=artifact.id, revision=1)
                ],
                created_by="tester",
                idempotency_key="generic-revision",
            )
        )
    assert invalid.value.code == "brainstorm_ref_invalid"
