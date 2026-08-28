from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.ai.jarvis_context import (
    JarvisContextAdapterRegistry,
    JarvisContextConflictError,
    JarvisContextError,
    build_jarvis_context_preview,
    require_dispatchable_preview,
)
from app.modules.ai.jarvis_context_models import (
    CANONICAL_ROUTE_PAIRS,
    JarvisContextRequest,
    JarvisExactRef,
    JarvisResolvedRef,
    JarvisRouteDescriptor,
)
from app.modules.ai.thread_models import AIThreadSubmit


class StaticAdapter:
    def __init__(
        self,
        *,
        state: str = "current",
        content: object = None,
        provenance: dict[str, object] | None = None,
        action_classes: list[str] | None = None,
        replacement_ref: JarvisExactRef | None = None,
    ) -> None:
        self.state = state
        self.content = content
        self.provenance = provenance or {}
        self.action_classes = action_classes or ["READ", "CONTEXT"]
        self.replacement_ref = replacement_ref

    def resolve(self, ref: JarvisExactRef) -> JarvisResolvedRef:
        return JarvisResolvedRef(
            ref=self.replacement_ref or ref,
            state=self.state,
            content=self.content if self.state == "current" else None,
            provenance=self.provenance,
            action_classes=self.action_classes,
            reason=None if self.state == "current" else f"state:{self.state}",
        )


def _ref(
    *,
    workspace_id: str = "bluerev",
    owner: str = "test-owner",
    kind: str = "test-kind",
    id: str = "record-1",
    version: str = "v1",
) -> JarvisExactRef:
    return JarvisExactRef(
        workspace_id=workspace_id,
        owner=owner,
        kind=kind,
        id=id,
        version=version,
    )


def _request(
    *,
    selected_refs: list[JarvisExactRef] | None = None,
    added_refs: list[JarvisExactRef] | None = None,
    budget_chars: int = 32_000,
) -> JarvisContextRequest:
    return JarvisContextRequest(
        workspace_id="bluerev",
        route=JarvisRouteDescriptor(
            route_id="memory-project-basis",
            canonical_path="/memory/project-basis",
        ),
        selected_refs=selected_refs or [],
        added_context_refs=added_refs or [],
        budget_chars=budget_chars,
    )


def _registry(adapter: StaticAdapter) -> JarvisContextAdapterRegistry:
    registry = JarvisContextAdapterRegistry()
    registry.register(owner="test-owner", kind="test-kind", adapter=adapter)
    return registry


def test_frozen_route_pairs_are_exact_and_legacy_aliases_are_rejected() -> None:
    assert len(CANONICAL_ROUTE_PAIRS) == 17
    for route_id, path in CANONICAL_ROUTE_PAIRS.items():
        descriptor = JarvisRouteDescriptor(route_id=route_id, canonical_path=path)
        assert descriptor.route_id == route_id
        assert descriptor.canonical_path == path

    with pytest.raises(ValidationError):
        JarvisRouteDescriptor(route_id="memory-project-basis", canonical_path="/memory/models")
    with pytest.raises(ValidationError):
        JarvisRouteDescriptor(route_id="home", canonical_path="/")
    with pytest.raises(ValidationError):
        JarvisRouteDescriptor(route_id="design-model", canonical_path="/design/model")


def test_exact_ref_requires_at_least_one_exact_identity() -> None:
    with pytest.raises(ValidationError):
        JarvisExactRef(
            workspace_id="bluerev",
            owner="test-owner",
            kind="test-kind",
            id="record-1",
        )
    with pytest.raises(ValidationError):
        JarvisExactRef(
            workspace_id="bluerev",
            owner="test-owner",
            kind="test-kind",
            id="record-1",
            content_digest="deadbeef",
        )
    exact = JarvisExactRef(
        workspace_id="bluerev",
        owner="test-owner",
        kind="test-kind",
        id="record-1",
        content_digest="sha256:" + "a" * 64,
    )
    assert exact.content_digest == "sha256:" + "a" * 64


def test_selection_does_not_implicitly_add_context() -> None:
    preview = build_jarvis_context_preview(
        _request(selected_refs=[_ref()]),
        registry=_registry(StaticAdapter(content={"secret": "not-added"})),
    )
    assert preview.dispatchable is True
    assert preview.blocks == []
    assert preview.context_sources_manifest == []
    assert preview.ref_outcomes == []


def test_empty_production_registry_fails_closed_with_inspectable_unknown_outcome() -> None:
    preview = build_jarvis_context_preview(_request(added_refs=[_ref()]))
    assert preview.dispatchable is False
    assert preview.blocks == []
    assert preview.included_count == 0
    assert preview.ref_outcomes[0].state == "unknown"
    assert preview.ref_outcomes[0].included is False
    with pytest.raises(JarvisContextConflictError):
        require_dispatchable_preview(_request(added_refs=[_ref()]), preview.context_digest)


@pytest.mark.parametrize("state", ["stale", "unavailable", "unknown"])
def test_noncurrent_adapter_resolution_is_non_dispatchable(state: str) -> None:
    preview = build_jarvis_context_preview(
        _request(added_refs=[_ref()]),
        registry=_registry(StaticAdapter(state=state, provenance={"source": "test"})),
    )
    assert preview.dispatchable is False
    assert preview.blocks == []
    assert preview.ref_outcomes[0].state == state
    assert preview.ref_outcomes[0].provenance == {"source": "test"}


def test_current_adapter_yields_inert_block_provenance_and_stable_digest() -> None:
    request = _request(added_refs=[_ref()])
    registry = _registry(
        StaticAdapter(
            content={"value": 3.5, "unit": "m"},
            provenance={"source_ref": "artifact:123"},
        )
    )
    first = build_jarvis_context_preview(request, registry=registry)
    second = build_jarvis_context_preview(request, registry=registry)
    assert first.dispatchable is True
    assert first.context_digest == second.context_digest
    assert first.included_count == 1
    assert first.blocks[0]["content"] == {"value": 3.5, "unit": "m"}
    assert first.context_sources_manifest[0]["provenance"] == {"source_ref": "artifact:123"}
    assert require_dispatchable_preview(
        request, first.context_digest, registry=registry
    ).context_digest == first.context_digest
    with pytest.raises(JarvisContextConflictError):
        require_dispatchable_preview(request, "sha256:" + "0" * 64, registry=registry)


def test_whole_block_budget_drop_is_disclosed_without_partial_content() -> None:
    registry = _registry(StaticAdapter(content={"text": "x" * 500}))
    preview = build_jarvis_context_preview(
        _request(added_refs=[_ref()], budget_chars=40),
        registry=registry,
    )
    assert preview.dispatchable is True
    assert preview.blocks == []
    assert preview.included_count == 0
    assert preview.dropped_count == 1
    assert preview.ref_outcomes[0].state == "current"
    assert preview.ref_outcomes[0].dropped_for_budget is True


def test_identical_refs_dedupe_and_conflicting_exact_identity_fails_closed() -> None:
    exact = _ref()
    registry = _registry(StaticAdapter(content="ok"))
    preview = build_jarvis_context_preview(
        _request(added_refs=[exact, exact]), registry=registry
    )
    assert len(preview.request.added_context_refs) == 1
    assert preview.included_count == 1

    conflicting = exact.model_copy(update={"version": "v2"})
    with pytest.raises(JarvisContextConflictError):
        build_jarvis_context_preview(
            _request(selected_refs=[exact], added_refs=[conflicting]),
            registry=registry,
        )


def test_workspace_mismatch_fails_before_resolution() -> None:
    with pytest.raises(JarvisContextConflictError):
        build_jarvis_context_preview(
            _request(added_refs=[_ref(workspace_id="other")]),
            registry=_registry(StaticAdapter(content="never")),
        )


def test_registry_rejects_common_commit_execute_and_adapter_identity_drift() -> None:
    registry = JarvisContextAdapterRegistry()
    with pytest.raises(JarvisContextError):
        registry.register(
            owner="test-owner",
            kind="test-kind",
            adapter=StaticAdapter(content="x"),
            action_classes=("READ", "COMMIT"),
        )

    registry.register(
        owner="test-owner",
        kind="test-kind",
        adapter=StaticAdapter(content="x", action_classes=["READ", "EXECUTE"]),
    )
    with pytest.raises(JarvisContextError):
        build_jarvis_context_preview(_request(added_refs=[_ref()]), registry=registry)

    replacement_registry = JarvisContextAdapterRegistry()
    replacement_registry.register(
        owner="test-owner",
        kind="test-kind",
        adapter=StaticAdapter(
            content="x",
            replacement_ref=_ref(id="different-id"),
        ),
    )
    with pytest.raises(JarvisContextConflictError):
        build_jarvis_context_preview(
            _request(added_refs=[_ref()]), registry=replacement_registry
        )


def test_thread_submit_requires_jarvis_request_digest_pair() -> None:
    request = _request()
    with pytest.raises(ValidationError):
        AIThreadSubmit(request_id="req-1", prompt="hello", jarvis_context=request)
    with pytest.raises(ValidationError):
        AIThreadSubmit(
            request_id="req-1",
            prompt="hello",
            expected_jarvis_context_digest="sha256:" + "0" * 64,
        )
    payload = AIThreadSubmit(
        request_id="req-1",
        prompt="hello",
        jarvis_context=request,
        expected_jarvis_context_digest="sha256:" + "0" * 64,
    )
    assert payload.jarvis_context == request
