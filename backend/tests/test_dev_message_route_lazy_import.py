"""Stage 1 regression: disabled dev-route startup must not import router_policy_* scripts."""

from __future__ import annotations

import sys

import pytest
from fastapi.testclient import TestClient

_SCRIPT_MODULE_NAMES = (
    "router_policy_message_route_smoke",
    "router_policy_local_route_probe",
    "router_policy_local_responder",
)


def _purge_script_state() -> None:
    """Remove router_policy_* from sys.modules and from smoke_adapter's lazy cache.

    Other tests in the session may have loaded these modules. This function resets
    the state so the lazy-import assertion is meaningful regardless of test order.
    """
    from app.modules.dev_message_route import smoke_adapter

    for mod_name in _SCRIPT_MODULE_NAMES:
        sys.modules.pop(mod_name, None)

    for attr in smoke_adapter._SCRIPT_ATTRS:
        smoke_adapter.__dict__.pop(attr, None)


def test_disabled_startup_does_not_import_router_policy_scripts(monkeypatch) -> None:
    """With dev smoke disabled, app creation and /health must not load router_policy_*."""
    _purge_script_state()

    monkeypatch.delenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", raising=False)

    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200

    for mod_name in _SCRIPT_MODULE_NAMES:
        assert mod_name not in sys.modules, (
            f"{mod_name} was imported during disabled dev-smoke startup"
        )


def test_disabled_route_returns_404_with_expected_body(monkeypatch, tmp_path) -> None:
    """Disabled-mode HTTP behavior is preserved after the lazy-import refactor."""
    monkeypatch.delenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", raising=False)

    from app.core.config import get_settings
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    get_settings.cache_clear()
    initialize_storage(seed_default=True)

    with TestClient(create_app()) as client:
        response = client.post(
            "/api/dev/message-route-smoke",
            json={"message": "Explain what a pump is."},
        )

    get_settings.cache_clear()

    assert response.status_code == 404
    body = response.json()
    assert isinstance(body["trace_id"], str)
    assert body["audit_ref"] is None
    assert body["executed"] is False
    assert body["reason"] == "dev_message_route_smoke_disabled"
    assert "input_obj" not in body
    assert "decision" not in body


def test_enabled_path_reaches_adapter_lazily(monkeypatch, tmp_path) -> None:
    """Enabled dev-smoke path works after lazy load: adapter is reachable, scripts load."""
    from app.modules.dev_message_route import smoke_adapter
    from unittest.mock import Mock

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE", "0")

    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    from app.core.config import get_settings
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    get_settings.cache_clear()
    initialize_storage(seed_default=True)

    with TestClient(create_app()) as client:
        response = client.post(
            "/api/dev/message-route-smoke",
            json={"message": "Explain what a pump is."},
        )

    get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["executed"] is False
    assert body["reason"] == "not_safe_local_route"
    responder_builder.assert_not_called()
