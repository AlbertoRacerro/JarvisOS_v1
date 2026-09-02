from __future__ import annotations

import pytest

from app.modules.ai import gateway, thread_service
from app.modules.ai.execution import resolve_effective_route_class
from app.modules.ai.jarvis_context_models import (
    JarvisContextRequest,
    JarvisExactRef,
    JarvisRouteDescriptor,
)
from app.modules.ai.models import AITaskRunRequest
from app.modules.ai.thread_models import AIThreadSubmit


def test_resolve_effective_route_uses_task_kind_default_when_omitted() -> None:
    assert resolve_effective_route_class(task_kind="general", route_class=None) == "local:fake"


def test_resolve_effective_route_preserves_explicit_route() -> None:
    assert (
        resolve_effective_route_class(
            task_kind="general",
            route_class="external:scaleway",
        )
        == "external:scaleway"
    )


def test_resolve_effective_route_preserves_explicit_auto() -> None:
    assert resolve_effective_route_class(task_kind="general", route_class="auto") == "auto"


def test_gateway_uses_effective_route_resolver_before_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = object()
    monkeypatch.setattr(
        gateway,
        "resolve_effective_route_class",
        lambda **_kwargs: "auto",
    )

    from app.modules.ai.routing import bridge

    monkeypatch.setattr(bridge, "run_auto_task", lambda _request: sentinel)

    assert gateway.AIGateway().run_task(AITaskRunRequest(prompt="route me")) is sentinel


def test_exact_ref_guard_uses_effective_route_when_route_is_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        thread_service,
        "resolve_effective_route_class",
        lambda **_kwargs: "external:scaleway",
    )
    exact_ref = JarvisExactRef(
        workspace_id="w",
        owner="memory",
        kind="parameter",
        id="p1",
        revision="1",
    )
    jarvis_context = JarvisContextRequest(
        workspace_id="w",
        route=JarvisRouteDescriptor(route_id="ai-threads", canonical_path="/ai-threads"),
        added_context_refs=[exact_ref],
    )
    payload = AIThreadSubmit(
        request_id="r1",
        prompt="use exact ref",
        task_kind="general",
        route_class=None,
        jarvis_context=jarvis_context,
        expected_jarvis_context_digest="sha256:" + "0" * 64,
    )

    with pytest.raises(
        thread_service.AIThreadConflictError,
        match="exact-ref Jarvis context is unavailable for external routes",
    ):
        thread_service._context_blocks_for_new_submit("w", payload)
