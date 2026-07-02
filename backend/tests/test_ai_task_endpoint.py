from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


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


def test_task_endpoint_local_fake_uses_run_ai_task_and_writes_one_ai_job(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.modules.ai.execution as execution

    real_run_ai_task = execution.run_ai_task
    calls: list[dict[str, object]] = []

    def spy_run_ai_task(**kwargs):
        calls.append(kwargs)
        return real_run_ai_task(**kwargs)

    monkeypatch.setattr(execution, "run_ai_task", spy_run_ai_task)

    response = client.post(
        "/ai/tasks/run",
        json={
            "prompt": "POS-1B fake endpoint smoke",
            "route_class": "local:fake",
            "task_kind": "general",
            "max_tokens": 64,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["include_project_context"] is False
    assert body["workspace_id"] is None
    assert body["context_digest"] is None
    assert body["context_sources_count"] == 0
    assert body["ledger_id"]
    assert body["selected_route_class"] == "local:fake"
    assert body["response_text"].startswith("[fake:")
    assert body["provider_id"] == "fake"
    assert body["model_id"] == "fake-deterministic-v1"
    assert body["usage"]["input_tokens"] > 0
    assert body["usage"]["output_tokens"] > 0
    assert len(calls) == 1
    assert calls[0]["route_class"] == "local:fake"

    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["id"] == body["ledger_id"]
    assert rows[0]["status"] == "success"
    assert rows[0]["selected_route_class"] == "local:fake"


def test_task_endpoint_defaults_to_safe_local_fake_route(client: TestClient) -> None:
    response = client.post(
        "/ai/tasks/run",
        json={"prompt": "default route must stay local even for synthesis", "task_kind": "synthesis"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["include_project_context"] is False
    assert body["workspace_id"] is None
    assert body["context_digest"] is None
    assert body["context_sources_count"] == 0
    assert body["selected_route_class"] == "local:fake"

    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["selected_route_class"] == "local:fake"


def test_task_endpoint_unbound_route_fails_closed_and_writes_one_ai_job(client: TestClient) -> None:
    response = client.post(
        "/ai/tasks/run",
        json={"prompt": "unbound route", "route_class": "external:not_bound", "max_tokens": 64},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "route_unavailable"
    assert body["selected_route_class"] == "external:not_bound"
    assert body["blocked_reason"] == "route_unavailable"
    assert body["error_type"] == "route_unavailable"
    assert body["response_text"] is None
    assert body["provider_id"] is None
    assert body["model_id"] is None

    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["id"] == body["ledger_id"]
    assert rows[0]["status"] == "route_unavailable"


def test_task_endpoint_malformed_route_fails_closed_and_writes_one_ai_job(client: TestClient) -> None:
    response = client.post(
        "/ai/tasks/run",
        json={"prompt": "malformed route", "route_class": "external reasoning", "max_tokens": 64},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "validation_error"
    assert body["selected_route_class"] == "external reasoning"
    assert body["blocked_reason"] == "route_class_malformed"
    assert body["error_type"] == "validation_error"
    assert body["response_text"] is None

    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["id"] == body["ledger_id"]
    assert rows[0]["status"] == "validation_error"


def test_task_endpoint_external_route_requires_max_tokens_before_provider_call(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SCALEWAY_API_KEY", "test-only-key")
    settings_response = client.put(
        "/ai/settings",
        json={
            "provider_mode": "scaleway",
            "default_ai_provider": "scaleway",
            "paid_ai_enabled": True,
            "monthly_api_budget_usd": 1,
            "scaleway_enabled": True,
            "scaleway_smoke_test_enabled": True,
            "scaleway_live_smoke_test_enabled": True,
            "use_fake_provider_when_budget_zero": False,
        },
    )
    assert settings_response.status_code == 200

    from app.modules.ai.contracts import AIRequest, AIResponse
    from app.modules.ai.providers.scaleway_adapter import ScalewayProviderAdapter

    def fail(self: ScalewayProviderAdapter, request: AIRequest) -> AIResponse:
        raise AssertionError("external task endpoint must require max_tokens before provider call")

    monkeypatch.setattr(ScalewayProviderAdapter, "complete", fail)

    response = client.post(
        "/ai/tasks/run",
        json={"prompt": "external route without explicit max", "route_class": "external:cheap"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "config_error"
    assert body["selected_route_class"] == "external:cheap"
    assert body["provider_id"] == "scaleway"
    assert body["model_id"] == "llama-3.1-8b-instruct"
    assert body["blocked_reason"] == "config_error"
    assert body["decision_reason"] == "max_output_tokens required for network route"
    assert body["error_type"] == "config_error"
    assert body["response_text"] is None

    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["id"] == body["ledger_id"]
    assert rows[0]["status"] == "config_error"
    assert rows[0]["provider_id"] == "scaleway"
    assert rows[0]["error_type"] == "config_error"


def test_task_endpoint_external_route_respects_ai_settings_gate_before_provider_call(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SCALEWAY_API_KEY", "test-only-key")

    from app.modules.ai.contracts import AIRequest, AIResponse
    from app.modules.ai.providers.scaleway_adapter import ScalewayProviderAdapter

    def fail(self: ScalewayProviderAdapter, request: AIRequest) -> AIResponse:
        raise AssertionError("external task endpoint must respect settings gate before provider call")

    monkeypatch.setattr(ScalewayProviderAdapter, "complete", fail)

    response = client.post(
        "/ai/tasks/run",
        json={"prompt": "settings disabled external route", "route_class": "external:cheap", "max_tokens": 64},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "config_error"
    assert body["selected_route_class"] == "external:cheap"
    assert body["provider_id"] == "scaleway"
    assert body["model_id"] == "llama-3.1-8b-instruct"
    assert body["blocked_reason"] == "config_error"
    assert body["error_type"] == "config_error"
    assert "external provider execution disabled by settings/gate" in body["decision_reason"]
    assert "scaleway_disabled" in body["decision_reason"]
    assert body["response_text"] is None

    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["id"] == body["ledger_id"]
    assert rows[0]["status"] == "config_error"
    assert rows[0]["provider_id"] == "scaleway"
    assert rows[0]["error_type"] == "config_error"


def test_task_endpoint_rejects_too_many_context_blocks(client: TestClient) -> None:
    response = client.post(
        "/ai/tasks/run",
        json={
            "prompt": "too many context blocks",
            "route_class": "local:fake",
            "context_blocks": [{"content": str(index)} for index in range(21)],
        },
    )

    assert response.status_code == 422
    assert _all_ai_jobs() == []


def test_task_endpoint_rejects_oversized_context_blocks(client: TestClient) -> None:
    response = client.post(
        "/ai/tasks/run",
        json={
            "prompt": "too large context",
            "route_class": "local:fake",
            "context_blocks": [{"content": "x" * 32_001}],
        },
    )

    assert response.status_code == 422
    assert _all_ai_jobs() == []


def test_task_endpoint_accepts_small_context_blocks_for_local_fake(client: TestClient) -> None:
    response = client.post(
        "/ai/tasks/run",
        json={
            "prompt": "small context",
            "route_class": "local:fake",
            "context_blocks": [{"source": "manual", "content": "small context"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["include_project_context"] is False
    assert body["workspace_id"] is None
    assert body["context_digest"] is not None
    assert body["context_sources_count"] >= 1
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["context_digest"].startswith("sha256:")


def test_task_endpoint_without_project_context_records_no_sources(client: TestClient) -> None:
    response = client.post(
        "/ai/tasks/run",
        json={"prompt": "no project context", "route_class": "local:fake"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["include_project_context"] is False
    assert body["workspace_id"] is None
    assert body["context_digest"] is None
    assert body["context_sources_count"] == 0
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["context_sources_json"] is None


def test_task_endpoint_include_project_context_injects_workspace_context(client: TestClient) -> None:
    import json

    from app.modules.modeling.models import DecisionCreate, ParameterCreate
    from app.modules.modeling.service import create_decision, create_parameter

    create_decision("bluerev", DecisionCreate(title="Provider", decision_text="Scaleway EU first", status="accepted"))
    create_parameter(
        "bluerev",
        ParameterCreate(name="tube_diameter", value="0.05", unit="m", source_ref="spec-1", status="approved"),
    )

    response = client.post(
        "/ai/tasks/run",
        json={
            "prompt": "what do you know about the project?",
            "route_class": "local:fake",
            "include_project_context": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["include_project_context"] is True
    assert body["workspace_id"] == "bluerev"
    assert body["context_digest"] is not None
    assert body["context_sources_count"] >= 2

    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["context_digest"] is not None
    sources = json.loads(rows[0]["context_sources_json"])
    assert any(source["type"] == "decision" for source in sources)
    assert any(source["type"] == "parameter" for source in sources)


def test_task_endpoint_invalid_workspace_fails_closed_before_provider(client: TestClient) -> None:
    response = client.post(
        "/ai/tasks/run",
        json={
            "prompt": "context from a missing workspace",
            "route_class": "local:fake",
            "include_project_context": True,
            "workspace_id": "does-not-exist",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "config_error"
    assert body["error_type"] == "context_build_error"
    assert body["include_project_context"] is True
    assert body["workspace_id"] == "does-not-exist"
    assert body["context_digest"] is None
    assert body["context_sources_count"] == 0
    assert body["response_text"] is None

    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "config_error"
    assert rows[0]["error_type"] == "context_build_error"


def _proposal() -> dict[str, object]:
    return {
        "proposal_ledger_id": "proposal-1",
        "proposed_route_class": "external:reasoning",
        "provider_id": "scaleway",
        "model_id": "qwen3-235b-a22b-instruct-2507",
        "estimated_cost": {"max_output_tokens": 64, "estimated_cost_usd": 0.0001, "currency": "USD"},
        "outbound_text": "confirm raw prompt",
        "context_excluded": True,
    }


def test_confirm_escalation_happy_path_uses_external_spine(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCALEWAY_API_KEY", "test-only-key")
    client.put(
        "/ai/settings",
        json={
            "provider_mode": "scaleway",
            "default_ai_provider": "scaleway",
            "paid_ai_enabled": True,
            "monthly_api_budget_usd": 1,
            "scaleway_enabled": True,
            "scaleway_smoke_test_enabled": True,
            "scaleway_live_smoke_test_enabled": True,
            "use_fake_provider_when_budget_zero": False,
        },
    )
    from app.modules.ai.contracts import AIRequest
    from app.modules.ai.providers.fake_adapter import FakeProviderAdapter
    from app.modules.ai.providers.scaleway_adapter import ScalewayProviderAdapter

    seen: list[str | None] = []

    def fake_complete(self: ScalewayProviderAdapter, request: AIRequest):
        seen.append(request.prompt)
        return FakeProviderAdapter().complete(request)

    monkeypatch.setattr(ScalewayProviderAdapter, "complete", fake_complete)
    monkeypatch.setattr("app.modules.ai.execution._scaleway_ready", lambda: True)

    response = client.post("/ai/tasks/escalations/confirm", json={"proposal": _proposal(), "task_kind": "general"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["proposal_ledger_id"] == "proposal-1"
    assert body["task_response"]["selected_route_class"] == "external:reasoning"
    assert seen == ["confirm raw prompt"]
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "success"
    assert rows[0]["context_digest"] is None


def test_confirm_escalation_paid_ai_disabled_fails_closed(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCALEWAY_API_KEY", "test-only-key")
    from app.modules.ai.providers.scaleway_adapter import ScalewayProviderAdapter

    def fail(self, request):
        raise AssertionError("provider must not be called")

    monkeypatch.setattr(ScalewayProviderAdapter, "complete", fail)
    client.put(
        "/ai/settings",
        json={
            "provider_mode": "scaleway",
            "default_ai_provider": "scaleway",
            "paid_ai_enabled": False,
            "monthly_api_budget_usd": 1,
            "scaleway_enabled": True,
            "scaleway_smoke_test_enabled": True,
            "scaleway_live_smoke_test_enabled": True,
            "use_fake_provider_when_budget_zero": False,
        },
    )
    response = client.post("/ai/tasks/escalations/confirm", json={"proposal": _proposal()})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "config_error"
    assert "paid_ai_disabled" in body["task_response"]["decision_reason"]


def test_confirm_escalation_budget_zero_fails_closed(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCALEWAY_API_KEY", "test-only-key")
    client.put(
        "/ai/settings",
        json={
            "provider_mode": "scaleway",
            "default_ai_provider": "scaleway",
            "paid_ai_enabled": True,
            "monthly_api_budget_usd": 0,
            "scaleway_enabled": True,
            "scaleway_smoke_test_enabled": True,
            "scaleway_live_smoke_test_enabled": True,
            "use_fake_provider_when_budget_zero": False,
        },
    )
    response = client.post("/ai/tasks/escalations/confirm", json={"proposal": _proposal()})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "config_error"
    assert "monthly_budget_zero" in body["task_response"]["decision_reason"]
