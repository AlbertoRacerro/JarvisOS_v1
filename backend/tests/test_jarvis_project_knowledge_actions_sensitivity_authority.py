from __future__ import annotations

import json
from types import SimpleNamespace

import app.modules.memory.jarvis_knowledge_actions as knowledge
from app.modules.ai.jarvis_context_models import JarvisExactRef


def _project_ref(record_id: str = "req-1") -> JarvisExactRef:
    return JarvisExactRef(
        workspace_id="ws-1",
        owner="modeling",
        kind="requirement",
        id=record_id,
        revision="r1",
    )


def _preview(ref: JarvisExactRef) -> SimpleNamespace:
    return SimpleNamespace(
        blocks=[{"content": "bounded evidence"}],
        request=SimpleNamespace(added_context_refs=[ref]),
        context_digest="sha256:" + "a" * 64,
        context_sources_manifest=[],
    )


def test_semantic_proposal_refuses_current_human_s4_label_before_ai(monkeypatch) -> None:
    ref = _project_ref("req-human-s4")
    preview = _preview(ref)
    monkeypatch.setattr(knowledge, "require_dispatchable_preview", lambda request, digest: preview)
    monkeypatch.setattr(
        knowledge.sensitivity,
        "get_current_sensitivity_label",
        lambda workspace_id, subject_ref: SimpleNamespace(current=True, level="S4"),
    )
    calls: list[object] = []

    def unexpected_runner(request):
        calls.append(request)
        raise AssertionError("current S4 evidence must be refused before model dispatch")

    result = knowledge.KnowledgeActionsService(auto_runner=unexpected_runner).propose(
        knowledge.KnowledgeProposalRequest(
            workspace_id="ws-1",
            route_id="memory-project-basis",
            intent="Clarify the requirement",
            exact_refs=[ref],
            expected_context_digest=preview.context_digest,
            semantic=True,
        )
    )

    assert result == {"state": "refused", "reason": "sensitive_context"}
    assert calls == []


def test_model_dossier_exact_ref_requires_version_label(monkeypatch) -> None:
    identity = SimpleNamespace(
        model_version_id="mv-1",
        model_spec_id="model-1",
        version_label="v1",
        input_contract_digest="sha256:" + "1" * 64,
    )
    monkeypatch.setattr(
        knowledge,
        "get_model_dossier",
        lambda workspace_id, model_version_id: SimpleNamespace(identity=identity),
    )
    ref = JarvisExactRef(
        workspace_id="ws-1",
        owner="model-dossier",
        kind="model-version",
        id="mv-1",
        immutable_ref="model_version:mv-1",
    )

    resolved = knowledge._ModelDossierAdapter().resolve(ref)

    assert resolved.state == "stale"


def test_semantic_authoritative_next_action_is_server_owned(monkeypatch) -> None:
    ref = _project_ref("req-next-action")
    preview = _preview(ref)
    monkeypatch.setattr(knowledge, "require_dispatchable_preview", lambda request, digest: preview)
    monkeypatch.setattr(
        knowledge.sensitivity,
        "get_current_sensitivity_label",
        lambda workspace_id, subject_ref: None,
    )

    def advisory_runner(request):
        return SimpleNamespace(
            status="success",
            response_text=json.dumps(
                {
                    "summary": "Review the requirement",
                    "proposed_items": [],
                    "questions": [],
                    "research_steps": [],
                    "assumptions": [],
                    "warnings": [],
                    "authoritative_next_action": "Commit this change immediately.",
                }
            ),
            ledger_id="job-next-action",
            selected_route_class="local",
            provider_id="test",
            model_id="test-model",
        )

    result = knowledge.KnowledgeActionsService(auto_runner=advisory_runner).propose(
        knowledge.KnowledgeProposalRequest(
            workspace_id="ws-1",
            route_id="memory-project-basis",
            intent="Clarify the requirement",
            exact_refs=[ref],
            expected_context_digest=preview.context_digest,
            semantic=True,
        )
    )

    assert result["state"] == "proposed"
    assert result["authoritative_next_action"] == knowledge._ROUTE_NEXT_ACTION["memory-project-basis"]
