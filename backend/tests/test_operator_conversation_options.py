from dataclasses import replace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.ai import provider_registry
from app.modules.ai.thread_routes import router


@pytest.mark.parametrize(
    ("status", "reachable", "installed", "loaded", "reason"),
    [
        ({"ollama_reachable": False}, False, None, None, "RUNTIME_UNREACHABLE"),
        ({"ollama_reachable": True, "installed_models": [], "loaded_models": [], "configured_route_models": {"local:general": "gemma4:12b-it-qat"}}, True, False, False, "MODEL_NOT_INSTALLED"),
        ({"ollama_reachable": True, "installed_models": ["gemma4:12b-it-qat"], "loaded_models": [], "configured_route_models": {"local:general": "gemma4:12b-it-qat"}}, True, True, False, None),
        ({"ollama_reachable": True, "installed_models": ["gemma4:12b-it-qat"], "loaded_models": [{"name": "gemma4:12b-it-qat"}], "configured_route_models": {"local:general": "gemma4:12b-it-qat"}}, True, True, True, None),
    ],
)
def test_conversation_options_report_truthful_ollama_availability(monkeypatch, status, reachable, installed, loaded, reason):
    monkeypatch.setattr("app.modules.local_ai.runtime.status.get_local_ai_runtime_status", lambda: status)
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.get('/threads/conversation-options')
    route = next(route for route in response.json()['routes'] if route['route_class'] == 'local:general')
    state = route['availability']
    assert state['runtime_reachable'] is reachable
    assert state['model_installed'] is installed
    assert state['model_loaded'] is loaded
    assert state['qualified'] == 'unknown'
    assert state['reason_code'] == reason


def test_local_conversation_options_are_read_only_configuration_not_health():
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.get('/threads/conversation-options')
    assert response.status_code == 200
    data = response.json()
    assert data['availability'] == 'configured'
    general = next(route for route in data['routes'] if route['route_class'] == 'local:general')
    assert {'configured', 'runtime_reachable', 'model_installed', 'model_loaded', 'qualified', 'reason_code', 'message'} <= set(general['availability'])
    assert general['availability']['qualified'] == 'unknown'
    synthetic = next(route for route in data['routes'] if route['route_class'] == 'local:fake')
    assert synthetic['execution_class'] == 'synthetic'
    assert all(route['execution_class'] in {'local_compute', 'synthetic'} for route in data['routes'])
    assert 'api_key' not in response.text and 'base_url' not in response.text


def test_conversation_options_never_offer_a_network_or_external_binding(monkeypatch):
    bindings = provider_registry.registry_bindings()
    bindings['local:general'] = replace(bindings['local:general'], requires_network=True)
    bindings['local:coder'] = replace(bindings['local:coder'], execution_class='external_provider')
    monkeypatch.setattr(provider_registry, 'registry_bindings', lambda: bindings)
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.get('/threads/conversation-options')
    assert [route['route_class'] for route in response.json()['routes']] == ['local:fast', 'local:fake']
