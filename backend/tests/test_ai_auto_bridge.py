from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.modules.ai.contracts import AIResponse, AIUsage, AIUsageSource, RoutingDecision
from app.modules.ai.execution import AiTaskOutcome
from app.modules.ai.models import AITaskRunRequest
from app.modules.ai.routing.bridge import (
    auto_local_route_class_for_task,
    build_auto_router_input,
    resolve_bridge_outcome_from_decision,
)
from app.modules.ai.routing.safe_local import is_safe_local_execution

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.delenv("SCALEWAY_API_KEY", raising=False)
    monkeypatch.delenv("SCALEWAY_BASE_URL", raising=False)
    monkeypatch.delenv("SCALEWAY_MODEL", raising=False)

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)

    with TestClient(create_app()) as test_client:
        yield test_client

    get_settings.cache_clear()


def _all_ai_jobs() -> list[dict[str, object]]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute("SELECT * FROM ai_jobs ORDER BY created_at ASC").fetchall()
    return [dict(row) for row in rows]


def _safe_decision(**overrides) -> dict:
    decision = {
        "route_action": "answer_local",
        "route_tier": "LOCAL_FAST",
        "provider_candidate": "local:qwen",
        "response_allowed_now": True,
        "external_allowed": False,
        "provider_call_allowed_now": False,
        "external_network_allowed_now": False,
        "tool_execution_allowed_now": False,
        "state_change_allowed_now": False,
        "allowed_execution_mode": "answer_only",
        "modifies_state": False,
        "side_effect_level": "none",
        "environment_type": "chat",
        "proposed_external_target": None,
    }
    decision.update(overrides)
    return decision


def _fake_success_outcome(route_class: str) -> AiTaskOutcome:
    response = AIResponse(
        provider_id="fake-runner",
        model_id="fake-runner-model",
        request_id="test-request",
        text=f"fake auto response for {route_class}",
        usage=AIUsage(
            provider_id="fake-runner",
            model_id="fake-runner-model",
            input_tokens=1,
            output_tokens=1,
            usage_source=AIUsageSource.estimated,
        ),
    )
    return AiTaskOutcome(
        status="success",
        ledger_id=f"ledger-{route_class}",
        selected_route_class=route_class,
        decision=RoutingDecision(
            provider_id="fake-runner",
            model_id="fake-runner-model",
            decision_reason=f"test:{route_class}",
        ),
        response=response,
    )


def test_backend_safe_local_predicate_matches_script_predicate() -> None:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    from router_policy_local_route_probe import is_safe_local_execution as script_is_safe_local_execution

    decisions = [
        _safe_decision(),
        _safe_decision(route_action="route_local"),
        _safe_decision(provider_call_allowed_now=True),
        _safe_decision(external_network_allowed_now=True),
        _safe_decision(proposed_external_target="external:scientific_medium"),
        _safe_decision(allowed_execution_mode="propose_only"),
    ]

    for decision in decisions:
        assert is_safe_local_execution(decision) is script_is_safe_local_execution(decision)


def test_safe_local_execution_keeps_provider_call_permission_false() -> None:
    decision = _safe_decision(provider_call_allowed_now=False, external_network_allowed_now=False)

    assert is_safe_local_execution(decision) is True


def test_task_endpoint_auto_executes_safe_local_through_injected_runner(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.modules.ai.execution as execution

    calls: list[dict[str, object]] = []

    def fake_run_ai_task(**kwargs):
        calls.append(kwargs)
        return _fake_success_outcome(str(kwargs["route_class"]))

    monkeypatch.setattr(execution, "run_ai_task", fake_run_ai_task)

    response = client.post(
        "/ai/tasks/run",
        json={"prompt": "review this code locally", "route_class": "auto", "task_kind": "code_review", "max_tokens": 64},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["selected_route_class"] == "local:coder"
    assert body["provider_id"] == "fake-runner"
    assert body["model_id"] == "fake-runner-model"
    assert body["response_text"] == "fake auto response for local:coder"
    assert len(calls) == 1
    assert calls[0]["route_class"] == "local:coder"


@pytest.mark.parametrize(
    ("task_kind", "expected_route_class"),
    [
        ("general", "local:fast"),
        ("test", "local:fast"),
        ("synthesis", "local:general"),
        ("decision_support", "local:general"),
        ("code_review", "local:coder"),
        ("architecture_review", "local:coder_heavy"),
        ("unknown", "local:fast"),
    ],
)
def test_auto_local_subselector_maps_task_kind_to_real_local_route(task_kind: str, expected_route_class: str) -> None:
    request = AITaskRunRequest(prompt="local task", route_class="auto", task_kind=task_kind, max_tokens=64)
    calls: list[dict[str, object]] = []

    def fake_run_ai_task(**kwargs):
        calls.append(kwargs)
        return _fake_success_outcome(str(kwargs["route_class"]))

    response = resolve_bridge_outcome_from_decision(
        request=request,
        decision=_safe_decision(),
        run_ai_task_func=fake_run_ai_task,
    )

    assert auto_local_route_class_for_task(task_kind) == expected_route_class
    assert response.status == "success"
    assert response.selected_route_class == expected_route_class
    assert calls[0]["route_class"] == expected_route_class


def test_auto_builder_uses_internal_or_unknown_sensitivity_without_claiming_public() -> None:
    without_context = build_auto_router_input(AITaskRunRequest(prompt="local task", route_class="auto"))
    with_context = build_auto_router_input(
        AITaskRunRequest(prompt="local task", route_class="auto", include_project_context=True)
    )

    assert without_context["phase_a_signals"]["sensitivity_bucket_proposal"] == "unknown"
    assert with_context["phase_a_signals"]["sensitivity_bucket_proposal"] == "internal"


def test_task_endpoint_explicit_route_bypasses_auto_bridge(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.ai.routing import bridge

    def fail_auto_builder(*args, **kwargs):
        raise AssertionError("explicit route must not use auto bridge")

    monkeypatch.setattr(bridge, "build_auto_decision", fail_auto_builder)

    response = client.post(
        "/ai/tasks/run",
        json={"prompt": "explicit fake route", "route_class": "local:fake", "task_kind": "general"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["selected_route_class"] == "local:fake"


def test_auto_resolver_refuses_injected_external_candidate_without_run_ai_task(client: TestClient) -> None:
    request = AITaskRunRequest(prompt="should not execute external", route_class="auto", max_tokens=64)
    external_decision = _safe_decision(
        route_action="route_external_candidate",
        route_tier="SCIENTIFIC_MEDIUM",
        provider_candidate="external:scientific_medium",
        proposed_external_target="external:scientific_medium",
        allowed_execution_mode="propose_only",
        reason_codes=["adversarial_external_candidate"],
    )
    calls = {"run_ai_task": 0}

    def fail_run_ai_task(**kwargs):
        calls["run_ai_task"] += 1
        raise AssertionError("Auto resolver must not execute external proposals")

    response = resolve_bridge_outcome_from_decision(
        request=request,
        decision=external_decision,
        run_ai_task_func=fail_run_ai_task,
    )

    assert response.status == "proposed_external"
    assert response.selected_route_class == "auto"
    assert response.provider_id is None
    assert response.model_id is None
    assert response.response_text is None
    assert response.blocked_reason == "auto_external_proposal_refused"
    assert calls["run_ai_task"] == 0

    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["id"] == response.ledger_id
    assert rows[0]["status"] == "proposed_external"
    assert rows[0]["provider_id"] is None
    assert rows[0]["model_id"] is None
    reason = json.loads(rows[0]["route_reason_json"])
    assert reason["route_action"] == "route_external_candidate"
    assert reason["permissions"]["external_network_allowed_now"] is False


def test_auto_resolver_records_control_state_without_run_ai_task(client: TestClient) -> None:
    request = AITaskRunRequest(prompt="needs confirmation", route_class="auto", max_tokens=64)
    decision = _safe_decision(
        route_action="ask_user_confirm",
        route_tier="USER_CONFIRM",
        provider_candidate="none",
        allowed_execution_mode="propose_only",
        response_allowed_now=True,
        reason_codes=["manual_review_required"],
    )
    calls = {"run_ai_task": 0}

    def fail_run_ai_task(**kwargs):
        calls["run_ai_task"] += 1
        raise AssertionError("control states must not call run_ai_task")

    response = resolve_bridge_outcome_from_decision(
        request=request,
        decision=decision,
        run_ai_task_func=fail_run_ai_task,
    )

    assert response.status == "needs_confirmation"
    assert response.selected_route_class == "auto"
    assert response.provider_id is None
    assert response.model_id is None
    assert response.response_text is None
    assert calls["run_ai_task"] == 0

    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "needs_confirmation"
    assert rows[0]["input_tokens"] is None
    assert rows[0]["output_tokens"] is None
