from __future__ import annotations

import importlib
import json

import pytest
from pydantic import ValidationError

from app.modules.ai.context_builder import DEFAULT_CONTEXT_BUDGET_CHARS, assemble_prompt
from app.modules.ai.jarvis_context import (
    PRODUCTION_ADAPTER_REGISTRY,
    PRODUCTION_CAPABILITY_REGISTRY,
    JarvisCapabilityRegistry,
    JarvisContextAdapterRegistry,
    JarvisContextConflictError,
    JarvisContextError,
    build_jarvis_context_preview,
    require_dispatchable_preview,
)
from app.modules.ai.jarvis_context_models import (
    CANONICAL_ROUTE_PAIRS,
    JarvisCapabilityDescriptor,
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

    for route_id, path in [
        ("memory-project-basis", "/memory/models"),
        ("home", "/"),
        ("design-model", "/design/model"),
        ("design-results", "/design/results"),
        ("settings", "/settings"),
    ]:
        with pytest.raises(ValidationError):
            JarvisRouteDescriptor(route_id=route_id, canonical_path=path)


def test_capability_lookup_is_keyed_by_canonical_route_id() -> None:
    registry = JarvisCapabilityRegistry()
    registry.register(
        JarvisCapabilityDescriptor(
            capability_id="basis-context",
            route_id="memory-project-basis",
            action_class="CONTEXT",
        )
    )
    registry.register(
        JarvisCapabilityDescriptor(
            capability_id="models-read",
            route_id="memory-models",
            action_class="READ",
        )
    )

    assert [item.capability_id for item in registry.for_route("memory-project-basis")] == [
        "basis-context"
    ]
    assert registry.for_route("/memory/project-basis") == []
    importlib.import_module("app.modules.memory.jarvis_knowledge_actions")
    production = PRODUCTION_CAPABILITY_REGISTRY.for_route("memory-project-basis")
    assert {item.capability_id for item in production} == {
        "knowledge.add-context",
        "knowledge.propose",
    }
    assert {item.action_class for item in production} == {"CONTEXT", "PROPOSE"}


def test_exact_ref_requires_at_least_one_exact_identity() -> None:
    with pytest.raises(ValidationError):
        JarvisExactRef(
            workspace_id="bluerev",
            owner="test-owner",
            kind="test-kind",
            id="record-1",
        )


def test_registry_rejects_duplicate_adapter_keys() -> None:
    registry = JarvisContextAdapterRegistry()
    adapter = StaticAdapter()
    registry.register(owner="test-owner", kind="test-kind", adapter=adapter)
    with pytest.raises(ValueError):
        registry.register(owner="test-owner", kind="test-kind", adapter=adapter)


def test_capability_registry_rejects_duplicate_ids() -> None:
    registry = JarvisCapabilityRegistry()
    capability = JarvisCapabilityDescriptor(
        capability_id="cap-1",
        route_id="memory-project-basis",
        action_class="READ",
    )
    registry.register(capability)
    with pytest.raises(ValueError):
        registry.register(capability)


def test_preview_preserves_selection_and_context_order() -> None:
    registry = _registry(StaticAdapter(content={"value": 1}))
    selected = _ref(id="selected")
    added = _ref(id="added")
    preview = build_jarvis_context_preview(
        _request(selected_refs=[selected], added_refs=[added]),
        registry=registry,
    )
    assert [block["origin"] for block in preview.blocks] == ["selection", "context"]
    assert [block["record"]["value"] for block in preview.blocks] == [1, 1]


def test_preview_deduplicates_identical_refs_across_origins() -> None:
    registry = _registry(StaticAdapter(content={"value": 1}))
    ref = _ref()
    preview = build_jarvis_context_preview(
        _request(selected_refs=[ref], added_refs=[ref]),
        registry=registry,
    )
    assert preview.included_count == 1
    assert preview.blocks[0]["origin"] == "selection"


def test_preview_detects_conflicting_identity_for_same_owner_kind_id() -> None:
    registry = _registry(StaticAdapter(content={"value": 1}))
    first = _ref(version="v1")
    second = _ref(version="v2")
    with pytest.raises(JarvisContextConflictError):
        build_jarvis_context_preview(
            _request(selected_refs=[first], added_refs=[second]),
            registry=registry,
        )


def test_preview_marks_stale_ref_non_dispatchable() -> None:
    registry = _registry(StaticAdapter(state="stale"))
    preview = build_jarvis_context_preview(
        _request(added_refs=[_ref()]),
        registry=registry,
    )
    assert preview.dispatchable is False
    assert preview.resolved_refs[0].state == "stale"
    with pytest.raises(JarvisContextError):
        require_dispatchable_preview(_request(added_refs=[_ref()]), preview.context_digest, registry=registry)


def test_preview_marks_unknown_adapter_non_dispatchable() -> None:
    preview = build_jarvis_context_preview(_request(added_refs=[_ref()]))
    assert preview.dispatchable is False
    assert preview.resolved_refs[0].state == "unknown"


def test_preview_budget_drops_whole_blocks_without_partial_records() -> None:
    registry = _registry(StaticAdapter(content={"text": "x" * 4_000}))
    preview = build_jarvis_context_preview(
        _request(added_refs=[_ref(id="one"), _ref(id="two")], budget_chars=4_500),
        registry=registry,
    )
    assert preview.included_count == 1
    assert preview.dropped_count == 1
    assert preview.blocks[0]["record"]["text"] == "x" * 4_000


def test_digest_is_deterministic_for_the_same_exact_refs_and_resolved_content() -> None:
    registry = _registry(StaticAdapter(content={"value": 1}, provenance={"source": "fixture"}))
    request = _request(added_refs=[_ref()])
    first = build_jarvis_context_preview(request, registry=registry)
    second = build_jarvis_context_preview(request, registry=registry)
    assert first.context_digest == second.context_digest


def test_require_dispatchable_preview_rejects_digest_drift() -> None:
    registry = _registry(StaticAdapter(content={"value": 1}))
    request = _request(added_refs=[_ref()])
    preview = build_jarvis_context_preview(request, registry=registry)
    with pytest.raises(JarvisContextConflictError):
        require_dispatchable_preview(request, "sha256:" + "0" * 64, registry=registry)
    assert require_dispatchable_preview(request, preview.context_digest, registry=registry).context_digest == preview.context_digest


def test_thread_submit_rejects_raw_context_payload() -> None:
    with pytest.raises(ValidationError):
        AIThreadSubmit.model_validate(
            {
                "prompt": "hello",
                "request_id": "req-1",
                "context": {"records": [{"id": "raw"}]},
            }
        )


def test_thread_submit_accepts_exact_inspected_context_request() -> None:
    submit = AIThreadSubmit.model_validate(
        {
            "prompt": "hello",
            "request_id": "req-1",
            "context_request": {
                "selection": {"requirements": ["req-1"]},
                "expected_context_digest": "sha256:" + "1" * 64,
            },
        }
    )
    assert submit.context_request is not None
    assert submit.context_request.expected_context_digest == "sha256:" + "1" * 64


def test_prompt_assembly_is_additive_and_ordered() -> None:
    assembled, summary = assemble_prompt(
        "system",
        "user",
        context_blocks=[
            {"origin": "selection", "record": {"id": "selected"}},
            {"origin": "context", "record": {"id": "added"}},
        ],
    )
    assert "system" in assembled
    assert '"selected"' in assembled
    assert '"added"' in assembled
    assert assembled.index('"selected"') < assembled.index('"added"') < assembled.index("user")
    assert summary.included_blocks == 2


def test_prompt_assembly_drops_last_blocks_on_budget_pressure() -> None:
    first = {"record": {"text": "a" * 200}}
    second = {"record": {"text": "b" * 200}}
    assembled, summary = assemble_prompt(
        "system",
        "user",
        context_blocks=[first, second],
        budget_chars=DEFAULT_CONTEXT_BUDGET_CHARS,
    )
    assert summary.included_blocks == 2
    assert summary.dropped_blocks == 0
    assert '"aaaa' in assembled and '"bbbb' in assembled
