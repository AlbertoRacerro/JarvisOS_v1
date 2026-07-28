from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

import app.modules.bluecad.loop as loop_module
from app.core.database import initialize_database, open_sqlite_connection
from app.modules.ai.egress_persistence import prepare_egress_attempt
from app.modules.ai.egress_policy import EXTERNAL_PROVIDER_OPERATION
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


def _bootstrap(monkeypatch: pytest.MonkeyPatch) -> None:
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
        "sensitivity_policy_version": "ip-egress-v1",
        "egress_policy_version": "ip-egress-v1",
    }


def _material(*, lineage: dict[str, object] | None = None) -> EgressPacketMaterial:
    manifest = {
        "source_ref": "derivative:derivative-1",
        "source_refs": ["evidence:e1"],
        "content_digest": "sha256:" + "2" * 64,
        "effective_level": "S1",
        "label_id": None,
        "derivative_id": "derivative-1",
        "inclusion_reason": "approved_derivative",
    }
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
        prompt_derivative_id="prompt-derivative-1",
        included_manifest=(manifest,),
        source_digests=(("evidence:e1", sha256_text("source-body")),),
    )


def test_lineage_enrichment_is_scoped_and_exact() -> None:
    manifest = (
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

    assert enrich_authorized_evidence_manifest(manifest) == manifest
    with bind_evidence_lineage(_lineage()):
        enriched = enrich_authorized_evidence_manifest(manifest)
    assert enriched[0]["evidence_lineage"]["structural_attempt_id"] == "attempt-2"
    assert "evidence_lineage" not in manifest[0]

    bad = _lineage()
    bad["ordered_source_refs"] = ["evidence:other"]
    with bind_evidence_lineage(bad), pytest.raises(Exception):
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
    _bootstrap(monkeypatch)

    result = prepare_egress_attempt(_material(lineage=_lineage()), now=NOW)

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
