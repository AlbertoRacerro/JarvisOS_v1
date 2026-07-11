from __future__ import annotations

from uuid import uuid4

import pytest

import app.modules.ai.sensitivity as sensitivity_module
from app.core.database import initialize_database, open_sqlite_connection
from app.modules.ai.context_builder import ContextSelectionSpec
from app.modules.ai.sensitivity import (
    build_external_context_preview,
    create_sensitivity_label,
)
from app.modules.ai.sensitivity_models import SensitivityLabelCreate
from app.modules.events.service import utc_now

WORKSPACE_ID = "bluerev"


def _bootstrap() -> None:
    initialize_database()
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO workspaces (id, name, slug, description, status, created_at, updated_at)
            VALUES (?, 'BlueRev', 'bluerev', NULL, 'active', ?, ?)
            """,
            (WORKSPACE_ID, now, now),
        )
        connection.commit()


def _decision(text: str) -> str:
    record_id = str(uuid4())
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO decisions (
                id, workspace_id, title, decision_text, rationale, status,
                linked_run_id, created_at, updated_at, notes
            ) VALUES (?, ?, 'Decision', ?, NULL, 'accepted', NULL, ?, ?, NULL)
            """,
            (record_id, WORKSPACE_ID, text, now, now),
        )
        connection.commit()
    return record_id


def _update_decision(record_id: str, text: str) -> None:
    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE decisions SET decision_text = ?, updated_at = ? WHERE id = ?",
            (text, utc_now(), record_id),
        )
        connection.commit()


def test_preview_rejects_label_for_newer_source_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _bootstrap()
    record_id = _decision("Original generic pump note")
    subject_ref = f"decision:{record_id}"
    create_sensitivity_label(
        SensitivityLabelCreate(
            workspace_id=WORKSPACE_ID,
            subject_ref=subject_ref,
            level="S1",
        )
    )
    original_select = sensitivity_module.select_context_records

    def select_then_replace_and_relabel(*args, **kwargs):
        selected = original_select(*args, **kwargs)
        _update_decision(record_id, "Replacement generic pump note")
        create_sensitivity_label(
            SensitivityLabelCreate(
                workspace_id=WORKSPACE_ID,
                subject_ref=subject_ref,
                level="S1",
            )
        )
        return selected

    monkeypatch.setattr(
        sensitivity_module,
        "select_context_records",
        select_then_replace_and_relabel,
    )

    preview = build_external_context_preview(
        WORKSPACE_ID,
        32_000,
        ContextSelectionSpec(kinds=["decision"], ids=[record_id]),
    )

    assert preview.blocks == []
    assert preview.included_count == 0
    assert preview.withheld_sources_manifest == [
        {
            "source_ref": subject_ref,
            "effective_level": "unknown",
            "reason": "source_changed_during_preview",
        }
    ]
