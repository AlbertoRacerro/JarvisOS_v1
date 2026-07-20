from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest

from app.modules.ai.context_builder import canonical_digest
from app.modules.ai.token_flow_segments import store_protected_segment
from app.modules.ai.token_flow_service import (
    TokenFlowConflictError,
    create_flow,
    recompute_flow_aggregates,
)
from app.modules.ai.token_flow_status import get_continuation_flow_status

BODY = "Protected status fixture body that must never appear in status."
NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)


@pytest.fixture
def initialized_database():
    from app.core.database import initialize_database
    from app.modules.ai.settings import ensure_ai_settings

    initialize_database()
    ensure_ai_settings()


def _workspace(workspace_id: str) -> None:
    from app.core.database import open_sqlite_connection
    from app.modules.events.service import utc_now

    with open_sqlite_connection() as connection:
        now = utc_now()
        connection.execute(
            """
            INSERT INTO workspaces (id, name, slug, status, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            (workspace_id, workspace_id, workspace_id, now, now),
        )
        connection.commit()


def _flow_with_segment() -> str:
    from app.core.database import open_sqlite_connection
    from app.modules.events.service import utc_now

    _workspace("ws-status")
    flow = create_flow(
        task_kind="synthesis",
        requested_route_class="local:fake",
        workspace_id="ws-status",
    )
    flow_id = str(flow["id"])
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_jobs (
                id, created_at, status, task_kind, requested_route_class,
                selected_route_class, provider_id, model_id, fallback_index,
                route_reason_json, output_digest, input_tokens, output_tokens,
                flow_id, flow_attempt_index, execution_class, adapter_invoked,
                external_dispatch_state, requested_output_ceiling,
                effective_output_ceiling, normalized_finish_reason,
                normalized_usage_source, accounting_basis,
                accounted_provider_spend_usd_decimal, outcome_reason,
                capability_version, accounting_version
            ) VALUES (
                'attempt-0', ?, 'success', 'synthesis', 'local:fake',
                'local:fake', 'fake', 'fake-v0', 0, ?, ?, 4, 9,
                ?, 0, 'synthetic', 1, 'not_applicable', 128, 128,
                'length', 'estimated', 'synthetic_not_economic', '0',
                'success', 'provider-registry-v1', 'token-flow-v0'
            )
            """,
            (
                utc_now(),
                '{"decision_reason":"bound:local:fake","fallback_attempt_index":0}',
                canonical_digest({"text": BODY}),
                flow_id,
            ),
        )
        connection.commit()
    recompute_flow_aggregates(flow_id)
    store_protected_segment(
        flow_id=flow_id,
        originating_attempt_id="attempt-0",
        body_text=BODY,
        effective_sensitivity_level="S1",
        workspace_id="ws-status",
        now=NOW,
    )
    return flow_id


def test_status_contains_only_safe_aggregates_and_digests(
    initialized_database,
) -> None:
    flow_id = _flow_with_segment()
    status = get_continuation_flow_status(
        flow_id=flow_id,
        workspace_id="ws-status",
        now=NOW + timedelta(minutes=1),
    )
    payload = asdict(status)

    assert status.state == "running"
    assert status.attempt_count == 1
    assert status.ordered_attempt_ids == ("attempt-0",)
    assert status.synthetic_evidence_present is True
    assert status.segment_count == 1
    assert status.segment_digests == (canonical_digest({"text": BODY}),)
    assert status.segment_expired == (False,)
    assert BODY not in repr(status)
    assert BODY not in str(payload)
    assert "body_text" not in payload
    assert "prompt" not in payload
    assert "packet_json" not in payload


def test_status_requires_exact_workspace_authority(
    initialized_database,
) -> None:
    flow_id = _flow_with_segment()
    with pytest.raises(TokenFlowConflictError, match="workspace"):
        get_continuation_flow_status(
            flow_id=flow_id,
            workspace_id="other-workspace",
            now=NOW,
        )


def test_status_reports_expiry_without_exposing_expired_body(
    initialized_database,
) -> None:
    flow_id = _flow_with_segment()
    status = get_continuation_flow_status(
        flow_id=flow_id,
        workspace_id="ws-status",
        now=NOW + timedelta(hours=25),
    )

    assert status.segment_count == 1
    assert status.segment_expired == (True,)
    assert BODY not in repr(status)
