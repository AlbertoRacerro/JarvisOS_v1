from __future__ import annotations

import sys
from pathlib import Path


def replace_once(root: Path, path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def main(root: Path) -> None:
    confirmation = "backend/app/modules/ai/egress_confirmation.py"
    replace_once(
        root,
        confirmation,
        "    max_output_tokens: int\n    pricing_version: str\n",
        "    max_output_tokens: int\n",
    )
    replace_once(
        root,
        confirmation,
        "                   decision.source_count, decision.pricing_version,\n",
        "                   decision.source_count,\n",
    )
    replace_once(
        root,
        confirmation,
        '''        fallback_index=int(row["fallback_index"]),\n        max_output_tokens=int(row["max_output_tokens"]),\n        pricing_version=str(row["pricing_version"]),\n    )\n''',
        '''        fallback_index=int(row["fallback_index"]),\n        max_output_tokens=int(row["max_output_tokens"]),\n    )\n''',
    )
    replace_once(
        root,
        confirmation,
        '''        reservation_id=reservation_id,\n        registry=registry,\n        persisted_pricing_version=(\n            metadata.pricing_version if reservation_id is None else None\n        ),\n''',
        '''        reservation_id=reservation_id,\n        registry=registry,\n        use_confirmation_pricing_snapshot=not consumed.authorized,\n''',
    )

    transaction = "backend/app/modules/ai/token_flow_external_transaction.py"
    replace_once(
        root,
        transaction,
        "from __future__ import annotations\n\nimport sqlite3\n",
        "from __future__ import annotations\n\nimport json\nimport sqlite3\n",
    )
    replace_once(
        root,
        transaction,
        '''    reservation_id: str | None = None,\n    registry: ProviderRegistry | None = None,\n    persisted_pricing_version: str | None = None,\n    now: datetime | None = None,\n''',
        '''    reservation_id: str | None = None,\n    registry: ProviderRegistry | None = None,\n    use_confirmation_pricing_snapshot: bool = False,\n    now: datetime | None = None,\n''',
    )
    replace_once(
        root,
        transaction,
        '''    registry = registry or load_default_provider_registry()\n    if persisted_pricing_version is not None:\n        if (\n            reservation_id is not None\n            or adapter_invoked\n            or dispatch_state is not AIExternalDispatchState.not_started\n            or response is not None\n        ):\n            raise EgressContractError(\n                "persisted pricing version is only valid for a non-dispatched "\n                "attempt without a reservation"\n            )\n        if (\n            not isinstance(persisted_pricing_version, str)\n            or not persisted_pricing_version.strip()\n        ):\n            raise EgressContractError(\n                "persisted pricing version must be non-empty text"\n            )\n        pricing_version = persisted_pricing_version.strip()\n    else:\n        pricing_version = resolve_model_pricing(\n            registry, binding.provider_id, binding.model_id\n        ).pricing_version\n    with persistence._immediate_transaction() as connection:\n        _bind_attempt_identity(\n            connection,\n            ai_job_id=ai_job_id,\n            binding=binding,\n            fallback_index=fallback_index,\n        )\n''',
        '''    if not isinstance(use_confirmation_pricing_snapshot, bool):\n        raise EgressContractError(\n            "use_confirmation_pricing_snapshot must be boolean"\n        )\n    if use_confirmation_pricing_snapshot and (\n        reservation_id is not None\n        or adapter_invoked\n        or dispatch_state is not AIExternalDispatchState.not_started\n        or response is not None\n    ):\n        raise EgressContractError(\n            "confirmation pricing snapshot is only valid for a non-dispatched "\n            "attempt without a reservation"\n        )\n\n    registry = registry or load_default_provider_registry()\n    with persistence._immediate_transaction() as connection:\n        _bind_attempt_identity(\n            connection,\n            ai_job_id=ai_job_id,\n            binding=binding,\n            fallback_index=fallback_index,\n        )\n        pricing_version = (\n            _confirmation_pricing_version(\n                connection,\n                ai_job_id=ai_job_id,\n                binding=binding,\n                fallback_index=fallback_index,\n            )\n            if use_confirmation_pricing_snapshot\n            else resolve_model_pricing(\n                registry, binding.provider_id, binding.model_id\n            ).pricing_version\n        )\n''',
    )
    replace_once(
        root,
        transaction,
        '''\n\ndef _bind_attempt_identity(\n''',
        '''\n\ndef _confirmation_pricing_version(\n    connection: sqlite3.Connection,\n    *,\n    ai_job_id: str,\n    binding: ProviderBinding,\n    fallback_index: int,\n) -> str:\n    job = connection.execute(\n        "SELECT task_kind, decision_reason, route_reason_json "\n        "FROM ai_jobs WHERE id = ?",\n        (ai_job_id,),\n    ).fetchone()\n    if job is None:\n        raise persistence.EgressStateError("ai_job was not found")\n    try:\n        route_metadata = json.loads(job["route_reason_json"])\n    except (TypeError, json.JSONDecodeError) as exc:\n        raise EgressContractError(\n            "confirmation pricing snapshot metadata is malformed"\n        ) from exc\n    if not isinstance(route_metadata, dict):\n        raise EgressContractError(\n            "confirmation pricing snapshot metadata is malformed"\n        )\n    ticket_id = route_metadata.get("egress_confirmation_ticket_id")\n    if not isinstance(ticket_id, str) or not ticket_id.strip():\n        raise EgressContractError(\n            "confirmation pricing snapshot ticket is missing"\n        )\n    ticket_id = ticket_id.strip()\n\n    snapshot = connection.execute(\n        """\n        SELECT ticket.state AS ticket_state,\n               ticket.decision_id AS ticket_decision_id,\n               ticket.packet_id AS ticket_packet_id,\n               ticket.packet_digest AS ticket_packet_digest,\n               ticket.provider_id AS ticket_provider_id,\n               ticket.model_id AS ticket_model_id,\n               decision.packet_id AS decision_packet_id,\n               decision.packet_digest AS decision_packet_digest,\n               decision.pricing_version AS pricing_version,\n               decision.reservation_id AS decision_reservation_id,\n               packet.packet_digest AS packet_digest,\n               packet.task_kind AS packet_task_kind,\n               packet.route_class AS packet_route_class,\n               packet.provider_id AS packet_provider_id,\n               packet.model_id AS packet_model_id,\n               packet.fallback_index AS packet_fallback_index\n        FROM egress_confirmation_tickets AS ticket\n        JOIN egress_decisions AS decision ON decision.id = ticket.decision_id\n        JOIN egress_packets AS packet ON packet.id = ticket.packet_id\n        WHERE ticket.id = ?\n        """,\n        (ticket_id,),\n    ).fetchone()\n    if snapshot is None:\n        raise EgressContractError(\n            "confirmation pricing snapshot ticket was not found"\n        )\n    if snapshot["ticket_state"] not in {"expired", "revoked"}:\n        raise EgressContractError(\n            "confirmation pricing snapshot requires an expired or revoked ticket"\n        )\n    if snapshot["decision_reservation_id"] is not None:\n        raise EgressContractError(\n            "confirmation pricing snapshot cannot reference a reserved decision"\n        )\n\n    expected_metadata = {\n        "egress_confirmation_ticket_id": ticket_id,\n        "egress_decision_id": snapshot["ticket_decision_id"],\n        "egress_packet_digest": snapshot["ticket_packet_digest"],\n        "fallback_attempt_index": fallback_index,\n        "fallback_chain_route": binding.route_class,\n        "fallback_model_id": binding.model_id,\n        "fallback_provider_id": binding.provider_id,\n    }\n    for key, expected in expected_metadata.items():\n        if route_metadata.get(key) != expected:\n            raise EgressContractError(\n                f"confirmation pricing snapshot metadata mismatch: {key}"\n            )\n    if job["decision_reason"] != f"confirmed_ticket:{ticket_id}":\n        raise EgressContractError(\n            "confirmation pricing snapshot job is not ticket-bound"\n        )\n\n    packet_identity = (\n        snapshot["packet_route_class"],\n        snapshot["packet_provider_id"],\n        snapshot["packet_model_id"],\n        int(snapshot["packet_fallback_index"]),\n    )\n    binding_identity = (\n        binding.route_class,\n        binding.provider_id,\n        binding.model_id,\n        fallback_index,\n    )\n    if packet_identity != binding_identity:\n        raise EgressContractError(\n            "confirmation pricing snapshot binding does not match the packet"\n        )\n    if (\n        snapshot["ticket_provider_id"],\n        snapshot["ticket_model_id"],\n    ) != (binding.provider_id, binding.model_id):\n        raise EgressContractError(\n            "confirmation pricing snapshot binding does not match the ticket"\n        )\n    if (\n        snapshot["ticket_packet_id"] != snapshot["decision_packet_id"]\n        or snapshot["ticket_packet_digest"] != snapshot["decision_packet_digest"]\n        or snapshot["ticket_packet_digest"] != snapshot["packet_digest"]\n    ):\n        raise EgressContractError(\n            "confirmation pricing snapshot packet identity is inconsistent"\n        )\n    if job["task_kind"] != snapshot["packet_task_kind"]:\n        raise EgressContractError(\n            "confirmation pricing snapshot task kind does not match"\n        )\n    pricing_version = snapshot["pricing_version"]\n    if not isinstance(pricing_version, str) or not pricing_version.strip():\n        raise EgressContractError(\n            "confirmation pricing snapshot version is missing"\n        )\n    return pricing_version.strip()\n\n\ndef _bind_attempt_identity(\n''',
    )

    tests = "backend/tests/test_token_flow_external_reserved_transaction.py"
    replace_once(
        root,
        tests,
        "from __future__ import annotations\n\nimport pytest\n",
        "from __future__ import annotations\n\nfrom dataclasses import replace\n\nimport pytest\n",
    )
    replace_once(
        root,
        tests,
        "from app.modules.ai.provider_registry import load_default_provider_registry\n",
        "from app.modules.ai.provider_registry import load_default_provider_registry\n",
    )
    replace_once(
        root,
        tests,
        '''def test_persisted_pricing_version_is_rejected_for_dispatched_attempt(\n    monkeypatch, tmp_path\n) -> None:\n''',
        '''def test_confirmation_pricing_snapshot_is_rejected_for_dispatched_attempt(\n    monkeypatch, tmp_path\n) -> None:\n''',
    )
    replace_once(
        root,
        tests,
        '''    with pytest.raises(EgressContractError, match="persisted pricing version"):\n''',
        '''    with pytest.raises(EgressContractError, match="confirmation pricing snapshot"):\n''',
    )
    replace_once(
        root,
        tests,
        '''            registry=registry,\n            persisted_pricing_version="ticket-snapshot",\n        )\n''',
        '''            registry=registry,\n            use_confirmation_pricing_snapshot=True,\n        )\n''',
    )
    tests_path = root / tests
    tests_path.write_text(
        tests_path.read_text(encoding="utf-8")
        + '''\n\ndef test_generic_queued_job_cannot_use_confirmation_pricing_snapshot(\n    monkeypatch, tmp_path\n) -> None:\n    _initialize(monkeypatch, tmp_path)\n    registry = load_default_provider_registry()\n    binding = registry.bindings["external:cheap"]\n    job_id = create_queued_ai_job(\n        task_kind="synthesis",\n        requested_route_class="external:cheap",\n        selected_route_class="external:cheap",\n        provider_id="deepseek",\n        model_id="deepseek-v4-pro",\n        decision_reason="ordinary-external-job",\n        prompt_digest="sha256:" + "c" * 64,\n        context_digest=None,\n        context_sources=None,\n        route_metadata={"fallback_attempt_index": 0},\n    ).ai_job_id\n    flow = create_flow(task_kind="synthesis", requested_route_class="external:cheap")\n\n    with pytest.raises(EgressContractError, match="snapshot ticket is missing"):\n        finalize_external_attempt(\n            flow_id=str(flow["id"]),\n            ai_job_id=job_id,\n            binding=binding,\n            fallback_index=0,\n            status="config_error",\n            response=None,\n            latency_ms=1,\n            error_type="config_error",\n            adapter_invoked=False,\n            dispatch_state=AIExternalDispatchState.not_started,\n            requested_output_ceiling=32,\n            effective_output_ceiling=32,\n            outcome_reason="external_not_sent",\n            registry=registry,\n            use_confirmation_pricing_snapshot=True,\n        )\n\n    from app.core.database import open_sqlite_connection\n\n    with open_sqlite_connection() as connection:\n        job = connection.execute(\n            "SELECT status, flow_id, fallback_index FROM ai_jobs WHERE id = ?",\n            (job_id,),\n        ).fetchone()\n        linked = connection.execute(\n            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?",\n            (flow["id"],),\n        ).fetchone()["n"]\n    assert tuple(job) == ("queued", None, None)\n    assert linked == 0\n\n\ndef test_mismatched_confirmation_snapshot_metadata_rolls_back(\n    monkeypatch, tmp_path\n) -> None:\n    _initialize(monkeypatch, tmp_path)\n    registry = load_default_provider_registry()\n    binding = registry.bindings["external:cheap"]\n    preparation = prepare_egress_attempt(_material(), registry=registry)\n    assert preparation.ticket_id is not None\n\n    providers = dict(registry.providers)\n    providers["deepseek"] = replace(providers["deepseek"], enabled=False)\n    revoked_registry = replace(\n        registry,\n        providers=providers,\n        bindings={\n            route: candidate\n            for route, candidate in registry.bindings.items()\n            if candidate.provider_id != "deepseek"\n        },\n    )\n    consumed = consume_confirmation_ticket(\n        preparation.ticket_id, registry=revoked_registry\n    )\n    assert consumed.authorized is False\n    assert consumed.reason_code == "ticket_binding_or_policy_drift"\n\n    job_id = create_queued_ai_job(\n        task_kind="synthesis",\n        requested_route_class="external:cheap",\n        selected_route_class="external:cheap",\n        provider_id="deepseek",\n        model_id="deepseek-v4-pro",\n        decision_reason=f"confirmed_ticket:{consumed.ticket_id}",\n        prompt_digest="sha256:" + "d" * 64,\n        context_digest=None,\n        context_sources=None,\n        route_metadata={\n            "egress_confirmation_ticket_id": consumed.ticket_id,\n            "egress_decision_id": "forged-decision",\n            "egress_packet_digest": consumed.packet_digest,\n            "fallback_attempt_index": consumed.fallback_index,\n            "fallback_chain_route": consumed.route_class,\n            "fallback_model_id": consumed.model_id,\n            "fallback_provider_id": consumed.provider_id,\n        },\n    ).ai_job_id\n    flow = create_flow(task_kind="synthesis", requested_route_class="external:cheap")\n\n    with pytest.raises(EgressContractError, match="metadata mismatch"):\n        finalize_external_attempt(\n            flow_id=str(flow["id"]),\n            ai_job_id=job_id,\n            binding=binding,\n            fallback_index=0,\n            status="config_error",\n            response=None,\n            latency_ms=1,\n            error_type="config_error",\n            adapter_invoked=False,\n            dispatch_state=AIExternalDispatchState.not_started,\n            requested_output_ceiling=32,\n            effective_output_ceiling=32,\n            outcome_reason="ticket_binding_or_policy_drift",\n            registry=revoked_registry,\n            use_confirmation_pricing_snapshot=True,\n        )\n\n    from app.core.database import open_sqlite_connection\n\n    with open_sqlite_connection() as connection:\n        job = connection.execute(\n            "SELECT status, flow_id, fallback_index FROM ai_jobs WHERE id = ?",\n            (job_id,),\n        ).fetchone()\n        linked = connection.execute(\n            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?",\n            (flow["id"],),\n        ).fetchone()["n"]\n    assert tuple(job) == ("queued", None, None)\n    assert linked == 0\n''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: tmp_apply_wp1_pricing_snapshot.py <target-root>")
    main(Path(sys.argv[1]).resolve())
