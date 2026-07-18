from __future__ import annotations

import json
import time
from dataclasses import dataclass

from app.core.database import open_sqlite_connection
from app.modules.ai.budget import evaluate_provider_budget_gate
from app.modules.ai.context_builder import canonical_digest, context_sources_manifest
from app.modules.ai.contracts import AIProviderAdapter, AIRequest, AIResponse, RoutingDecision
from app.modules.ai.egress_lifecycle import (
    EgressTicketConsumption,
    consume_confirmation_ticket,
    reconcile_reserved_attempt,
    start_reserved_attempt,
)
from app.modules.ai.egress_persistence import EgressStateError
from app.modules.ai.egress_policy import EgressPolicyConfig, load_default_egress_policy
from app.modules.ai.egress_runtime import (
    _load_packet,
    _release_before_network_strict,
    _response_status,
)
from app.modules.ai.egress_spine import (
    EgressSpineStateError,
    create_queued_ai_job,
    finalize_queued_ai_job,
)
from app.modules.ai.execution import (
    AiTaskOutcome,
    _ai_task_type_for,
    _create_proposed_records_from_response,
    _default_adapters,
    _prompt_for_task,
)
from app.modules.ai.provider_registry import ProviderRegistry, load_default_provider_registry
from app.modules.ai.settings import get_ai_settings
from app.modules.ai.token_flow_runtime import normalize_finish_reason


@dataclass(frozen=True)
class ConfirmedTicketExecution:
    ticket_id: str
    workspace_id: str | None
    outcome: AiTaskOutcome


@dataclass(frozen=True)
class _TicketMetadata:
    task_kind: str
    workspace_id: str | None
    source_count: int
    trigger_ids: tuple[str, ...]
    packet_digest: str
    provider_id: str
    model_id: str
    route_class: str
    fallback_index: int
    max_output_tokens: int


def run_confirmation_ticket(
    ticket_id: str,
    *,
    adapters: dict[str, AIProviderAdapter] | None = None,
    registry: ProviderRegistry | None = None,
    policy: EgressPolicyConfig | None = None,
) -> ConfirmedTicketExecution:
    """Consume and execute exactly one server-owned 059b confirmation ticket.

    The caller supplies only ``ticket_id``. Prompt, context, route, provider, model,
    fallback index, and output cap are reloaded from persisted rows. A confirmed ticket
    never opens a fallback chain: it authorizes only its exact concrete binding.
    """

    started_at = time.perf_counter()
    registry = registry or load_default_provider_registry()
    policy = policy or load_default_egress_policy()
    adapter_table = adapters if adapters is not None else _default_adapters()

    # Read non-secret audit metadata before ticket consumption. If this row is missing
    # or malformed, fail before the pending->consumed CAS so no orphan reservation can
    # be created without a corresponding terminal ai_job.
    metadata = _load_ticket_metadata(ticket_id)
    consumed = consume_confirmation_ticket(
        ticket_id,
        registry=registry,
        policy=policy,
    )
    base_route_metadata = _route_metadata(consumed, metadata)

    if not _ticket_metadata_matches_consumption(metadata, consumed):
        packet = _safe_load_consumed_packet(consumed)
        outcome = _terminal_outcome(
            consumed=consumed,
            metadata=metadata,
            route_metadata={**base_route_metadata, "ticket_metadata_drift": True},
            status="config_error",
            reason_code="ticket_metadata_drift",
            error_type="config_error",
            started_at=started_at,
            reservation_id=consumed.reservation_id,
            packet=packet,
        )
        return ConfirmedTicketExecution(ticket_id, metadata.workspace_id, outcome)

    if not consumed.authorized:
        outcome = _terminal_outcome(
            consumed=consumed,
            metadata=metadata,
            route_metadata=base_route_metadata,
            status="config_error",
            reason_code=consumed.reason_code,
            error_type=consumed.reason_code,
            started_at=started_at,
            reservation_id=None,
            packet=None,
        )
        return ConfirmedTicketExecution(ticket_id, metadata.workspace_id, outcome)

    reservation_id = consumed.reservation_id
    if reservation_id is None or consumed.packet_json is None:
        raise EgressSpineStateError("authorized confirmation ticket omitted reservation or packet")

    try:
        packet = _load_packet(consumed.packet_json)
    except Exception as exc:
        outcome = _terminal_outcome(
            consumed=consumed,
            metadata=metadata,
            route_metadata=base_route_metadata,
            status="config_error",
            reason_code="persisted_packet_invalid",
            error_type=type(exc).__name__,
            started_at=started_at,
            reservation_id=reservation_id,
            packet=None,
        )
        return ConfirmedTicketExecution(ticket_id, metadata.workspace_id, outcome)

    gate = evaluate_provider_budget_gate(get_ai_settings(), consumed.provider_id)
    if not gate.allowed:
        outcome = _terminal_outcome(
            consumed=consumed,
            metadata=metadata,
            route_metadata={**base_route_metadata, "provider_gate_reason": gate.blocking_reason},
            status="config_error",
            reason_code=gate.blocking_reason or "provider_gate_blocked",
            error_type="config_error",
            started_at=started_at,
            reservation_id=reservation_id,
            packet=packet,
        )
        return ConfirmedTicketExecution(ticket_id, metadata.workspace_id, outcome)

    adapter = adapter_table.get(consumed.provider_id)
    if adapter is None:
        outcome = _terminal_outcome(
            consumed=consumed,
            metadata=metadata,
            route_metadata={**base_route_metadata, "adapter_unavailable": True},
            status="config_error",
            reason_code="adapter_unavailable",
            error_type="config_error",
            started_at=started_at,
            reservation_id=reservation_id,
            packet=packet,
        )
        return ConfirmedTicketExecution(ticket_id, metadata.workspace_id, outcome)

    queued = _create_confirmation_job(
        consumed=consumed,
        metadata=metadata,
        route_metadata=base_route_metadata,
        packet=packet,
    )
    context_digest = _context_digest(packet)

    try:
        reserved = start_reserved_attempt(
            reservation_id,
            ai_job_id=queued.ai_job_id,
        )
        if reserved.packet_json != consumed.packet_json:
            raise EgressSpineStateError("ticket packet changed between consumption and attempt start")
        if (
            reserved.provider_id,
            reserved.model_id,
            reserved.route_class,
            reserved.fallback_index,
            reserved.max_output_tokens,
        ) != (
            consumed.provider_id,
            consumed.model_id,
            consumed.route_class,
            consumed.fallback_index,
            consumed.max_output_tokens,
        ):
            raise EgressSpineStateError("ticket reservation binding changed before execution")
        reserved_packet = _load_packet(reserved.packet_json)
        request = AIRequest(
            task_type=_ai_task_type_for(metadata.task_kind),
            prompt=_prompt_for_task(
                metadata.task_kind,
                reserved_packet["context_blocks"],
                reserved_packet["prompt"],
            ),
            model_preference=reserved.model_id,
            max_output_tokens=reserved.max_output_tokens,
            metadata={
                "egress_confirmation_ticket_id": consumed.ticket_id,
                "egress_decision_id": consumed.decision_id,
                "egress_packet_digest": consumed.packet_digest,
                "selected_route_class": consumed.route_class,
            },
        )
    except Exception as exc:
        finalize_queued_ai_job(
            queued.ai_job_id,
            status="config_error",
            response=None,
            latency_ms=_elapsed_ms(started_at),
            error_type=type(exc).__name__,
        )
        _release_before_network_strict(
            reservation_id=reservation_id,
            ai_job_id=queued.ai_job_id,
        )
        outcome = _outcome(
            consumed=consumed,
            metadata=metadata,
            ledger_id=queued.ai_job_id,
            status="config_error",
            response=None,
            error_type=type(exc).__name__,
            reason_code="egress_start_failed",
            context_digest=context_digest,
            blocked=True,
        )
        return ConfirmedTicketExecution(ticket_id, metadata.workspace_id, outcome)

    try:
        response = adapter.complete(request)
    except Exception as exc:
        finalize_queued_ai_job(
            queued.ai_job_id,
            status="provider_error",
            response=None,
            latency_ms=_elapsed_ms(started_at),
            error_type=type(exc).__name__,
        )
        reconcile_reserved_attempt(
            reservation_id,
            ai_job_id=queued.ai_job_id,
            network_attempt=True,
            usage_source="estimated",
            registry=registry,
        )
        outcome = _outcome(
            consumed=consumed,
            metadata=metadata,
            ledger_id=queued.ai_job_id,
            status="provider_error",
            response=None,
            error_type=type(exc).__name__,
            reason_code="ticket_consumed",
            context_digest=context_digest,
            blocked=False,
        )
        return ConfirmedTicketExecution(ticket_id, metadata.workspace_id, outcome)

    status, error_type = _response_status(response)
    try:
        finalize_queued_ai_job(
            queued.ai_job_id,
            status=status,
            response=response,
            latency_ms=_elapsed_ms(started_at),
            error_type=error_type,
        )
    except EgressSpineStateError as exc:
        finalize_queued_ai_job(
            queued.ai_job_id,
            status="provider_error",
            response=None,
            latency_ms=_elapsed_ms(started_at),
            error_type=type(exc).__name__,
        )
        reconcile_reserved_attempt(
            reservation_id,
            ai_job_id=queued.ai_job_id,
            network_attempt=True,
            usage_source="estimated",
            registry=registry,
        )
        outcome = _outcome(
            consumed=consumed,
            metadata=metadata,
            ledger_id=queued.ai_job_id,
            status="provider_error",
            response=None,
            error_type=type(exc).__name__,
            reason_code="response_binding_mismatch",
            context_digest=context_digest,
            blocked=False,
        )
        return ConfirmedTicketExecution(ticket_id, metadata.workspace_id, outcome)

    reconcile_reserved_attempt(
        reservation_id,
        ai_job_id=queued.ai_job_id,
        network_attempt=True,
        actual_input_tokens=response.usage.input_tokens,
        actual_output_tokens=response.usage.output_tokens,
        usage_source=response.usage.usage_source.value,
        registry=registry,
    )
    outcome = _outcome(
        consumed=consumed,
        metadata=metadata,
        ledger_id=queued.ai_job_id,
        status=status,
        response=response,
        error_type=error_type,
        reason_code="ticket_consumed",
        context_digest=context_digest,
        blocked=False,
    )
    if status == "success" and normalize_finish_reason(
        response.finish_reason, failed=response.error is not None
    ) != "length":
        proposed_ids, parse_error = _create_proposed_records_from_response(
            task_kind=metadata.task_kind,
            response=response,
            ledger_id=queued.ai_job_id,
            workspace_id=metadata.workspace_id,
        )
        outcome.proposed_record_ids = proposed_ids
        outcome.records_parse_error = parse_error
    return ConfirmedTicketExecution(ticket_id, metadata.workspace_id, outcome)


def _load_ticket_metadata(ticket_id: str) -> _TicketMetadata:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT packet.task_kind, packet.workspace_id, decision.source_count,
                   ticket.trigger_ids_json, ticket.packet_digest,
                   packet.provider_id, packet.model_id, packet.route_class,
                   packet.fallback_index, packet.max_output_tokens
            FROM egress_confirmation_tickets AS ticket
            JOIN egress_decisions AS decision ON decision.id = ticket.decision_id
            JOIN egress_packets AS packet ON packet.id = ticket.packet_id
            WHERE ticket.id = ?
            """,
            (ticket_id,),
        ).fetchone()
    if row is None:
        raise EgressStateError("confirmation ticket metadata was not found")
    try:
        trigger_ids = json.loads(row["trigger_ids_json"])
    except (TypeError, json.JSONDecodeError) as exc:
        raise EgressStateError("confirmation ticket trigger metadata is malformed") from exc
    if not isinstance(trigger_ids, list) or not all(isinstance(value, str) for value in trigger_ids):
        raise EgressStateError("confirmation ticket trigger metadata is malformed")
    return _TicketMetadata(
        task_kind=str(row["task_kind"]),
        workspace_id=row["workspace_id"],
        source_count=int(row["source_count"]),
        trigger_ids=tuple(trigger_ids),
        packet_digest=str(row["packet_digest"]),
        provider_id=str(row["provider_id"]),
        model_id=str(row["model_id"]),
        route_class=str(row["route_class"]),
        fallback_index=int(row["fallback_index"]),
        max_output_tokens=int(row["max_output_tokens"]),
    )


def _ticket_metadata_matches_consumption(
    metadata: _TicketMetadata,
    consumed: EgressTicketConsumption,
) -> bool:
    return (
        metadata.packet_digest,
        metadata.provider_id,
        metadata.model_id,
        metadata.route_class,
        metadata.fallback_index,
        metadata.max_output_tokens,
    ) == (
        consumed.packet_digest,
        consumed.provider_id,
        consumed.model_id,
        consumed.route_class,
        consumed.fallback_index,
        consumed.max_output_tokens,
    )


def _safe_load_consumed_packet(
    consumed: EgressTicketConsumption,
) -> dict[str, object] | None:
    if consumed.packet_json is None:
        return None
    try:
        return _load_packet(consumed.packet_json)
    except Exception:
        return None


def _create_confirmation_job(
    *,
    consumed: EgressTicketConsumption,
    metadata: _TicketMetadata,
    route_metadata: dict[str, object],
    packet: dict[str, object] | None,
):
    blocks = packet["context_blocks"] if packet is not None else []
    prompt_digest = (
        canonical_digest({"effective_packet_prompt": packet["prompt"]})
        if packet is not None
        else None
    )
    context_digest = canonical_digest(blocks) if blocks else None
    context_sources = context_sources_manifest(blocks) if blocks else None
    return create_queued_ai_job(
        task_kind=metadata.task_kind,
        requested_route_class=consumed.route_class,
        selected_route_class=consumed.route_class,
        provider_id=consumed.provider_id,
        model_id=consumed.model_id,
        decision_reason=f"confirmed_ticket:{consumed.ticket_id}",
        prompt_digest=prompt_digest,
        context_digest=context_digest,
        context_sources=context_sources,
        route_metadata=route_metadata,
    )


def _terminal_outcome(
    *,
    consumed: EgressTicketConsumption,
    metadata: _TicketMetadata,
    route_metadata: dict[str, object],
    status: str,
    reason_code: str,
    error_type: str,
    started_at: float,
    reservation_id: str | None,
    packet: dict[str, object] | None,
) -> AiTaskOutcome:
    queued = _create_confirmation_job(
        consumed=consumed,
        metadata=metadata,
        route_metadata=route_metadata,
        packet=packet,
    )
    try:
        finalize_queued_ai_job(
            queued.ai_job_id,
            status=status,
            response=None,
            latency_ms=_elapsed_ms(started_at),
            error_type=error_type,
        )
    finally:
        if reservation_id is not None:
            _release_before_network_strict(
                reservation_id=reservation_id,
                ai_job_id=queued.ai_job_id,
            )
    return _outcome(
        consumed=consumed,
        metadata=metadata,
        ledger_id=queued.ai_job_id,
        status=status,
        response=None,
        error_type=error_type,
        reason_code=reason_code,
        context_digest=_context_digest(packet),
        blocked=True,
    )


def _outcome(
    *,
    consumed: EgressTicketConsumption,
    metadata: _TicketMetadata,
    ledger_id: str,
    status: str,
    response: AIResponse | None,
    error_type: str | None,
    reason_code: str,
    context_digest: str | None,
    blocked: bool,
) -> AiTaskOutcome:
    decision = RoutingDecision(
        provider_id=consumed.provider_id,
        model_id=consumed.model_id,
        blocked=blocked,
        blocked_reason=reason_code if blocked else None,
        decision_reason=(
            f"egress_ticket:{reason_code}"
            if blocked
            else f"confirmed_ticket:{consumed.ticket_id}"
        ),
    )
    return AiTaskOutcome(
        status=status,
        ledger_id=ledger_id,
        selected_route_class=consumed.route_class,
        decision=decision,
        response=response,
        error_type=error_type,
        context_digest=context_digest,
        context_sources_count=metadata.source_count,
        egress_decision_id=consumed.decision_id,
        egress_packet_digest=consumed.packet_digest,
        egress_ticket_id=consumed.ticket_id,
        egress_reservation_id=consumed.reservation_id,
        egress_reason_code=reason_code,
        egress_trigger_ids=metadata.trigger_ids,
    )


def _route_metadata(
    consumed: EgressTicketConsumption,
    metadata: _TicketMetadata,
) -> dict[str, object]:
    return {
        "confirmation_mode": "ticket_id_only",
        "egress_confirmation_ticket_id": consumed.ticket_id,
        "egress_decision_id": consumed.decision_id,
        "egress_packet_digest": consumed.packet_digest,
        "egress_reason_code": consumed.reason_code,
        "egress_reservation_id": consumed.reservation_id,
        "egress_trigger_ids": list(metadata.trigger_ids),
        "fallback_attempt_index": consumed.fallback_index,
        "fallback_chain_route": consumed.route_class,
        "fallback_model_id": consumed.model_id,
        "fallback_provider_id": consumed.provider_id,
    }


def _context_digest(packet: dict[str, object] | None) -> str | None:
    if packet is None:
        return None
    blocks = packet["context_blocks"]
    return canonical_digest(blocks) if blocks else None


def _elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)
