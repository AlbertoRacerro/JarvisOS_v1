from __future__ import annotations

from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from app.core.database import initialize_database, open_sqlite_connection
from app.modules.ai.contracts import (
    AIProviderError,
    AIProviderErrorCode,
    AIRequest,
    AIResponse,
    AIUsage,
)
from app.modules.ai.egress_confirmation import run_confirmation_ticket
from app.modules.ai.egress_persistence import EgressStateError, prepare_egress_attempt
from app.modules.ai.egress_policy import EXTERNAL_PROVIDER_OPERATION
from app.modules.ai.egress_service import EgressPacketMaterial
from app.modules.ai.models import AISettingsUpdate, EscalationConfirmRequest
from app.modules.ai.settings import ensure_ai_settings, update_ai_settings


@dataclass
class _Adapter:
    provider_id: str
    response: AIResponse | None = None
    raises: Exception | None = None

    def __post_init__(self) -> None:
        self.requests: list[AIRequest] = []

    def complete(self, request: AIRequest) -> AIResponse:
        self.requests.append(request)
        if self.raises is not None:
            raise self.raises
        assert self.response is not None
        return self.response

    def health(self):  # pragma: no cover - protocol method unused
        raise NotImplementedError

    def list_models(self):  # pragma: no cover - protocol method unused
        raise NotImplementedError

    def stream(self, request: AIRequest):  # pragma: no cover - protocol method unused
        raise NotImplementedError


def _bootstrap(monkeypatch) -> None:
    initialize_database()
    ensure_ai_settings()
    update_ai_settings(
        AISettingsUpdate(
            policy_mode="FAST_DEV",
            monthly_api_budget_usd=100,
            paid_ai_enabled=True,
            provider_mode="deepseek",
        )
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only-secret")
    monkeypatch.setenv("GLM_API_KEY", "test-only-secret")


def _pending_ticket(monkeypatch, *, route_class: str = "external:cheap") -> str:
    _bootstrap(monkeypatch)
    if route_class == "external:cheap":
        provider_id = "deepseek"
        model_id = "deepseek-v4-pro"
        fallback_index = 0
    else:
        provider_id = "glm"
        model_id = "glm-5.2"
        fallback_index = 0
    preparation = prepare_egress_attempt(
        EgressPacketMaterial(
            operation=EXTERNAL_PROVIDER_OPERATION,
            task_kind="general",
            route_class=route_class,
            provider_id=provider_id,
            model_id=model_id,
            fallback_index=fallback_index,
            prompt="Explain a generic pump sizing method.",
            context_blocks=(),
            prompt_level="S1",
            context_level="S0",
            final_level="S1",
            max_output_tokens=64,
        )
    )
    assert preparation.ticket_id is not None
    return preparation.ticket_id


def _success_response(provider_id: str = "deepseek", model_id: str = "deepseek-v4-pro") -> AIResponse:
    return AIResponse(
        provider_id=provider_id,
        model_id=model_id,
        request_id="test-request",
        text="confirmed answer",
        content="confirmed answer",
        usage=AIUsage(
            provider_id=provider_id,
            model_id=model_id,
            input_tokens=11,
            output_tokens=7,
            provider_cost_estimate=0.001,
        ),
        safety_status="allowed",
    )


def test_confirmation_request_accepts_only_ticket_id() -> None:
    request = EscalationConfirmRequest.model_validate({"ticket_id": "ticket-1"})
    assert request.ticket_id == "ticket-1"
    for payload in (
        {"proposal": {"outbound_text": "client-owned"}},
        {"ticket_id": "ticket-1", "task_kind": "general"},
        {"ticket_id": "ticket-1", "outbound_text": "replacement"},
    ):
        with pytest.raises(ValidationError):
            EscalationConfirmRequest.model_validate(payload)


def test_ticket_confirmation_executes_exact_binding_once(monkeypatch) -> None:
    ticket_id = _pending_ticket(monkeypatch)
    adapter = _Adapter("deepseek", response=_success_response())

    confirmed = run_confirmation_ticket(
        ticket_id,
        adapters={"deepseek": adapter},
    )

    outcome = confirmed.outcome
    assert outcome.status == "success"
    assert outcome.response is not None
    assert outcome.response.text == "confirmed answer"
    assert outcome.egress_ticket_id == ticket_id
    assert outcome.egress_reason_code == "ticket_consumed"
    assert outcome.egress_trigger_ids == ("t1",)
    assert len(adapter.requests) == 1
    request = adapter.requests[0]
    assert request.prompt == "Explain a generic pump sizing method."
    assert request.model_preference == "deepseek-v4-pro"
    assert request.max_output_tokens == 64
    with open_sqlite_connection() as connection:
        job = connection.execute(
            "SELECT status, provider_id, model_id FROM ai_jobs WHERE id = ?",
            (outcome.ledger_id,),
        ).fetchone()
        attempt = connection.execute(
            "SELECT network_attempt, provider_id, model_id, fallback_index FROM egress_attempts"
        ).fetchone()
        reservation = connection.execute(
            "SELECT state FROM egress_budget_reservations WHERE id = ?",
            (outcome.egress_reservation_id,),
        ).fetchone()
    assert tuple(job) == ("success", "deepseek", "deepseek-v4-pro")
    assert tuple(attempt) == (1, "deepseek", "deepseek-v4-pro", 0)
    assert reservation["state"] == "reconciled"


def test_ticket_confirmation_is_one_shot_and_second_call_makes_no_provider_call(monkeypatch) -> None:
    ticket_id = _pending_ticket(monkeypatch)
    first = _Adapter("deepseek", response=_success_response())
    run_confirmation_ticket(ticket_id, adapters={"deepseek": first})
    second = _Adapter("deepseek", response=_success_response())

    with pytest.raises(EgressStateError, match="not pending: consumed"):
        run_confirmation_ticket(ticket_id, adapters={"deepseek": second})

    assert len(first.requests) == 1
    assert second.requests == []
    with open_sqlite_connection() as connection:
        attempts = connection.execute("SELECT COUNT(*) AS count FROM egress_attempts").fetchone()["count"]
    assert attempts == 1


def test_gate_change_after_consumption_releases_without_network(monkeypatch) -> None:
    ticket_id = _pending_ticket(monkeypatch)
    import app.modules.ai.egress_confirmation as confirmation
    from app.modules.ai.budget import ProviderBudgetGate

    monkeypatch.setattr(
        confirmation,
        "evaluate_provider_budget_gate",
        lambda settings, provider_id: ProviderBudgetGate(False, "gate_closed_after_ticket", provider_id),
    )
    adapter = _Adapter("deepseek", response=_success_response())

    outcome = run_confirmation_ticket(ticket_id, adapters={"deepseek": adapter}).outcome

    assert outcome.status == "config_error"
    assert outcome.decision.blocked_reason == "gate_closed_after_ticket"
    assert adapter.requests == []
    with open_sqlite_connection() as connection:
        reservation = connection.execute(
            "SELECT state, reconciliation_status FROM egress_budget_reservations WHERE id = ?",
            (outcome.egress_reservation_id,),
        ).fetchone()
        attempt = connection.execute(
            "SELECT network_attempt, actual_input_tokens, actual_output_tokens, actual_cost_usd FROM egress_attempts"
        ).fetchone()
    assert tuple(reservation) == ("released", "not_sent")
    assert tuple(attempt) == (0, 0, 0, 0.0)


def test_retryable_confirmed_error_does_not_open_fallback(monkeypatch) -> None:
    ticket_id = _pending_ticket(monkeypatch)
    retryable = AIResponse(
        provider_id="deepseek",
        model_id="deepseek-v4-pro",
        request_id="test-request",
        usage=AIUsage(provider_id="deepseek", model_id="deepseek-v4-pro"),
        safety_status="blocked",
        blocked_reason="provider_failed",
        error=AIProviderError(
            code=AIProviderErrorCode.provider_timeout,
            message="timeout",
            retryable=True,
        ),
    )
    deepseek = _Adapter("deepseek", response=retryable)
    glm = _Adapter("glm", response=_success_response("glm", "glm-5.2"))

    outcome = run_confirmation_ticket(
        ticket_id,
        adapters={"deepseek": deepseek, "glm": glm},
    ).outcome

    assert outcome.status == "provider_error"
    assert len(deepseek.requests) == 1
    assert glm.requests == []
    with open_sqlite_connection() as connection:
        providers = [
            row["provider_id"]
            for row in connection.execute("SELECT provider_id FROM egress_attempts ORDER BY created_at")
        ]
    assert providers == ["deepseek"]


def test_response_binding_mismatch_is_reconciled_as_network_attempt(monkeypatch) -> None:
    ticket_id = _pending_ticket(monkeypatch)
    adapter = _Adapter("deepseek", response=_success_response("glm", "glm-5.2"))

    outcome = run_confirmation_ticket(ticket_id, adapters={"deepseek": adapter}).outcome

    assert outcome.status == "provider_error"
    assert outcome.egress_reason_code == "response_binding_mismatch"
    assert len(adapter.requests) == 1
    with open_sqlite_connection() as connection:
        job = connection.execute(
            "SELECT status, error_type FROM ai_jobs WHERE id = ?",
            (outcome.ledger_id,),
        ).fetchone()
        attempt = connection.execute(
            "SELECT network_attempt, reconciliation_status FROM egress_attempts"
        ).fetchone()
    assert job["status"] == "provider_error"
    assert job["error_type"] == "EgressSpineStateError"
    assert attempt["network_attempt"] == 1
    assert attempt["reconciliation_status"] == "conservative_missing_usage"
