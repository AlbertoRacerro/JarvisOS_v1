from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

import app.modules.ai.egress_authority as egress_authority_module
import app.modules.bluecad.evidence_egress as evidence_egress_module
import app.modules.bluecad.loop as loop_module
from app.core.database import initialize_database, open_sqlite_connection
from app.modules.ai import sensitivity
from app.modules.ai.egress_persistence import prepare_egress_attempt
from app.modules.ai.egress_policy import EXTERNAL_PROVIDER_OPERATION
from app.modules.ai.egress_sanitizer import create_prompt_derivative
from app.modules.ai.egress_service import (
    EgressPacketMaterial,
    build_packet_projection,
    sha256_text,
)
from app.modules.ai.execution import ProviderBinding
from app.modules.ai.models import AISettingsUpdate
from app.modules.ai.settings import ensure_ai_settings, update_ai_settings
from app.modules.bluecad.evidence_egress import (
    bind_evidence_lineage,
    enrich_authorized_evidence_manifest,
)
from app.modules.bluecad.evidence_sight import EvidenceSight
from app.modules.events.service import utc_now

WORKSPACE_ID = "bluerev"
NOW = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)


def _bootstrap(monkeypatch: pytest.MonkeyPatch) -> str:
    initialize_database()
    ensure_ai_settings()
    update_ai_settings(
        AISettingsUpdate(
            policy_mode="FAST_DEV",
            monthly_api_budget_usd=100.0,
            paid_ai_enabled=True,
            provider_mode="deepseek",
        )
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only-secret")
    with open_sqlite_connection() as connection:
        now = utc_now()
        connection.execute(
            """
            INSERT OR IGNORE INTO workspaces (
                id, name, slug, description, status, created_at, updated_at
            ) VALUES (?, 'BlueRev', 'bluerev', NULL, 'active', ?, ?)
            """,
            (WORKSPACE_ID, now, now),
        )
        connection.commit()
    approval = create_prompt_derivative(
        raw_prompt="CONFIDENTIAL PROJECT GEOMETRY: test-only raw request.",
        derivative_content="Generic structural repair instruction.",
        final_level="S1",
        transformations=("test_fixture_generic_rewrite",),
        sanitizer_kind="deterministic",
        sanitizer_version="test-fixture-v1",
        sanitizer_config_digest="a" * 64,
        workspace_id=WORKSPACE_ID,
        now=NOW,
    )
    return approval.derivative_id


def _lineage(*, structural_attempt_id: str = "attempt-2") -> dict[str, object]:
    return {
        "schema_version": "bluecad_evidence_lineage_v0_1",
        "workspace_id": WORKSPACE_ID,
        "candidate_id": "candidate-1",
        "source_attempt_id": "attempt-1",
        "structural_attempt_id": structural_attempt_id,
        "ordered_source_refs": ["evidence:e1"],
        "sight_digest": "sha256:" + "1" * 64,
        "renderer_id": "evidence_sight_v0",
        "renderer_version": "evidence_sight_v0",
        "max_lines": 6,
        "max_chars": 2000,
        "derivative_id": "derivative-1",
        "derivative_digest": "sha256:" + "2" * 64,
        "effective_level": "S1",
        "sanitizer_kind": "deterministic",
        "sanitizer_version": "bluecad_evidence_sight_derivative_v0_1",
        "sanitizer_config_digest": "3" * 64,
        "sanitizer_ai_job_id": None,
        "instruction_derivative_id": "prompt-derivative-1",
        "instruction_derivative_digest": "sha256:" + "4" * 64,
        "sensitivity_policy_version": "ip-egress-v1",
        "egress_policy_version": "ip-egress-v1",
    }


def _manifest() -> tuple[dict[str, object], ...]:
    return (
        {
            "source_ref": "derivative:derivative-1",
            "source_refs": ["evidence:e1"],
            "content_digest": "sha256:" + "2" * 64,
            "effective_level": "S1",
            "label_id": None,
            "derivative_id": "derivative-1",
            "inclusion_reason": "approved_derivative",
        },
    )


def _material(
    *,
    lineage: dict[str, object] | None = None,
    prompt_derivative_id: str = "prompt-derivative-1",
) -> EgressPacketMaterial:
    manifest = dict(_manifest()[0])
    if lineage is not None:
        manifest["evidence_lineage"] = lineage
    return EgressPacketMaterial(
        operation=EXTERNAL_PROVIDER_OPERATION,
        task_kind="bluecad_cad_repair",
        route_class="external:cheap",
        provider_id="deepseek",
        model_id="deepseek-v4-pro",
        fallback_index=0,
        prompt="Generic structural repair instruction.",
        context_blocks=(
            {
                "source": "derivative:derivative-1",
                "type": "sanitized_derivative",
                "id": "derivative-1",
                "content": "Generic structural evidence.",
            },
        ),
        prompt_level="S1",
        context_level="S1",
        final_level="S1",
        max_output_tokens=128,
        workspace_id=WORKSPACE_ID,
        prompt_derivative_id=prompt_derivative_id,
        included_manifest=(manifest,),
        source_digests=(("evidence:e1", sha256_text("source-body")),),
    )


def _matching_sight() -> EvidenceSight:
    return EvidenceSight(
        text="EVIDENCE_SIGHT_V0\nevidence:validation verdict=fail",
        digest="sha256:" + "1" * 64,
        record_ids=("e1",),
    )


def _matching_prompt_derivative() -> SimpleNamespace:
    return SimpleNamespace(
        id="prompt-derivative-1",
        derivative_digest="sha256:" + "4" * 64,
        workspace_id=WORKSPACE_ID,
        sanitizer_kind="model_local",
        status="approved",
    )


def test_lineage_enrichment_is_scoped_and_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest()
    monkeypatch.setattr(
        evidence_egress_module,
        "_current_lineage_sight",
        lambda _lineage: _matching_sight(),
    )
    monkeypatch.setattr(
        evidence_egress_module,
        "_current_structural_prompt_derivative",
        lambda _lineage: _matching_prompt_derivative(),
    )

    assert enrich_authorized_evidence_manifest(manifest) == manifest
    with bind_evidence_lineage(_lineage()):
        enriched = enrich_authorized_evidence_manifest(manifest)
    assert enriched[0]["evidence_lineage"]["structural_attempt_id"] == "attempt-2"
    assert "evidence_lineage" not in manifest[0]

    bad = _lineage()
    bad["ordered_source_refs"] = ["evidence:other"]
    with bind_evidence_lineage(bad), pytest.raises(
        sensitivity.SensitivityPolicyError
    ):
        enrich_authorized_evidence_manifest(manifest)

    wrong_manifest = (dict(manifest[0], content_digest="sha256:" + "9" * 64),)
    with bind_evidence_lineage(_lineage()), pytest.raises(
        sensitivity.SensitivityPolicyError
    ):
        enrich_authorized_evidence_manifest(wrong_manifest)


def test_packet_authorization_rejects_prompt_derivative_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        evidence_egress_module,
        "_current_lineage_sight",
        lambda _lineage: _matching_sight(),
    )
    monkeypatch.setattr(
        evidence_egress_module,
        "_current_structural_prompt_derivative",
        lambda _lineage: SimpleNamespace(
            id="prompt-derivative-other",
            derivative_digest="sha256:" + "9" * 64,
            workspace_id=WORKSPACE_ID,
            sanitizer_kind="model_local",
            status="approved",
        ),
    )

    with bind_evidence_lineage(_lineage()), pytest.raises(
        sensitivity.SensitivityPolicyError
    ):
        enrich_authorized_evidence_manifest(_manifest())


def test_packet_authorization_rejects_sight_insertion_order_or_digest_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest()
    monkeypatch.setattr(
        evidence_egress_module,
        "_current_structural_prompt_derivative",
        lambda _lineage: _matching_prompt_derivative(),
    )
    current_sights = (
        EvidenceSight("changed", "sha256:" + "8" * 64, ("e1",)),
        EvidenceSight("inserted", "sha256:" + "1" * 64, ("e1", "e2")),
        EvidenceSight("reordered", "sha256:" + "1" * 64, ("e2", "e1")),
    )
    for sight in current_sights:
        monkeypatch.setattr(
            evidence_egress_module,
            "_current_lineage_sight",
            lambda _lineage, current=sight: current,
        )
        with bind_evidence_lineage(_lineage()), pytest.raises(
            sensitivity.SensitivityPolicyError
        ):
            enrich_authorized_evidence_manifest(manifest)


def test_lineage_mutation_changes_packet_digest() -> None:
    first = build_packet_projection(_material(lineage=_lineage()))
    second = build_packet_projection(
        _material(lineage=_lineage(structural_attempt_id="attempt-3"))
    )
    assert first.packet_digest != second.packet_digest
    assert first.included_manifest_json != second.included_manifest_json


def test_first_use_structural_trigger_denies_without_ticket_or_reservation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompt_derivative_id = _bootstrap(monkeypatch)

    result = prepare_egress_attempt(
        _material(
            lineage=_lineage(),
            prompt_derivative_id=prompt_derivative_id,
        ),
        now=NOW,
    )

    assert result.result == "deny"
    assert result.reason_code == "bluecad_structural_confirmation_unsupported"
    assert result.trigger_ids == ("t1",)
    assert result.ticket_id is None
    assert result.reservation_id is None
    assert result.confirmation_required is False
    with open_sqlite_connection() as connection:
        counts = {
            table: int(
                connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()[
                    "count"
                ]
            )
            for table in (
                "egress_packets",
                "egress_decisions",
                "egress_confirmation_tickets",
                "egress_budget_reservations",
            )
        }
        decision = connection.execute(
            "SELECT result, reason_code, confirmation_required, trigger_ids_json "
            "FROM egress_decisions"
        ).fetchone()
    assert counts == {
        "egress_packets": 1,
        "egress_decisions": 1,
        "egress_confirmation_tickets": 0,
        "egress_budget_reservations": 0,
    }
    assert dict(decision) == {
        "result": "deny",
        "reason_code": "bluecad_structural_confirmation_unsupported",
        "confirmation_required": 0,
        "trigger_ids_json": '["t1"]',
    }


def test_prompt_validator_runs_before_derivative_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialize_database()
    binding = SimpleNamespace(
        provider_id="local-provider",
        model_id="local-model",
        requires_network=False,
        max_output_tokens=256,
    )
    registry = SimpleNamespace(
        bindings={"local:fast": binding},
        fallback_chains={"local:fast": ()},
    )
    response = SimpleNamespace(
        text="Generic repair\nRAW_GEOMETRY_SPEC_BEGIN",
        provider_id=binding.provider_id,
        model_id=binding.model_id,
    )
    outcome = SimpleNamespace(
        status="success",
        response=response,
        selected_route_class="local:fast",
        ledger_id="sanitizer-job-1",
        error_type=None,
    )
    monkeypatch.setattr(
        egress_authority_module,
        "_resolve_local_sanitizer_binding",
        lambda **_kwargs: (binding, registry),
    )
    monkeypatch.setattr(
        egress_authority_module,
        "_run_local_sanitizer",
        lambda **_kwargs: outcome,
    )
    with open_sqlite_connection() as connection:
        before = connection.execute(
            "SELECT COUNT(*) AS count FROM egress_prompt_derivatives"
        ).fetchone()["count"]

    with pytest.raises(sensitivity.SensitivityPolicyError):
        egress_authority_module.sanitize_prompt_with_local_model(
            raw_prompt="CONFIDENTIAL PROJECT GEOMETRY: raw task.",
            task_kind="bluecad_cad_repair",
            workspace_id=WORKSPACE_ID,
            output_validator=lambda content: (
                evidence_egress_module._validate_transformed_prompt_content(
                    content,
                    raw_prompt="CONFIDENTIAL PROJECT GEOMETRY: raw task.",
                    forbidden_spec_json='{"schema_version":"geometry_spec_v0_1"}',
                )
            ),
        )

    with open_sqlite_connection() as connection:
        after = connection.execute(
            "SELECT COUNT(*) AS count FROM egress_prompt_derivatives"
        ).fetchone()["count"]
    assert after == before


def test_model_sanitizer_config_identity_binds_renderer_context() -> None:
    policy = SimpleNamespace(config_digest="policy-digest")
    binding = SimpleNamespace(
        provider_id="local-provider",
        model_id="local-model",
        requires_network=False,
        max_output_tokens=512,
    )
    registry = SimpleNamespace(
        bindings={"local:fast": binding},
        fallback_chains={"local:fast": ()},
    )
    base = {
        "workspace_id": WORKSPACE_ID,
        "candidate_id": "candidate-1",
        "source_attempt_id": "attempt-1",
        "ordered_source_refs": ["evidence:e1"],
        "sight_digest": "sha256:" + "1" * 64,
        "renderer_id": "evidence_sight_v0",
        "renderer_version": "evidence_sight_v0",
        "max_lines": 6,
        "max_chars": 2000,
    }

    def digest(context: dict[str, object]) -> str:
        return egress_authority_module._sanitizer_config_digest(
            policy=policy,
            route_class="local:fast",
            template="canonical-template",
            version="canonical-v1",
            registry=registry,
            config_context=context,
        )

    variants = (
        base,
        dict(base, candidate_id="candidate-2"),
        dict(base, source_attempt_id="attempt-2"),
        dict(base, sight_digest="sha256:" + "2" * 64),
        dict(base, ordered_source_refs=["evidence:e2", "evidence:e1"]),
    )
    assert len({digest(context) for context in variants}) == len(variants)


def test_preparation_failure_happens_before_structural_attempt_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sight = EvidenceSight(
        text="EVIDENCE_SIGHT_V0\nevidence:validation verdict=fail",
        digest="sha256:" + "4" * 64,
        record_ids=("e1",),
    )
    events: list[str] = []
    binding = ProviderBinding(
        "external:cheap",
        "deepseek",
        "deepseek-v4-pro",
        True,
        4000,
        execution_class="external",
        context_window_tokens=8192,
    )
    monkeypatch.setattr(loop_module, "render_evidence_sight", lambda *_args: sight)
    monkeypatch.setattr(
        loop_module,
        "resolve_binding",
        lambda *_args, **_kwargs: (binding, SimpleNamespace()),
    )

    def fail_preparation(**_kwargs):
        events.append("prepare")
        raise RuntimeError("stale evidence")

    def start_attempt(*_args, **_kwargs):
        events.append("start")
        raise AssertionError("attempt must not be inserted")

    monkeypatch.setattr(loop_module, "prepare_external_structural_repair", fail_preparation)
    monkeypatch.setattr(loop_module, "start_structural_attempt", start_attempt)

    loop_module._run_structural_repair_cycle(
        workspace_id=WORKSPACE_ID,
        candidate_id="candidate-1",
        initial_attempt_id="attempt-1",
        initial_attempt_no=1,
        initial_spec={"schema_version": "geometry_spec_v0_1"},
        route_class="external:cheap",
        loop_config=SimpleNamespace(max_structural_repairs=1, max_output_tokens=128),
        adapters=None,
        bindings={"external:cheap": binding},
    )

    assert events == ["prepare"]


def test_unresolved_binding_stops_before_preparation_attempt_or_ai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sight = EvidenceSight(
        text="EVIDENCE_SIGHT_V0\nevidence:validation verdict=fail",
        digest="sha256:" + "5" * 64,
        record_ids=("e1",),
    )
    events: list[str] = []
    monkeypatch.setattr(loop_module, "render_evidence_sight", lambda *_args: sight)
    monkeypatch.setattr(
        loop_module,
        "resolve_binding",
        lambda *_args, **_kwargs: (None, SimpleNamespace()),
    )
    monkeypatch.setattr(
        loop_module,
        "prepare_external_structural_repair",
        lambda **_kwargs: events.append("prepare"),
    )
    monkeypatch.setattr(
        loop_module,
        "start_structural_attempt",
        lambda *_args, **_kwargs: events.append("start"),
    )
    monkeypatch.setattr(
        loop_module,
        "run_ai_task",
        lambda **_kwargs: events.append("ai"),
    )

    loop_module._run_structural_repair_cycle(
        workspace_id=WORKSPACE_ID,
        candidate_id="candidate-1",
        initial_attempt_id="attempt-1",
        initial_attempt_no=1,
        initial_spec={"schema_version": "geometry_spec_v0_1"},
        route_class="external:cheap",
        loop_config=SimpleNamespace(max_structural_repairs=1, max_output_tokens=128),
        adapters=None,
        bindings=None,
    )

    assert events == []
