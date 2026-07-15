from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.database import initialize_database, open_sqlite_connection
from app.modules.ai.egress_lifecycle import (
    consume_confirmation_ticket,
    reconcile_reserved_attempt,
    start_reserved_attempt,
)
from app.modules.ai.egress_persistence import EgressStateError, prepare_egress_attempt
from app.modules.ai.egress_policy import EXTERNAL_PROVIDER_OPERATION, load_default_egress_policy
from app.modules.ai.egress_service import EgressPacketMaterial
from app.modules.ai.models import AISettingsUpdate
from app.modules.ai.provider_registry import load_default_provider_registry
from app.modules.ai.settings import ensure_ai_settings, update_ai_settings
from app.modules.events.service import utc_now

WORKSPACE_ID = "bluerev"
NOW = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)


def _bootstrap(monkeypatch, *, budget: float = 100.0) -> None:
    initialize_database()
    ensure_ai_settings()
    update_ai_settings(
        AISettingsUpdate(
            policy_mode="FAST_DEV",
            monthly_api_budget_usd=budget,
            paid_ai_enabled=True,
            provider_mode="deepseek",
        )
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only-secret")
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


def _material(**overrides) -> EgressPacketMaterial:
    values = {
        "operation": EXTERNAL_PROVIDER_OPERATION,
        "task_kind": "general",
        "route_class": "external:cheap",
        "provider_id": "deepseek",
        "model_id": "deepseek-v4-pro",
        "fallback_index": 0,
        "prompt": "Summarize the approved generic pump note.",
        "context_blocks": (),
        "prompt_level": "S1",
        "context_level": "S0",
        "final_level": "S1",
        "max_output_tokens": 128,
        "workspace_id": WORKSPACE_ID,
        "included_manifest": (),
        "source_digests": (),
    }
    values.update(overrides)
    return EgressPacketMaterial(**values)


def _pending_ticket(monkeypatch):
    _bootstrap(monkeypatch)
    preparation = prepare_egress_attempt(_material(), now=NOW)
    assert preparation.ticket_id is not None
    return preparation


def _insert_ai_job(
    *,
    provider_id: str = "deepseek",
    model_id: str = "deepseek-v4-pro",
    route_class: str = "external:cheap",
) -> str:
    ai_job_id = str(uuid4())
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_jobs (
                id, created_at, status, task_kind, requested_route_class,
                selected_route_class, provider_id, model_id, route_reason_json
            ) VALUES (?, ?, 'queued', 'general', ?, ?, ?, ?, '{}')
            """,
            (
                ai_job_id,
                NOW.isoformat(),
                route_class,
                route_class,
                provider_id,
                model_id,
            ),
        )
        connection.commit()
    return ai_job_id


def test_ticket_consumption_reloads_exact_packet_and_creates_one_reservation(monkeypatch):
    preparation = _pending_ticket(monkeypatch)

    result = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))

    assert result.authorized is True
    assert result.reason_code == "ticket_consumed"
    assert result.reservation_id is not None
    assert result.packet_digest == preparation.packet_digest
    assert "approved generic pump note" in result.packet_json
    assert "approved generic pump note" not in repr(result)
    with open_sqlite_connection() as connection:
        ticket = connection.execute(
            "SELECT state, version FROM egress_confirmation_tickets WHERE id = ?",
            (preparation.ticket_id,),
        ).fetchone()
        reservation = connection.execute(
            "SELECT state, decision_id FROM egress_budget_reservations WHERE id = ?",
            (result.reservation_id,),
        ).fetchone()
    assert ticket["state"] == "consumed"
    assert ticket["version"] == 1
    assert reservation["state"] == "active"
    assert reservation["decision_id"] == preparation.decision_id


def test_ticket_consumption_is_single_use(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    first = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))
    assert first.authorized is True

    with pytest.raises(EgressStateError, match="not pending: consumed"):
        consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=2))

    with open_sqlite_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM egress_budget_reservations"
        ).fetchone()["count"]
    assert count == 1


def test_expired_ticket_transition_is_persisted(monkeypatch):
    preparation = _pending_ticket(monkeypatch)

    result = consume_confirmation_ticket(
        preparation.ticket_id,
        now=NOW + timedelta(minutes=16),
    )

    assert result.authorized is False
    assert result.reason_code == "ticket_expired"
    assert result.reservation_id is None
    with open_sqlite_connection() as connection:
        state = connection.execute(
            "SELECT state FROM egress_confirmation_tickets WHERE id = ?",
            (preparation.ticket_id,),
        ).fetchone()["state"]
    assert state == "expired"


def test_packet_tampering_revokes_ticket_without_reservation(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE egress_packets SET packet_json = '{\"prompt\":\"tampered\",\"context_blocks\":[]}' WHERE id = ?",
            (preparation.packet_id,),
        )
        connection.commit()

    result = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))

    assert result.authorized is False
    assert result.reason_code == "ticket_binding_or_policy_drift"
    with open_sqlite_connection() as connection:
        ticket = connection.execute(
            "SELECT state, revocation_reason FROM egress_confirmation_tickets WHERE id = ?",
            (preparation.ticket_id,),
        ).fetchone()
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM egress_budget_reservations"
        ).fetchone()["count"]
    assert ticket["state"] == "revoked"
    assert ticket["revocation_reason"] == "ticket_binding_or_policy_drift"
    assert count == 0


def test_policy_drift_revokes_ticket(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    policy = replace(load_default_egress_policy(), policy_version="egress-policy-v2")

    result = consume_confirmation_ticket(
        preparation.ticket_id,
        policy=policy,
        now=NOW + timedelta(seconds=1),
    )

    assert result.authorized is False
    assert result.reason_code == "ticket_binding_or_policy_drift"


def test_budget_change_after_ticket_revokes_before_reservation(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    update_ai_settings(AISettingsUpdate(monthly_api_budget_usd=0.000001))

    result = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))

    assert result.authorized is False
    assert result.reason_code == "global_monthly_cost_cap_exceeded"
    with open_sqlite_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM egress_budget_reservations"
        ).fetchone()["count"]
    assert count == 0


def test_start_reservation_binds_existing_ai_job_and_is_single_use(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    consumed = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))
    ai_job_id = _insert_ai_job()

    started = start_reserved_attempt(
        consumed.reservation_id,
        ai_job_id=ai_job_id,
        now=NOW + timedelta(seconds=2),
    )

    assert started.ai_job_id == ai_job_id
    assert started.packet_digest == preparation.packet_digest
    assert "approved generic pump note" in started.packet_json
    assert "approved generic pump note" not in repr(started)
    with pytest.raises(EgressStateError, match="not active: in_flight"):
        start_reserved_attempt(
            consumed.reservation_id,
            ai_job_id=ai_job_id,
            now=NOW + timedelta(seconds=3),
        )


def test_start_rejects_ai_job_binding_mismatch_and_keeps_reservation_active(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    consumed = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))
    ai_job_id = _insert_ai_job(provider_id="glm", model_id="glm-5.2")

    with pytest.raises(EgressStateError, match="binding does not match"):
        start_reserved_attempt(
            consumed.reservation_id,
            ai_job_id=ai_job_id,
            now=NOW + timedelta(seconds=2),
        )

    with open_sqlite_connection() as connection:
        state = connection.execute(
            "SELECT state FROM egress_budget_reservations WHERE id = ?",
            (consumed.reservation_id,),
        ).fetchone()["state"]
    assert state == "active"


def test_expired_reservation_start_records_expiry(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    consumed = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))
    ai_job_id = _insert_ai_job()

    with pytest.raises(EgressStateError, match="expired before start"):
        start_reserved_attempt(
            consumed.reservation_id,
            ai_job_id=ai_job_id,
            now=NOW + timedelta(minutes=6),
        )

    with open_sqlite_connection() as connection:
        state = connection.execute(
            "SELECT state FROM egress_budget_reservations WHERE id = ?",
            (consumed.reservation_id,),
        ).fetchone()["state"]
    assert state == "expired"


def test_pre_network_failure_releases_zero_provider_consumption(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    consumed = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))
    ai_job_id = _insert_ai_job()

    result = reconcile_reserved_attempt(
        consumed.reservation_id,
        ai_job_id=ai_job_id,
        network_attempt=False,
        now=NOW + timedelta(seconds=2),
    )

    assert result.reservation_state == "released"
    assert result.reconciliation_status == "not_sent"
    assert result.actual_input_tokens == 0
    assert result.actual_output_tokens == 0
    assert result.actual_cost_usd == 0
    with open_sqlite_connection() as connection:
        attempt = connection.execute(
            "SELECT network_attempt, actual_cost_usd FROM egress_attempts WHERE id = ?",
            (result.egress_attempt_id,),
        ).fetchone()
    assert attempt["network_attempt"] == 0
    assert attempt["actual_cost_usd"] == 0


def test_network_attempt_reconciles_actual_usage_and_cost_once(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    consumed = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))
    ai_job_id = _insert_ai_job()
    start_reserved_attempt(
        consumed.reservation_id,
        ai_job_id=ai_job_id,
        now=NOW + timedelta(seconds=2),
    )

    result = reconcile_reserved_attempt(
        consumed.reservation_id,
        ai_job_id=ai_job_id,
        network_attempt=True,
        actual_input_tokens=10,
        actual_output_tokens=20,
        usage_source="actual",
        now=NOW + timedelta(seconds=3),
    )

    assert result.reservation_state == "reconciled"
    assert result.reconciliation_status == "actual"
    assert result.actual_cost_usd == pytest.approx((10 * 5.0 + 20 * 20.0) / 1_000_000)
    with pytest.raises(EgressStateError, match="cannot be reconciled"):
        reconcile_reserved_attempt(
            consumed.reservation_id,
            ai_job_id=ai_job_id,
            network_attempt=True,
            actual_input_tokens=10,
            actual_output_tokens=20,
            now=NOW + timedelta(seconds=4),
        )


def test_missing_usage_reconciles_to_reserved_upper_bound(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    consumed = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))
    ai_job_id = _insert_ai_job()
    start_reserved_attempt(
        consumed.reservation_id,
        ai_job_id=ai_job_id,
        now=NOW + timedelta(seconds=2),
    )

    result = reconcile_reserved_attempt(
        consumed.reservation_id,
        ai_job_id=ai_job_id,
        network_attempt=True,
        now=NOW + timedelta(seconds=3),
    )

    assert result.reconciliation_status == "conservative_missing_usage"
    assert result.actual_input_tokens == preparation.projected_input_tokens
    assert result.actual_output_tokens == preparation.projected_output_tokens
    assert result.actual_cost_usd == preparation.projected_cost_upper_usd


def test_pricing_drift_uses_reserved_upper_bound(monkeypatch):
    preparation = _pending_ticket(monkeypatch)
    consumed = consume_confirmation_ticket(preparation.ticket_id, now=NOW + timedelta(seconds=1))
    ai_job_id = _insert_ai_job()
    start_reserved_attempt(
        consumed.reservation_id,
        ai_job_id=ai_job_id,
        now=NOW + timedelta(seconds=2),
    )
    registry = load_default_provider_registry()
    models = dict(registry.models)
    key = ("deepseek", "deepseek-v4-pro")
    model = models[key]
    models[key] = replace(
        model,
        pricing=replace(model.pricing, pricing_version="drifted-pricing-v2"),
    )
    drifted_registry = replace(registry, models=models)

    result = reconcile_reserved_attempt(
        consumed.reservation_id,
        ai_job_id=ai_job_id,
        network_attempt=True,
        actual_input_tokens=10,
        actual_output_tokens=20,
        registry=drifted_registry,
        now=NOW + timedelta(seconds=3),
    )

    assert result.reconciliation_status == "conservative_pricing_drift"
    assert result.actual_input_tokens == 10
    assert result.actual_output_tokens == 20
    assert result.actual_cost_usd == preparation.projected_cost_upper_usd
