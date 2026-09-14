from __future__ import annotations

import threading
from pathlib import Path

import app.modules.development.brainstorm_service as brainstorm_service
from app.modules.development.brainstorm_models import (
    BrainstormDiscussionRecord,
    BrainstormExactRef,
    BrainstormRawCreate,
    BrainstormReconcileCreate,
)
from app.modules.workspaces.models import WorkspaceCreate
from app.modules.workspaces.service import create_workspace


def _initialize(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    from app.core.config import get_settings
    from app.core.database import initialize_database

    get_settings.cache_clear()
    initialize_database()


def test_get_idea_keeps_one_snapshot_during_concurrent_reconcile(monkeypatch, tmp_path: Path) -> None:
    _initialize(monkeypatch, tmp_path)
    workspace = create_workspace(
        WorkspaceCreate(
            name="brainstorm-snapshot",
            slug="brainstorm-snapshot",
            description=None,
            status="active",
        )
    )
    raw = brainstorm_service.create_raw(
        BrainstormRawCreate(
            workspace_id=workspace.id,
            content="Snapshot source",
            attachment_refs=[],
            created_by="tester",
            idempotency_key="snapshot-raw",
        )
    )
    discussion = brainstorm_service.record_discussion(
        BrainstormDiscussionRecord(
            workspace_id=workspace.id,
            target_type="raw",
            target_id=str(raw["id"]),
            source_refs=[BrainstormExactRef(ref_type="raw", ref_id=str(raw["id"]))],
            actor="tester",
            idempotency_key="snapshot-discussion",
        )
    )
    idea = brainstorm_service.reconcile(
        BrainstormReconcileCreate(
            workspace_id=workspace.id,
            title="Idea v1",
            takeaway="Takeaway v1",
            synthesis="Synthesis v1",
            source_refs=[BrainstormExactRef(ref_type="raw", ref_id=str(raw["id"]))],
            actor="tester",
            idempotency_key="snapshot-v1",
        )
    )

    reader_paused = threading.Event()
    writer_done = threading.Event()
    writer_errors: list[BaseException] = []
    original_idea_payload = brainstorm_service._idea_payload

    def paused_idea_payload(connection, row):
        value = original_idea_payload(connection, row)
        if threading.current_thread() is threading.main_thread() and not reader_paused.is_set():
            reader_paused.set()
            assert writer_done.wait(5), "concurrent reconciliation did not complete"
        return value

    monkeypatch.setattr(brainstorm_service, "_idea_payload", paused_idea_payload)

    def reconcile_v2() -> None:
        try:
            assert reader_paused.wait(5), "detail read never reached snapshot pause"
            brainstorm_service.reconcile(
                BrainstormReconcileCreate(
                    workspace_id=workspace.id,
                    idea_id=str(idea["id"]),
                    expected_revision=1,
                    title="Idea v2",
                    takeaway="Takeaway v2",
                    synthesis="Synthesis v2",
                    source_refs=[BrainstormExactRef(ref_type="raw", ref_id=str(raw["id"]))],
                    actor="tester",
                    idempotency_key="snapshot-v2",
                )
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            writer_errors.append(exc)
        finally:
            writer_done.set()

    writer = threading.Thread(target=reconcile_v2, daemon=True)
    writer.start()
    in_flight = brainstorm_service.get_idea(workspace.id, str(idea["id"]))
    writer.join(5)
    assert not writer.is_alive()
    assert writer_errors == []

    assert in_flight["current_revision"] == 1
    assert [row["revision"] for row in in_flight["revisions"]] == [1]
    assert [(row["id"], row["bound_revision"]) for row in in_flight["discussions"]] == [
        (discussion["id"], 1)
    ]

    monkeypatch.setattr(brainstorm_service, "_idea_payload", original_idea_payload)
    after = brainstorm_service.get_idea(workspace.id, str(idea["id"]))
    assert after["current_revision"] == 2
    assert [row["revision"] for row in after["revisions"]] == [2, 1]
    assert [(row["id"], row["bound_revision"]) for row in after["discussions"]] == [
        (discussion["id"], 1),
        (discussion["id"], 2),
    ]
