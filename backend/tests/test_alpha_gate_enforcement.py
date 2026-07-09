from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.core.bootstrap import initialize_storage
from app.modules.ai.alpha_gate import evaluate_alpha_execution_gate
from app.modules.ai.settings import get_ai_settings
from app.modules.bluecad.models import BluecadCandidateCreate


@pytest.fixture
def client() -> Iterator[TestClient]:
    initialize_storage(seed_default=True)
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


def test_side_effectful_external_request_denied_when_alpha_gate_closed() -> None:
    initialize_storage(seed_default=True)
    from app.modules.bluecad import loop

    side_effect = Mock(side_effect=AssertionError("provider side effect must not run"))
    original = loop.run_ai_task
    loop.run_ai_task = side_effect
    try:
        candidate = loop.create_bluecad_candidate("bluerev", BluecadCandidateCreate(brief_text="make a tube"))
    finally:
        loop.run_ai_task = original

    assert candidate.status == "parked"
    assert candidate.parked_reason == "budget_blocked"
    assert "external_blocked_reason=" in (candidate.notes or "")
    side_effect.assert_not_called()


def test_payload_fields_cannot_self_authorize_alpha_execution(client) -> None:
    side_effect = Mock(side_effect=AssertionError("provider side effect must not run"))
    from app.modules.bluecad import loop

    original = loop.run_ai_task
    loop.run_ai_task = side_effect
    try:
        response = client.post(
            "/workspaces/bluerev/bluecad/candidates",
            json={
                "brief_text": "make a tube",
                "alpha": True,
                "confirmed": True,
                "mode": "execute",
                "dry_run": False,
            },
        )
    finally:
        loop.run_ai_task = original

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "parked"
    assert body["parked_reason"] == "budget_blocked"
    side_effect.assert_not_called()


def test_missing_alpha_gate_context_fails_closed() -> None:
    decision = evaluate_alpha_execution_gate(
        settings=None,
        provider_mode="scaleway",
        operation="test_missing_context",
        side_effectful=True,
    )

    assert decision.allowed is False
    assert decision.reason == "alpha_gate_missing_context:test_missing_context"


def test_gate_evaluation_happens_before_side_effect_stub() -> None:
    initialize_storage(seed_default=True)
    from app.modules.bluecad import loop

    side_effect = Mock(side_effect=AssertionError("side effect happened before alpha gate denied"))
    original = loop.run_ai_task
    loop.run_ai_task = side_effect
    try:
        candidate = loop.create_bluecad_candidate("bluerev", BluecadCandidateCreate(brief_text="make a tube"))
    finally:
        loop.run_ai_task = original

    assert candidate.status == "parked"
    side_effect.assert_not_called()


def test_safe_read_only_alpha_gate_path_is_allowed() -> None:
    initialize_storage(seed_default=True)
    decision = evaluate_alpha_execution_gate(
        settings=get_ai_settings(),
        provider_mode=None,
        operation="list_candidates",
        side_effectful=False,
    )

    assert decision.allowed is True
    assert decision.reason == "alpha_gate_safe_read_only"
