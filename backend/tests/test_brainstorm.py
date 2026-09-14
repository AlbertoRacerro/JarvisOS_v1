from pathlib import Path

import pytest

from app.modules.development.brainstorm_models import (
    BrainstormDiscussionRecord,
    BrainstormExactRef,
    BrainstormPromotionCreate,
    BrainstormRawCreate,
    BrainstormReconcileCreate,
    BrainstormSupersedeRequest,
)
from app.modules.development.brainstorm_service import (
    create_promotion,
    create_raw,
    get_idea,
    list_raw,
    reconcile,
    record_discussion,
    supersede,
)
from app.modules.development.service import DevelopmentError
from app.modules.workspaces.models import WorkspaceCreate
from app.modules.workspaces.service import create_workspace


def _initialize(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    from app.core.config import get_settings
    from app.core.database import initialize_database

    get_settings.cache_clear()
    initialize_database()


def _workspace(slug: str):
    return create_workspace(
        WorkspaceCreate(name=slug, slug=slug, description=None, status="active")
    )


def _raw(workspace_id: str, content: str, key: str):
    return create_raw(
        BrainstormRawCreate(
            workspace_id=workspace_id,
            content=content,
            attachment_refs=[],
            created_by="tester",
            idempotency_key=key,
        )
    )


def _idea(workspace_id: str, raw_id: str, key: str, title: str = "Idea"):
    return reconcile(
        BrainstormReconcileCreate(
            workspace_id=workspace_id,
            title=title,
            takeaway="Takeaway",
            synthesis="Synthesis",
            source_refs=[BrainstormExactRef(ref_type="raw", ref_id=raw_id)],
            actor="tester",
            idempotency_key=key,
        )
    )


def test_raw_is_immutable_and_retry_is_payload_bound(monkeypatch, tmp_path: Path) -> None:
    _initialize(monkeypatch, tmp_path)
    workspace = _workspace("brainstorm-raw")
    first = _raw(workspace.id, "Original raw thought", "raw-1")
    retry = _raw(workspace.id, "Original raw thought", "raw-1")
    assert retry["id"] == first["id"]
    assert retry["content"] == "Original raw thought"

    with pytest.raises(DevelopmentError) as mismatch:
        _raw(workspace.id, "Changed thought", "raw-1")
    assert mismatch.value.code == "brainstorm_idempotency_mismatch"
    stored = list_raw(workspace.id)
    assert len(stored) == 1
    assert stored[0]["content"] == "Original raw thought"


def test_discussion_replay_and_idea_detail_preserve_exact_provenance(monkeypatch, tmp_path: Path) -> None:
    _initialize(monkeypatch, tmp_path)
    workspace = _workspace("brainstorm-discussion")
    raw = _raw(workspace.id, "Discuss this", "raw-discussion")
    payload = BrainstormDiscussionRecord(
        workspace_id=workspace.id,
        target_type="raw",
        target_id=str(raw["id"]),
        source_refs=[BrainstormExactRef(ref_type="raw", ref_id=str(raw["id"]))],
        actor="tester",
        idempotency_key="discussion-1",
    )
    first = record_discussion(payload)
    replay = record_discussion(payload)
    assert replay == first
    assert first["source_refs"] == [
        {"ref_type": "raw", "ref_id": str(raw["id"]), "revision": None}
    ]

    idea = _idea(workspace.id, str(raw["id"]), "discussion-idea")
    detail = get_idea(workspace.id, str(idea["id"]))
    assert len(detail["discussions"]) == 1
    assert detail["discussions"][0]["id"] == first["id"]
    assert detail["discussions"][0]["created_by"] == "tester"
    assert detail["discussions"][0]["source_refs"] == first["source_refs"]


def test_reconciliation_appends_immutable_revision_and_stale_cas_fails(monkeypatch, tmp_path: Path) -> None:
    _initialize(monkeypatch, tmp_path)
    workspace = _workspace("brainstorm-reconcile")
    raw = _raw(workspace.id, "Raw", "raw-1")
    idea = _idea(workspace.id, str(raw["id"]), "idea-1")
    assert idea["current_revision"] == 1

    updated = reconcile(
        BrainstormReconcileCreate(
            workspace_id=workspace.id,
            idea_id=str(idea["id"]),
            expected_revision=1,
            title="Idea v2",
            takeaway="Updated takeaway",
            synthesis="Updated synthesis",
            source_refs=[BrainstormExactRef(ref_type="raw", ref_id=str(raw["id"]))],
            actor="tester",
            idempotency_key="idea-2",
        )
    )
    assert updated["current_revision"] == 2

    with pytest.raises(DevelopmentError) as stale:
        reconcile(
            BrainstormReconcileCreate(
                workspace_id=workspace.id,
                idea_id=str(idea["id"]),
                expected_revision=1,
                title="Stale",
                takeaway="Stale",
                synthesis="Stale",
                source_refs=[BrainstormExactRef(ref_type="raw", ref_id=str(raw["id"]))],
                actor="tester",
                idempotency_key="idea-stale",
            )
        )
    assert stale.value.code == "brainstorm_idea_stale"
    detail = get_idea(workspace.id, str(idea["id"]))
    assert [row["revision"] for row in detail["revisions"]] == [2, 1]
    assert detail["revisions"][1]["title"] == "Idea"


def test_cross_workspace_source_fails_closed(monkeypatch, tmp_path: Path) -> None:
    _initialize(monkeypatch, tmp_path)
    left = _workspace("brainstorm-left")
    right = _workspace("brainstorm-right")
    foreign = _raw(right.id, "Foreign", "foreign-raw")

    with pytest.raises(DevelopmentError) as missing:
        _idea(left.id, str(foreign["id"]), "left-idea")
    assert missing.value.code == "brainstorm_raw_not_found"


def test_supersession_rejects_self_and_stale_promotion(monkeypatch, tmp_path: Path) -> None:
    _initialize(monkeypatch, tmp_path)
    workspace = _workspace("brainstorm-lineage")
    raw_a = _raw(workspace.id, "A", "raw-a")
    raw_b = _raw(workspace.id, "B", "raw-b")
    a = _idea(workspace.id, str(raw_a["id"]), "idea-a", "A")
    b = _idea(workspace.id, str(raw_b["id"]), "idea-b", "B")

    with pytest.raises(DevelopmentError) as self_link:
        supersede(
            BrainstormSupersedeRequest(
                workspace_id=workspace.id,
                idea_id=str(a["id"]),
                expected_revision=1,
                successor_idea_id=str(a["id"]),
                successor_revision=1,
                actor="tester",
                idempotency_key="self",
            )
        )
    assert self_link.value.code == "brainstorm_lineage_self"

    superseded = supersede(
        BrainstormSupersedeRequest(
            workspace_id=workspace.id,
            idea_id=str(a["id"]),
            expected_revision=1,
            successor_idea_id=str(b["id"]),
            successor_revision=1,
            actor="tester",
            idempotency_key="a-to-b",
        )
    )
    assert superseded["lineage_state"] == "SUPERSEDED"

    with pytest.raises(DevelopmentError) as blocked:
        create_promotion(
            BrainstormPromotionCreate(
                workspace_id=workspace.id,
                idea_id=str(a["id"]),
                source_revision=1,
                target="roadmap",
                payload={"title": "Proposal only"},
                actor="tester",
                idempotency_key="promotion-a",
            )
        )
    assert blocked.value.code == "brainstorm_promotion_superseded"

    proposal = create_promotion(
        BrainstormPromotionCreate(
            workspace_id=workspace.id,
            idea_id=str(b["id"]),
            source_revision=1,
            target="coding",
            payload={"summary": "Proposal only"},
            actor="tester",
            idempotency_key="promotion-b",
        )
    )
    assert proposal["state"] == "pending"
    assert proposal["downstream_handoff_id"] is None