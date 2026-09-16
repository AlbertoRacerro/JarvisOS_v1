from dataclasses import replace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.ai import provider_registry
from app.modules.ai.thread_routes import router


def test_local_conversation_options_are_read_only_configuration_not_health():
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.get('/threads/conversation-options')
    assert response.status_code == 200
    data = response.json()
    assert data['availability'] == 'configured'
    assert data['routes'][0]['route_class'] == 'local:general'
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
    assert [route['route_class'] for route in response.json()['routes']] == ['local:fake']
