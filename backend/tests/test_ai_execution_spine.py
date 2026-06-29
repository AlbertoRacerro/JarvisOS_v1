"""POS-1 — positive AI execution spine. Fake/offline only; no network, no secrets."""

from __future__ import annotations

import json

from app.modules.ai.contracts import (
    AIRequest,
    AIResponse,
    AIUsage,
)


def _isolate_and_init(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "jarvisos-aijobs"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.database import initialize_database

    initialize_database()


def _all_ai_jobs() -> list[dict]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute("SELECT * FROM ai_jobs ORDER BY created_at ASC").fetchall()
    return [dict(row) for row in rows]


class _RaisingAdapter:
    provider_id = "fake"

    def health(self):  # pragma: no cover - not used
        ...

    def list_models(self):  # pragma: no cover - not used
        return []

    def complete(self, request: AIRequest) -> AIResponse:
        raise RuntimeError("boom from provider")

    def stream(self, request: AIRequest):  # pragma: no cover - not used
        raise NotImplementedError


def _stub_scaleway_adapter(captured_text: str = "stub cloud answer"):
    class _StubScaleway:
        provider_id = "scaleway"

        def health(self):  # pragma: no cover - not used
            ...

        def list_models(self):  # pragma: no cover - not used
            return []

        def complete(self, request: AIRequest) -> AIResponse:
            return AIResponse(
                provider_id="scaleway",
                model_id=request.model_preference or "stub-model",
                request_id=request.request_id,
                text=captured_text,
                content=captured_text,
                usage=AIUsage(provider_id="scaleway", model_id="stub-model", input_tokens=3, output_tokens=4),
                safety_status="allowed",
            )

        def stream(self, request: AIRequest):  # pragma: no cover - not used
            raise NotImplementedError

    return _StubScaleway()


def test_fake_route_executes_and_writes_ai_job(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="explain a pump", route_class="local:fake")

    assert outcome.status == "success"
    assert outcome.response is not None
    assert outcome.response.text is not None
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "success"
    assert rows[0]["provider_id"] == "fake"
    assert rows[0]["selected_route_class"] == "local:fake"
    assert rows[0]["prompt_digest"].startswith("sha256:")
    assert rows[0]["output_digest"].startswith("sha256:")


def test_malformed_route_fails_closed_and_records(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="x", route_class="external reasoning")

    assert outcome.status == "validation_error"
    assert outcome.response is None
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "validation_error"
    assert rows[0]["provider_id"] is None


def test_unbound_route_fails_closed_and_records(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="x", route_class="external:vision")

    assert outcome.status == "route_unavailable"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "route_unavailable"
    assert "no binding configured" in json.loads(rows[0]["route_reason_json"])["decision_reason"]


def test_missing_provider_credentials_fails_closed_and_records(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    monkeypatch.delenv("SCALEWAY_API_KEY", raising=False)
    monkeypatch.setattr("app.modules.ai.execution._scaleway_ready", lambda: False)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="real work", route_class="external:cheap")

    assert outcome.status == "config_error"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "config_error"
    assert rows[0]["provider_id"] == "scaleway"
    assert rows[0]["error_type"] == "config_error"


def test_synthesis_task_kind_defaults_to_local_fake(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="summarize safely", task_kind="synthesis")

    assert outcome.status == "success"
    assert outcome.selected_route_class == "local:fake"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["selected_route_class"] == "local:fake"
    assert rows[0]["provider_id"] == "fake"


def test_success_writes_exactly_one_row(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    run_ai_task(user_prompt="one", route_class="local:fake")
    run_ai_task(user_prompt="two", route_class="local:fake")

    rows = _all_ai_jobs()
    assert len(rows) == 2
    assert all(row["status"] == "success" for row in rows)


def test_provider_error_records_one_row(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(
        user_prompt="will fail",
        route_class="local:fake",
        adapters={"fake": _RaisingAdapter()},
    )

    assert outcome.status == "provider_error"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "provider_error"
    assert rows[0]["error_type"] == "RuntimeError"


def test_api_key_value_absent_from_ledger(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    secret = "sk-scaleway-supersecret-998877"
    monkeypatch.setenv("SCALEWAY_API_KEY", secret)
    from app.modules.ai.execution import run_ai_task

    # Stub Scaleway adapter so no real network; key is set in env but must never
    # land in the ledger.
    outcome = run_ai_task(
        user_prompt="route through cloud binding",
        route_class="external:cheap",
        max_output_tokens=64,
        adapters={"scaleway": _stub_scaleway_adapter()},
    )

    assert outcome.status == "success"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    serialized = json.dumps(rows[0])
    assert secret not in serialized


def test_fake_path_does_not_touch_network(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)

    def _boom(*args, **kwargs):
        raise AssertionError("no network call allowed in tests")

    monkeypatch.setattr("httpx.post", _boom)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="offline", route_class="local:fake")
    assert outcome.status == "success"


def test_prompt_and_context_digests_are_stable(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    context = [{"source": "manual", "content": "JarvisOS positive cloud path"}]
    run_ai_task(user_prompt="same", route_class="local:fake", context_blocks=context)
    run_ai_task(user_prompt="same", route_class="local:fake", context_blocks=context)

    rows = _all_ai_jobs()
    assert rows[0]["prompt_digest"] == rows[1]["prompt_digest"]
    assert rows[0]["context_digest"] == rows[1]["context_digest"]
    assert rows[0]["context_digest"] is not None
