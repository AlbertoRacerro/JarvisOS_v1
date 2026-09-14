from pathlib import Path
from threading import Thread
from time import sleep

from app.core.database import open_sqlite_connection
from app.modules.development.brainstorm_models import (
    BrainstormDiscussionRecord,
    BrainstormExactRef,
    BrainstormPromotionCreate,
    BrainstormRawCreate,
    BrainstormReconcileCreate,
)
from app.modules.development.brainstorm_service import (
    create_promotion,
    create_raw,
    list_raw,
    reconcile,
    record_discussion,
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


def _idea(workspace_id: str, raw_id: str):
    return reconcile(
        BrainstormReconcileCreate(
            workspace_id=workspace_id,
            title="Idea",
            takeaway="Takeaway",
            synthesis="Synthesis",
            source_refs=[BrainstormExactRef(ref_type="raw", ref_id=raw_id)],
            actor="tester",
            idempotency_key="idea-1",
        )
    )


def test_raw_discussion_provenance_survives_fresh_read(monkeypatch, tmp_path: Path) -> None:
    _initialize(monkeypatch, tmp_path)
    workspace = _workspace("brainstorm-raw-discussion")
    raw = _raw(workspace.id, "Discuss without reconciling", "raw-1")
    discussion = record_discussion(
        BrainstormDiscussionRecord(
            workspace_id=workspace.id,
            target_type="raw",
            target_id=str(raw["id"]),
            source_refs=[BrainstormExactRef(ref_type="raw", ref_id=str(raw["id"]))],
            actor="tester",
            idempotency_key="discussion-1",
        )
    )

    stored = list_raw(workspace.id)
    assert len(stored) == 1
    assert stored[0]["lineage_state"] == "DISCUSSED"
    assert stored[0]["discussions"] == [discussion]
    assert stored[0]["discussions"][0]["created_by"] == "tester"
    assert stored[0]["discussions"][0]["source_refs"] == [
        {"ref_type": "raw", "ref_id": str(raw["id"]), "revision": None}
    ]
    assert "bound_revision" not in stored[0]["discussions"][0]


def test_promotion_waits_for_writer_then_rejects_newly_stale_revision(monkeypatch, tmp_path: Path) -> None:
    _initialize(monkeypatch, tmp_path)
    workspace = _workspace("brainstorm-writer-order")
    raw = _raw(workspace.id, "Raw", "raw-1")
    idea = _idea(workspace.id, str(raw["id"]))
    outcome: dict[str, str] = {}

    def promote() -> None:
        try:
            create_promotion(
                BrainstormPromotionCreate(
                    workspace_id=workspace.id,
                    idea_id=str(idea["id"]),
                    source_revision=1,
                    target="roadmap",
                    payload={"title": "Must be stale after writer commits"},
                    actor="tester",
                    idempotency_key="promotion-1",
                )
            )
        except DevelopmentError as exc:
            outcome["code"] = exc.code

    with open_sqlite_connection() as writer:
        writer.execute("BEGIN IMMEDIATE")
        writer.execute(
            "UPDATE brainstorm_ideas SET current_revision = 2 WHERE workspace_id = ? AND id = ?",
            (workspace.id, str(idea["id"])),
        )
        thread = Thread(target=promote)
        thread.start()
        sleep(0.1)
        assert thread.is_alive(), "promotion should wait behind the existing SQLite writer"
        writer.commit()

    thread.join(timeout=2)
    assert not thread.is_alive()
    assert outcome == {"code": "brainstorm_promotion_stale"}
