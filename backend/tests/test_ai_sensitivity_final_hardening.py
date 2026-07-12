from __future__ import annotations

import sqlite3
from uuid import uuid4

import pytest

import app.modules.ai.sensitivity as sensitivity_module
from app.core.database import initialize_database, open_sqlite_connection
from app.modules.ai.context_builder import ContextSelectionSpec
from app.modules.ai.sensitivity import (
    build_external_context_preview,
    create_sanitized_derivative,
)
from app.modules.ai.sensitivity_models import SanitizedDerivativeCreate
from app.modules.events.service import utc_now

WORKSPACE_ID = "bluerev"


def _bootstrap() -> None:
    initialize_database()
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO workspaces (
                id, name, slug, description, status, created_at, updated_at
            ) VALUES (?, 'BlueRev', 'bluerev', NULL, 'active', ?, ?)
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


@pytest.mark.parametrize(
    ("content", "expected_level"),
    [
        ("confidential private project note", "S2"),
        ("BlueRev proprietary geometry decision", "S3"),
        ("api_key=synthetic-secret-value", "S4"),
    ],
)
def test_unlabelled_hard_floor_is_preserved_in_withheld_manifest(
    content: str,
    expected_level: str,
) -> None:
    _bootstrap()
    record_id = _decision(content)

    preview = build_external_context_preview(
        WORKSPACE_ID,
        32_000,
        ContextSelectionSpec(kinds=["decision"], ids=[record_id]),
    )

    assert preview.blocks == []
    assert preview.withheld_sources_manifest == [
        {
            "source_ref": f"decision:{record_id}",
            "effective_level": expected_level,
            "reason": "missing_current_label",
        }
    ]


def test_multisource_derivative_draft_uses_one_database_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _bootstrap()
    first = _decision("Generic source A")
    second = _decision("Generic source B")
    seen_connections: list[sqlite3.Connection] = []
    original = sensitivity_module._resolve_source_snapshot_and_label_in_connection

    def tracked_resolver(connection: sqlite3.Connection, *args, **kwargs):
        seen_connections.append(connection)
        return original(connection, *args, **kwargs)

    monkeypatch.setattr(
        sensitivity_module,
        "_resolve_source_snapshot_and_label_in_connection",
        tracked_resolver,
    )

    derivative = create_sanitized_derivative(
        SanitizedDerivativeCreate(
            workspace_id=WORKSPACE_ID,
            source_refs=[f"decision:{first}", f"decision:{second}"],
            content="Generic combined engineering summary.",
            effective_level="S1",
            transformations=["Removed project-specific details"],
        )
    )

    assert derivative.status == "draft"
    assert len(seen_connections) == 2
    assert seen_connections[0] is seen_connections[1]
    assert set(derivative.source_digests) == {
        f"decision:{first}",
        f"decision:{second}",
    }
