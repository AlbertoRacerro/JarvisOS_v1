from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.database import initialize_database, open_sqlite_connection
from app.modules.ai.egress_persistence import prepare_egress_attempt
from app.modules.ai.egress_policy import EXTERNAL_PROVIDER_OPERATION
from app.modules.ai.egress_service import EgressPacketMaterial
from app.modules.ai.models import AISettingsUpdate
from app.modules.ai.settings import ensure_ai_settings, get_ai_settings, update_ai_settings
from app.modules.ai.token_guard import (
    reconcile_scaleway_smoke_reservation,
    reserve_scaleway_smoke_tokens,
)
from app.modules.events.service import utc_now

NOW = datetime(2026, 8, 4, 9, 0, tzinfo=UTC)
WORKSPACE_ID = "bluerev"
MODEL_ID = "gemma-4-26b-a4b-it"


def _bootstrap(monkeypatch) -> None:
    initialize_database()
    ensure_ai_settings()
    update_ai_settings(
        AISettingsUpdate(
            policy_mode="FAST_DEV",
            provider_mode="scaleway",
            paid_ai_enabled=True,
            monthly_api_budget_usd=100.0,
            scaleway_enabled=True,
            scaleway_smoke_test_enabled=True,
            scaleway_live_smoke_test_enabled=True,
            scaleway_monthly_token_cap=10_000,
            scaleway_hard_stop_token_cap=10_000,
        )
    )
    monkeypatch.setenv("SCALEWAY_API_KEY", "test-only-secret")
    with open_sqlite_connection() as connection:
        now = utc_now()
        connection.execute(
            """
            INSERT OR IGNORE INTO workspaces (
                id, name, slug, description, status, created_at, updated_at
            ) VALUES (?, 'BlueRev', 'bluerev', NULL, 'active', ?, ?)
            """,
            (WORKSPACE_ID, now, now),
        )
        connection.commit()


def _set_caps(*, monthly: int, hard_stop: int) -> None:
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            UPDATE ai_settings
            SET scaleway_monthly_token_cap = ?,
                scaleway_hard_stop_token_cap = ?
            WHERE id = 'default'
            """,
            (monthly, hard_stop),
        )
        connection.commit()


def _material() -> EgressPacketMaterial:
    return EgressPacketMaterial(
        operation=EXTERNAL_PROVIDER_OPERATION,
        task_kind="decision_support",
        route_class="external:scaleway",
        provider_id="scaleway",
        model_id=MODEL_ID,
        fallback_index=0,
        prompt="Reply OK.",
        context_blocks=(),
        prompt_level="S1",
        context_level="S1",
        final_level="S1",
        max_output_tokens=8,
        workspace_id=WORKSPACE_ID,
        included_manifest=(),
        source_digests=(),
    )


def _seed_recorded_attempt(preparation) -> None:
    ai_job_id = str(uuid4())
    reservation_id = str(uuid4())
    attempt_id = str(uuid4())
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_jobs (
                id, created_at, status, task_kind, requested_route_class,
                selected_route_class, provider_id, model_id,
                route_reason_json, input_tokens, output_tokens, cost_estimate
            ) VALUES (?, ?, 'completed', 'decision_support',
                      'external:scaleway', 'external:scaleway', 'scaleway',
                      ?, '{}', 1, 1, 0.0)
            """,
            (ai_job_id, NOW.isoformat(), MODEL_ID),
        )
        connection.execute(
            """
            INSERT INTO egress_budget_reservations (
                id, decision_id, packet_digest, provider_id, model_id,
                projected_input_tokens, projected_output_tokens,
                projected_cost_upper_usd, state, created_at, expires_at,
                attempt_started_at, reconciled_at, egress_attempt_id,
                ai_job_id, actual_input_tokens, actual_output_tokens,
                actual_cost_usd, reconciliation_status
            ) VALUES (?, ?, ?, 'scaleway', ?, ?, ?, ?, 'reconciled',
                      ?, ?, ?, ?, ?, ?, 1, 1, 0.0, 'actual')
            """,
            (
                reservation_id,
                preparation.decision_id,
                preparation.packet_digest,
                MODEL_ID,
                preparation.projected_input_tokens,
                preparation.projected_output_tokens,
                preparation.projected_cost_upper_usd,
                NOW.isoformat(),
                (NOW + timedelta(minutes=5)).isoformat(),
                NOW.isoformat(),
                NOW.isoformat(),
                attempt_id,
                ai_job_id,
            ),
        )
        connection.execute(
            """
            INSERT INTO egress_attempts (
                id, decision_id, packet_id, ai_job_id, reservation_id,
                route_class, provider_id, model_id, fallback_index,
                network_attempt, reconciliation_status,
                projected_input_tokens, projected_output_tokens,
                projected_cost_upper_usd, actual_input_tokens,
                actual_output_tokens, actual_cost_usd, created_at
            ) VALUES (?, ?, ?, ?, ?, 'external:scaleway', 'scaleway', ?,
                      0, 1, 'actual', ?, ?, ?, 1, 1, 0.0, ?)
            """,
            (
                attempt_id,
                preparation.decision_id,
                preparation.packet_id,
                ai_job_id,
                reservation_id,
                MODEL_ID,
                preparation.projected_input_tokens,
                preparation.projected_output_tokens,
                preparation.projected_cost_upper_usd,
                NOW.isoformat(),
            ),
        )
        connection.commit()


def test_smoke_reservation_counts_completed_routed_usage(monkeypatch) -> None:
    _bootstrap(monkeypatch)
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_jobs (
                id, created_at, status, task_kind, selected_route_class,
                provider_id, model_id, route_reason_json, input_tokens,
                output_tokens, cost_estimate
            ) VALUES (?, ?, 'completed', 'decision_support',
                      'external:scaleway', 'scaleway', ?, '{}', 40, 10, 0.0)
            """,
            (str(uuid4()), NOW.isoformat(), MODEL_ID),
        )
        connection.commit()
    _set_caps(monthly=50, hard_stop=500)

    decision = reserve_scaleway_smoke_tokens(
        input_text="public",
        estimated_output_tokens=1,
        now=NOW,
    )

    assert decision.allowed is False
    assert decision.reason == "scaleway_monthly_token_cap_exceeded"
    assert decision.metadata.token_usage_month_to_date == 50
    settings = get_ai_settings()
    assert settings.scaleway_input_tokens_month_to_date == 0
    assert settings.scaleway_output_tokens_month_to_date == 0


def test_smoke_reservation_counts_active_routed_reservations(monkeypatch) -> None:
    _bootstrap(monkeypatch)
    first = prepare_egress_attempt(_material(), now=NOW)
    assert first.result == "pause"
    _seed_recorded_attempt(first)
    active = prepare_egress_attempt(_material(), now=NOW + timedelta(seconds=1))
    assert active.result == "allow"
    assert active.reservation_id is not None

    active_tokens = active.projected_input_tokens + active.projected_output_tokens
    _set_caps(monthly=active_tokens + 2, hard_stop=10_000)
    decision = reserve_scaleway_smoke_tokens(
        input_text="public",
        estimated_output_tokens=1,
        now=NOW + timedelta(seconds=2),
    )

    assert decision.allowed is False
    assert decision.reason == "scaleway_monthly_token_cap_exceeded"
    assert decision.metadata.token_usage_month_to_date >= active_tokens


def test_smoke_reservation_reconciles_projection_to_reported_usage(monkeypatch) -> None:
    _bootstrap(monkeypatch)

    decision = reserve_scaleway_smoke_tokens(
        input_text="public checkpoint",
        estimated_output_tokens=8,
        now=NOW,
    )
    assert decision.allowed is True
    reserved = get_ai_settings()
    assert reserved.scaleway_input_tokens_month_to_date == (
        decision.metadata.estimated_input_tokens
    )
    assert reserved.scaleway_output_tokens_month_to_date == 8

    reconcile_scaleway_smoke_reservation(
        decision.metadata,
        reported_input_tokens=2,
        reported_output_tokens=1,
    )

    reconciled = get_ai_settings()
    assert reconciled.scaleway_input_tokens_month_to_date == 2
    assert reconciled.scaleway_output_tokens_month_to_date == 1
