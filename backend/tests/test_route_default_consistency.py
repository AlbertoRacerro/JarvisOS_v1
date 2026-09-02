from __future__ import annotations

from app.modules.ai.execution import resolve_effective_route_class


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
