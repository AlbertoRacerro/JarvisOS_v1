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
        "    max_output_tokens: int\n\n\ndef run_confirmation_ticket(",
        "    max_output_tokens: int\n    pricing_version: str\n\n\ndef run_confirmation_ticket(",
    )
    replace_once(
        root,
        confirmation,
        '''    flow = get_confirmation_flow_for_ticket(ticket_id)\n    flow_id = str(flow["id"])\n    binding = _binding_from_ticket(metadata, registry)\n\n    consumed = consume_confirmation_ticket(\n        ticket_id,\n        registry=registry,\n        policy=policy,\n    )\n    activate_confirmation_flow(flow_id=flow_id, ticket_id=ticket_id)\n''',
        '''    flow = get_confirmation_flow_for_ticket(ticket_id)\n    flow_id = str(flow["id"])\n\n    consumed = consume_confirmation_ticket(\n        ticket_id,\n        registry=registry,\n        policy=policy,\n    )\n    binding = (\n        _binding_from_ticket(metadata, registry)\n        if consumed.authorized\n        else _persisted_external_binding(metadata)\n    )\n    activate_confirmation_flow(flow_id=flow_id, ticket_id=ticket_id)\n''',
    )
    replace_once(
        root,
        confirmation,
        '''                   decision.source_count,\n                   ticket.trigger_ids_json, ticket.packet_digest,\n''',
        '''                   decision.source_count, decision.pricing_version,\n                   ticket.trigger_ids_json, ticket.packet_digest,\n''',
    )
    replace_once(
        root,
        confirmation,
        '''        fallback_index=int(row["fallback_index"]),\n        max_output_tokens=int(row["max_output_tokens"]),\n    )\n''',
        '''        fallback_index=int(row["fallback_index"]),\n        max_output_tokens=int(row["max_output_tokens"]),\n        pricing_version=str(row["pricing_version"]),\n    )\n''',
    )
    replace_once(
        root,
        confirmation,
        '''        outcome_reason=reason_code,\n        reservation_id=reservation_id,\n        registry=registry,\n    )\n    outcome = _outcome(\n''',
        '''        outcome_reason=reason_code,\n        reservation_id=reservation_id,\n        registry=registry,\n        persisted_pricing_version=(\n            metadata.pricing_version if reservation_id is None else None\n        ),\n    )\n    outcome = _outcome(\n''',
    )
    replace_once(
        root,
        confirmation,
        "def _route_metadata(\n",
        '''def _persisted_external_binding(metadata: _TicketMetadata) -> ProviderBinding:\n    """Rebuild non-dispatched identity from the server-owned ticket snapshot."""\n\n    return ProviderBinding(\n        route_class=metadata.route_class,\n        provider_id=metadata.provider_id,\n        model_id=metadata.model_id,\n        requires_network=True,\n        max_output_tokens=metadata.max_output_tokens,\n        execution_class="external_provider",\n        context_window_tokens=None,\n    )\n\n\ndef _route_metadata(\n''',
    )

    transaction = "backend/app/modules/ai/token_flow_external_transaction.py"
    replace_once(
        root,
        transaction,
        '''    reservation_id: str | None = None,\n    registry: ProviderRegistry | None = None,\n    now: datetime | None = None,\n''',
        '''    reservation_id: str | None = None,\n    registry: ProviderRegistry | None = None,\n    persisted_pricing_version: str | None = None,\n    now: datetime | None = None,\n''',
    )
    replace_once(
        root,
        transaction,
        '''    registry = registry or load_default_provider_registry()\n    pricing = resolve_model_pricing(registry, binding.provider_id, binding.model_id)\n    with persistence._immediate_transaction() as connection:\n''',
        '''    registry = registry or load_default_provider_registry()\n    if persisted_pricing_version is not None:\n        if (\n            reservation_id is not None\n            or adapter_invoked\n            or dispatch_state is not AIExternalDispatchState.not_started\n            or response is not None\n        ):\n            raise EgressContractError(\n                "persisted pricing version is only valid for a non-dispatched "\n                "attempt without a reservation"\n            )\n        if (\n            not isinstance(persisted_pricing_version, str)\n            or not persisted_pricing_version.strip()\n        ):\n            raise EgressContractError(\n                "persisted pricing version must be non-empty text"\n            )\n        pricing_version = persisted_pricing_version.strip()\n    else:\n        pricing_version = resolve_model_pricing(\n            registry, binding.provider_id, binding.model_id\n        ).pricing_version\n    with persistence._immediate_transaction() as connection:\n''',
    )
    target = root / transaction
    text = target.read_text(encoding="utf-8")
    old_pricing = "pricing_version=pricing.pricing_version"
    count = text.count(old_pricing)
    if count != 3:
        raise SystemExit(f"{transaction}: expected 3 pricing uses, found {count}")
    target.write_text(
        text.replace(old_pricing, "pricing_version=pricing_version"),
        encoding="utf-8",
    )

    confirmation_tests = root / "backend/tests/test_ai_egress_confirmation.py"
    confirmation_tests.write_text(
        confirmation_tests.read_text(encoding="utf-8")
        + '''\n\ndef _assert_registry_drift_terminalized(\n    ticket_id: str, outcome, adapter: _Adapter\n) -> None:\n    assert outcome.status == "config_error"\n    assert outcome.egress_reason_code == "ticket_binding_or_policy_drift"\n    assert outcome.flow_id is not None\n    assert adapter.requests == []\n    with open_sqlite_connection() as connection:\n        ticket = connection.execute(\n            "SELECT state, revocation_reason "\n            "FROM egress_confirmation_tickets WHERE id = ?",\n            (ticket_id,),\n        ).fetchone()\n        decision = connection.execute(\n            "SELECT decision.pricing_version "\n            "FROM egress_confirmation_tickets AS ticket "\n            "JOIN egress_decisions AS decision ON decision.id = ticket.decision_id "\n            "WHERE ticket.id = ?",\n            (ticket_id,),\n        ).fetchone()\n        job = connection.execute(\n            "SELECT flow_id, execution_class, adapter_invoked, "\n            "external_dispatch_state, accounting_basis, "\n            "accounted_provider_spend_usd_decimal, pricing_version "\n            "FROM ai_jobs WHERE id = ?",\n            (outcome.ledger_id,),\n        ).fetchone()\n        flow = connection.execute(\n            "SELECT state, terminal_reason, terminal_attempt_id, "\n            "external_provider_spend_usd_decimal "\n            "FROM ai_flows WHERE id = ?",\n            (outcome.flow_id,),\n        ).fetchone()\n    assert tuple(ticket) == ("revoked", "ticket_binding_or_policy_drift")\n    assert job["flow_id"] == outcome.flow_id\n    assert job["execution_class"] == "external_provider"\n    assert job["adapter_invoked"] == 0\n    assert job["external_dispatch_state"] == "not_started"\n    assert job["accounting_basis"] == "external_not_sent"\n    assert job["accounted_provider_spend_usd_decimal"] == "0"\n    assert job["pricing_version"] == decision["pricing_version"]\n    assert tuple(flow) == (\n        "failed_terminal",\n        "ticket_binding_or_policy_drift",\n        outcome.ledger_id,\n        "0",\n    )\n\n\ndef test_disabled_provider_revokes_ticket_and_terminalizes_paused_flow(\n    monkeypatch,\n) -> None:\n    ticket_id = _pending_ticket(monkeypatch)\n    registry = load_default_provider_registry()\n    providers = dict(registry.providers)\n    providers["deepseek"] = replace(providers["deepseek"], enabled=False)\n    drifted_registry = replace(\n        registry,\n        providers=providers,\n        bindings={\n            route: binding\n            for route, binding in registry.bindings.items()\n            if binding.provider_id != "deepseek"\n        },\n    )\n    adapter = _Adapter("deepseek", response=_success_response())\n\n    outcome = run_confirmation_ticket(\n        ticket_id,\n        adapters={"deepseek": adapter},\n        registry=drifted_registry,\n    ).outcome\n\n    _assert_registry_drift_terminalized(ticket_id, outcome, adapter)\n\n\ndef test_removed_model_revokes_ticket_and_terminalizes_paused_flow(\n    monkeypatch,\n) -> None:\n    ticket_id = _pending_ticket(monkeypatch)\n    registry = load_default_provider_registry()\n    models = dict(registry.models)\n    models.pop(("deepseek", "deepseek-v4-pro"))\n    drifted_registry = replace(\n        registry,\n        models=models,\n        bindings={\n            route: binding\n            for route, binding in registry.bindings.items()\n            if (binding.provider_id, binding.model_id)\n            != ("deepseek", "deepseek-v4-pro")\n        },\n    )\n    adapter = _Adapter("deepseek", response=_success_response())\n\n    outcome = run_confirmation_ticket(\n        ticket_id,\n        adapters={"deepseek": adapter},\n        registry=drifted_registry,\n    ).outcome\n\n    _assert_registry_drift_terminalized(ticket_id, outcome, adapter)\n''',
        encoding="utf-8",
    )

    reserved_tests = "backend/tests/test_token_flow_external_reserved_transaction.py"
    replace_once(
        root,
        reserved_tests,
        "from app.modules.ai.egress_service import EgressPacketMaterial\n",
        "from app.modules.ai.egress_service import EgressContractError, EgressPacketMaterial\n",
    )
    reserved_path = root / reserved_tests
    reserved_path.write_text(
        reserved_path.read_text(encoding="utf-8")
        + '''\n\ndef test_persisted_pricing_version_is_rejected_for_dispatched_attempt(\n    monkeypatch, tmp_path\n) -> None:\n    _initialize(monkeypatch, tmp_path)\n    binding, registry, reservation_id, job_id = _started_reservation()\n    flow = create_flow(task_kind="synthesis", requested_route_class="external:cheap")\n\n    with pytest.raises(EgressContractError, match="persisted pricing version"):\n        finalize_external_attempt(\n            flow_id=str(flow["id"]),\n            ai_job_id=job_id,\n            binding=binding,\n            fallback_index=0,\n            status="success",\n            response=_response(),\n            latency_ms=2,\n            error_type=None,\n            adapter_invoked=True,\n            dispatch_state=AIExternalDispatchState.started,\n            requested_output_ceiling=32,\n            effective_output_ceiling=32,\n            outcome_reason="success",\n            reservation_id=reservation_id,\n            registry=registry,\n            persisted_pricing_version="ticket-snapshot",\n        )\n''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: tmp_apply_wp1_revoked_binding.py <target-root>")
    main(Path(sys.argv[1]).resolve())
