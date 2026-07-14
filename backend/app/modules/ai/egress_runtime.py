from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Callable

from app.modules.ai import sensitivity
from app.modules.ai.context_builder import (
    ContextBlockError,
    assemble_prompt,
    canonical_digest,
    canonicalize_blocks,
    context_sources_manifest,
)
from app.modules.ai.contracts import (
    AIProviderAdapter,
    AIRequest,
    AIResponse,
    AITaskType,
    RoutingDecision,
)
from app.modules.ai.egress_authority import authorize_manual_context, authorize_prompt
from app.modules.ai.egress_lifecycle import (
    reconcile_reserved_attempt,
    start_reserved_attempt,
)
from app.modules.ai.egress_persistence import prepare_egress_attempt
from app.modules.ai.egress_policy import EXTERNAL_PROVIDER_OPERATION
from app.modules.ai.egress_service import EgressPacketMaterial, sha256_text
from app.modules.ai.egress_spine import (
    create_queued_ai_job,
    finalize_queued_ai_job,
    record_prepacket_egress_decision,
)
from app.modules.ai.execution_types import ProviderBinding
from app.modules.ai.provider_registry import (
    ProviderRegistry,
    load_default_provider_registry,
)
from app.modules.ai.settings import get_ai_settings

_LOCAL_SANITIZER_ROUTE = "local:fast"
_LEVEL_RANK = {"S0": 0, "S1": 1}


@dataclass(frozen=True)
class ExternalTaskOutcome:
    status: str
    ledger_id: str
    selected_route_class: str
    decision: RoutingDecision
    response: AIResponse | None
    error_type: str | None
    context_digest: str | None
    context_sources_count: int
    retryable_error_code: str | None
    egress_decision_id: str | None
    egress_packet_digest: str | None
    egress_ticket_id: str | None
    egress_reservation_id: str | None
    egress_reason_code: str | None
    egress_trigger_ids: tuple[str, ...]


def run_external_task(
    *,
    user_prompt: str,
    task_kind: str,
    selected_route_class: str,
    requested_route_class: str | None,
    context_blocks: list[dict[str, object]] | None,
    max_output_tokens: int | None,
    adapters: dict[str, AIProviderAdapter],
    bindings: dict[str, ProviderBinding] | None,
    workspace_id: str | None,
    context_build_error: str | None,
    external_blocked_reason: str | None,
    task_type_for: Callable[[str], AITaskType],
    task_prompt_for: Callable[[str, list[dict], str], str] | None = None,
    registry: ProviderRegistry | None = None,
) -> ExternalTaskOutcome:
    """Execute one external route through the mandatory 059b per-binding boundary."""

    from app.modules.ai.execution import resolve_binding

    registry = registry or load_default_provider_registry()
    binding_table = bindings if bindings is not None else registry.bindings
    binding, route_decision = resolve_binding(selected_route_class, binding_table)
    if binding is None:
        raise ValueError("run_external_task requires a resolved external route")
    chain = _binding_chain(
        route_class=selected_route_class,
        primary=binding,
        bindings=bindings,
        registry=registry,
    )
    prompt_builder = task_prompt_for or _default_task_prompt
    prior_retryable_error_code: str | None = None
    last_outcome: ExternalTaskOutcome | None = None

    for fallback_index, attempt_binding in enumerate(chain):
        outcome = _run_external_binding(
            user_prompt=user_prompt,
            task_kind=task_kind,
            selected_route_class=selected_route_class,
            requested_route_class=requested_route_class,
            context_blocks=context_blocks,
            max_output_tokens=max_output_tokens,
            adapters=adapters,
            workspace_id=workspace_id,
            context_build_error=context_build_error,
            external_blocked_reason=external_blocked_reason,
            task_type_for=task_type_for,
            task_prompt_for=prompt_builder,
            attempt_binding=attempt_binding,
            fallback_index=fallback_index,
            prior_retryable_error_code=prior_retryable_error_code,
            registry=registry,
        )
        last_outcome = outcome
        if (
            outcome.status == "provider_error"
            and outcome.retryable_error_code is not None
            and fallback_index + 1 < len(chain)
        ):
            prior_retryable_error_code = outcome.retryable_error_code
            continue
        return outcome

    if last_outcome is None:
        raise RuntimeError("external binding chain was unexpectedly empty")
    return last_outcome


def _run_external_binding(
    *,
    user_prompt: str,
    task_kind: str,
    selected_route_class: str,
    requested_route_class: str | None,
    context_blocks: list[dict[str, object]] | None,
    max_output_tokens: int | None,
    adapters: dict[str, AIProviderAdapter],
    workspace_id: str | None,
    context_build_error: str | None,
    external_blocked_reason: str | None,
    task_type_for: Callable[[str], AITaskType],
    task_prompt_for: Callable[[str, list[dict], str], str],
    attempt_binding: ProviderBinding,
    fallback_index: int,
    prior_retryable_error_code: str | None,
    registry: ProviderRegistry,
) -> ExternalTaskOutcome:
    started_at = time.perf_counter()
    prompt_digest = sha256_text(user_prompt)
    ai_prompt_digest = canonical_digest({"prompt": user_prompt})
    route_metadata = _route_metadata(
        selected_route_class=selected_route_class,
        fallback_index=fallback_index,
        binding=attempt_binding,
        prior_retryable_error_code=prior_retryable_error_code,
    )

    if not attempt_binding.requires_network:
        return _prepacket_outcome(
            result="deny",
            reason_code="egress_policy_error",
            prompt_digest=prompt_digest,
            ai_prompt_digest=ai_prompt_digest,
            context_digest=None,
            prompt_level=_prompt_floor_or_unknown(user_prompt),
            context_level="unknown",
            route_class=selected_route_class,
            requested_route_class=requested_route_class,
            task_kind=task_kind,
            binding=attempt_binding,
            fallback_index=fallback_index,
            workspace_id=workspace_id,
            source_count=0,
            included_count=0,
            withheld_count=0,
            route_metadata=route_metadata,
            started_at=started_at,
        )

    if context_build_error is not None:
        return _prepacket_outcome(
            result="pause",
            reason_code="context_build_error",
            prompt_digest=prompt_digest,
            ai_prompt_digest=ai_prompt_digest,
            context_digest=None,
            prompt_level=_prompt_floor_or_unknown(user_prompt),
            context_level="unknown",
            route_class=selected_route_class,
            requested_route_class=requested_route_class,
            task_kind=task_kind,
            binding=attempt_binding,
            fallback_index=fallback_index,
            workspace_id=workspace_id,
            source_count=0,
            included_count=0,
            withheld_count=0,
            route_metadata=route_metadata,
            started_at=started_at,
        )

    if external_blocked_reason is not None:
        return _prepacket_outcome(
            result="deny",
            reason_code="egress_policy_error",
            prompt_digest=prompt_digest,
            ai_prompt_digest=ai_prompt_digest,
            context_digest=None,
            prompt_level=_prompt_floor_or_unknown(user_prompt),
            context_level="unknown",
            route_class=selected_route_class,
            requested_route_class=requested_route_class,
            task_kind=task_kind,
            binding=attempt_binding,
            fallback_index=fallback_index,
            workspace_id=workspace_id,
            source_count=0,
            included_count=0,
            withheld_count=0,
            route_metadata={**route_metadata, "legacy_blocked_reason": external_blocked_reason},
            started_at=started_at,
        )

    try:
        blocks = canonicalize_blocks(context_blocks)
    except ContextBlockError:
        return _prepacket_outcome(
            result="pause",
            reason_code="context_malformed",
            prompt_digest=prompt_digest,
            ai_prompt_digest=ai_prompt_digest,
            context_digest=None,
            prompt_level=_prompt_floor_or_unknown(user_prompt),
            context_level="unknown",
            route_class=selected_route_class,
            requested_route_class=requested_route_class,
            task_kind=task_kind,
            binding=attempt_binding,
            fallback_index=fallback_index,
            workspace_id=workspace_id,
            source_count=0,
            included_count=0,
            withheld_count=0,
            route_metadata=route_metadata,
            started_at=started_at,
        )

    raw_context_digest = canonical_digest(blocks) if blocks else None
    if blocks and workspace_id is None:
        return _prepacket_outcome(
            result="pause",
            reason_code="manual_context_not_authorized",
            prompt_digest=prompt_digest,
            ai_prompt_digest=ai_prompt_digest,
            context_digest=raw_context_digest,
            prompt_level=_prompt_floor_or_unknown(user_prompt),
            context_level="unknown",
            route_class=selected_route_class,
            requested_route_class=requested_route_class,
            task_kind=task_kind,
            binding=attempt_binding,
            fallback_index=fallback_index,
            workspace_id=None,
            source_count=len(blocks),
            included_count=0,
            withheld_count=len(blocks),
            route_metadata=route_metadata,
            started_at=started_at,
        )

    context_authority = None
    if blocks:
        try:
            context_authority = authorize_manual_context(
                workspace_id=workspace_id or "",
                raw_blocks=blocks,
                budget_chars=load_default_provider_registry_context_budget(),
            )
        except Exception:
            context_authority = None
        if context_authority is None or context_authority.result != "eligible":
            withheld_count = (
                len(context_authority.withheld_manifest)
                if context_authority is not None
                else len(blocks)
            )
            return _prepacket_outcome(
                result="pause",
                reason_code="manual_context_not_authorized",
                prompt_digest=prompt_digest,
                ai_prompt_digest=ai_prompt_digest,
                context_digest=raw_context_digest,
                prompt_level=_prompt_floor_or_unknown(user_prompt),
                context_level="unknown",
                route_class=selected_route_class,
                requested_route_class=requested_route_class,
                task_kind=task_kind,
                binding=attempt_binding,
                fallback_index=fallback_index,
                workspace_id=workspace_id,
                source_count=len(blocks),
                included_count=0,
                withheld_count=withheld_count,
                route_metadata=route_metadata,
                started_at=started_at,
            )

    floor = sensitivity.deterministic_floor(user_prompt)
    if blocks and floor is None:
        return _prepacket_outcome(
            result="pause",
            reason_code="prompt_classification_required",
            prompt_digest=prompt_digest,
            ai_prompt_digest=ai_prompt_digest,
            context_digest=(
                context_authority.context_digest
                if context_authority is not None
                else raw_context_digest
            ),
            prompt_level="unknown",
            context_level=(
                context_authority.context_level
                if context_authority is not None
                else "unknown"
            ),
            route_class=selected_route_class,
            requested_route_class=requested_route_class,
            task_kind=task_kind,
            binding=attempt_binding,
            fallback_index=fallback_index,
            workspace_id=workspace_id,
            source_count=(
                len(context_authority.source_digests)
                if context_authority is not None
                else len(blocks)
            ),
            included_count=(
                len(context_authority.included_manifest)
                if context_authority is not None
                else 0
            ),
            withheld_count=0,
            route_metadata=route_metadata,
            started_at=started_at,
        )

    try:
        prompt_authority = authorize_prompt(
            raw_prompt=user_prompt,
            task_kind=task_kind,
            policy_mode=get_ai_settings().policy_mode,
            workspace_id=workspace_id,
            local_sanitizer_route=_LOCAL_SANITIZER_ROUTE,
            adapters=adapters,
            registry=registry,
        )
    except Exception:
        prompt_authority = None
    if prompt_authority is None:
        return _prepacket_outcome(
            result="pause",
            reason_code="prompt_sanitization_required",
            prompt_digest=prompt_digest,
            ai_prompt_digest=ai_prompt_digest,
            context_digest=(
                context_authority.context_digest
                if context_authority is not None
                else raw_context_digest
            ),
            prompt_level=floor or "unknown",
            context_level=(
                context_authority.context_level
                if context_authority is not None
                else "S0"
            ),
            route_class=selected_route_class,
            requested_route_class=requested_route_class,
            task_kind=task_kind,
            binding=attempt_binding,
            fallback_index=fallback_index,
            workspace_id=workspace_id,
            source_count=(
                len(context_authority.source_digests)
                if context_authority is not None
                else 0
            ),
            included_count=(
                len(context_authority.included_manifest)
                if context_authority is not None
                else 0
            ),
            withheld_count=0,
            route_metadata=route_metadata,
            started_at=started_at,
        )
    if prompt_authority.result != "eligible":
        return _prepacket_outcome(
            result="deny" if prompt_authority.result == "deny" else "pause",
            reason_code=prompt_authority.reason_code,
            prompt_digest=prompt_digest,
            ai_prompt_digest=ai_prompt_digest,
            context_digest=(
                context_authority.context_digest
                if context_authority is not None
                else raw_context_digest
            ),
            prompt_level=prompt_authority.prompt_level or "unknown",
            context_level=(
                context_authority.context_level
                if context_authority is not None
                else "S0"
            ),
            route_class=selected_route_class,
            requested_route_class=requested_route_class,
            task_kind=task_kind,
            binding=attempt_binding,
            fallback_index=fallback_index,
            workspace_id=workspace_id,
            source_count=(
                len(context_authority.source_digests)
                if context_authority is not None
                else 0
            ),
            included_count=(
                len(context_authority.included_manifest)
                if context_authority is not None
                else 0
            ),
            withheld_count=0,
            route_metadata=route_metadata,
            started_at=started_at,
        )

    effective_blocks = list(context_authority.blocks) if context_authority is not None else []
    context_level = context_authority.context_level if context_authority is not None else "S0"
    final_level = max(
        (prompt_authority.prompt_level or "S1", context_level),
        key=_LEVEL_RANK.__getitem__,
    )
    attempt_max = min(
        max_output_tokens if max_output_tokens is not None else attempt_binding.max_output_tokens,
        attempt_binding.max_output_tokens,
    )
    material = EgressPacketMaterial(
        operation=EXTERNAL_PROVIDER_OPERATION,
        task_kind=task_kind,
        route_class=selected_route_class,
        provider_id=attempt_binding.provider_id,
        model_id=attempt_binding.model_id,
        fallback_index=fallback_index,
        prompt=prompt_authority.effective_prompt or "",
        context_blocks=tuple(effective_blocks),
        prompt_level=prompt_authority.prompt_level or "S1",
        context_level=context_level,
        final_level=final_level,
        max_output_tokens=attempt_max,
        workspace_id=workspace_id,
        prompt_derivative_id=prompt_authority.prompt_derivative_id,
        included_manifest=(
            context_authority.included_manifest if context_authority is not None else ()
        ),
        withheld_manifest=(
            context_authority.withheld_manifest if context_authority is not None else ()
        ),
        budget_dropped_manifest=(
            context_authority.budget_dropped_manifest if context_authority is not None else ()
        ),
        source_digests=(
            context_authority.source_digests if context_authority is not None else ()
        ),
    )
    preparation = prepare_egress_attempt(material, registry=registry)
    route_metadata = {
        **route_metadata,
        "egress_decision_id": preparation.decision_id,
        "egress_packet_digest": preparation.packet_digest,
        "egress_reason_code": preparation.reason_code,
        "egress_ticket_id": preparation.ticket_id,
        "egress_trigger_ids": list(preparation.trigger_ids),
    }

    if preparation.result != "allow":
        terminal_status = "validation_error" if preparation.result == "pause" else "config_error"
        ledger_id = _terminal_ai_job(
            task_kind=task_kind,
            requested_route_class=requested_route_class,
            selected_route_class=selected_route_class,
            binding=attempt_binding,
            prompt_digest=ai_prompt_digest,
            context_digest=(
                context_authority.context_digest
                if context_authority is not None
                else None
            ),
            context_sources=(
                context_sources_manifest(effective_blocks) if effective_blocks else None
            ),
            route_metadata=route_metadata,
            status=terminal_status,
            error_type=preparation.reason_code,
            started_at=started_at,
        )
        decision = RoutingDecision(
            provider_id=attempt_binding.provider_id,
            model_id=attempt_binding.model_id,
            blocked=True,
            blocked_reason=preparation.reason_code,
            decision_reason=f"egress:{preparation.reason_code}",
        )
        return ExternalTaskOutcome(
            status=terminal_status,
            ledger_id=ledger_id,
            selected_route_class=selected_route_class,
            decision=decision,
            response=None,
            error_type=preparation.reason_code,
            context_digest=(
                context_authority.context_digest
                if context_authority is not None
                else None
            ),
            context_sources_count=len(effective_blocks),
            retryable_error_code=None,
            egress_decision_id=preparation.decision_id,
            egress_packet_digest=preparation.packet_digest,
            egress_ticket_id=preparation.ticket_id,
            egress_reservation_id=None,
            egress_reason_code=preparation.reason_code,
            egress_trigger_ids=preparation.trigger_ids,
        )

    adapter = adapters.get(attempt_binding.provider_id)
    if adapter is None:
        ledger_id = _terminal_ai_job(
            task_kind=task_kind,
            requested_route_class=requested_route_class,
            selected_route_class=selected_route_class,
            binding=attempt_binding,
            prompt_digest=ai_prompt_digest,
            context_digest=(
                context_authority.context_digest
                if context_authority is not None
                else None
            ),
            context_sources=(
                context_sources_manifest(effective_blocks) if effective_blocks else None
            ),
            route_metadata=route_metadata,
            status="config_error",
            error_type="adapter_unavailable",
            started_at=started_at,
        )
        _release_before_network(
            reservation_id=preparation.reservation_id,
            ai_job_id=ledger_id,
        )
        decision = RoutingDecision(
            provider_id=attempt_binding.provider_id,
            model_id=attempt_binding.model_id,
            blocked=True,
            blocked_reason="adapter_unavailable",
            decision_reason="egress:adapter_unavailable",
        )
        return ExternalTaskOutcome(
            status="config_error",
            ledger_id=ledger_id,
            selected_route_class=selected_route_class,
            decision=decision,
            response=None,
            error_type="adapter_unavailable",
            context_digest=(
                context_authority.context_digest
                if context_authority is not None
                else None
            ),
            context_sources_count=len(effective_blocks),
            retryable_error_code=None,
            egress_decision_id=preparation.decision_id,
            egress_packet_digest=preparation.packet_digest,
            egress_ticket_id=None,
            egress_reservation_id=preparation.reservation_id,
            egress_reason_code="adapter_unavailable",
            egress_trigger_ids=(),
        )

    queued = create_queued_ai_job(
        task_kind=task_kind,
        requested_route_class=requested_route_class,
        selected_route_class=selected_route_class,
        provider_id=attempt_binding.provider_id,
        model_id=attempt_binding.model_id,
        decision_reason=f"bound:{selected_route_class}",
        prompt_digest=ai_prompt_digest,
        context_digest=(
            context_authority.context_digest if context_authority is not None else None
        ),
        context_sources=(
            context_sources_manifest(effective_blocks) if effective_blocks else None
        ),
        route_metadata=route_metadata,
    )
    try:
        reserved = start_reserved_attempt(
            preparation.reservation_id or "",
            ai_job_id=queued.ai_job_id,
        )
        packet = _load_persisted_packet(reserved.packet_json)
        request = AIRequest(
            task_type=task_type_for(task_kind),
            prompt=task_prompt_for(task_kind, packet["context_blocks"], packet["prompt"]),
            model_preference=reserved.model_id,
            max_output_tokens=reserved.max_output_tokens,
            metadata={
                "egress_decision_id": reserved.decision_id,
                "egress_packet_digest": reserved.packet_digest,
                "selected_route_class": reserved.route_class,
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
        _release_before_network(
            reservation_id=preparation.reservation_id,
            ai_job_id=queued.ai_job_id,
        )
        decision = RoutingDecision(
            provider_id=attempt_binding.provider_id,
            model_id=attempt_binding.model_id,
            blocked=True,
            blocked_reason="egress_start_failed",
            decision_reason=f"egress_start_failed:{type(exc).__name__}",
        )
        return ExternalTaskOutcome(
            status="config_error",
            ledger_id=queued.ai_job_id,
            selected_route_class=selected_route_class,
            decision=decision,
            response=None,
            error_type=type(exc).__name__,
            context_digest=(
                context_authority.context_digest
                if context_authority is not None
                else None
            ),
            context_sources_count=len(effective_blocks),
            retryable_error_code=None,
            egress_decision_id=preparation.decision_id,
            egress_packet_digest=preparation.packet_digest,
            egress_ticket_id=None,
            egress_reservation_id=preparation.reservation_id,
            egress_reason_code="egress_start_failed",
            egress_trigger_ids=(),
        )

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
            preparation.reservation_id or "",
            ai_job_id=queued.ai_job_id,
            network_attempt=True,
            usage_source="estimated",
            registry=registry,
        )
        decision = RoutingDecision(
            provider_id=attempt_binding.provider_id,
            model_id=attempt_binding.model_id,
            decision_reason=f"bound:{selected_route_class}",
        )
        return ExternalTaskOutcome(
            status="provider_error",
            ledger_id=queued.ai_job_id,
            selected_route_class=selected_route_class,
            decision=decision,
            response=None,
            error_type=type(exc).__name__,
            context_digest=(
                context_authority.context_digest
                if context_authority is not None
                else None
            ),
            context_sources_count=len(effective_blocks),
            retryable_error_code=None,
            egress_decision_id=preparation.decision_id,
            egress_packet_digest=preparation.packet_digest,
            egress_ticket_id=None,
            egress_reservation_id=preparation.reservation_id,
            egress_reason_code=preparation.reason_code,
            egress_trigger_ids=(),
        )

    status, error_type = _response_status(response)
    try:
        finalize_queued_ai_job(
            queued.ai_job_id,
            status=status,
            response=response,
            latency_ms=_elapsed_ms(started_at),
            error_type=error_type,
        )
    except Exception as exc:
        finalize_queued_ai_job(
            queued.ai_job_id,
            status="provider_error",
            response=None,
            latency_ms=_elapsed_ms(started_at),
            error_type=type(exc).__name__,
        )
        reconcile_reserved_attempt(
            preparation.reservation_id or "",
            ai_job_id=queued.ai_job_id,
            network_attempt=True,
            usage_source="estimated",
            registry=registry,
        )
        decision = RoutingDecision(
            provider_id=attempt_binding.provider_id,
            model_id=attempt_binding.model_id,
            decision_reason=f"bound:{selected_route_class}",
        )
        return ExternalTaskOutcome(
            status="provider_error",
            ledger_id=queued.ai_job_id,
            selected_route_class=selected_route_class,
            decision=decision,
            response=None,
            error_type=type(exc).__name__,
            context_digest=(
                context_authority.context_digest
                if context_authority is not None
                else None
            ),
            context_sources_count=len(effective_blocks),
            retryable_error_code=None,
            egress_decision_id=preparation.decision_id,
            egress_packet_digest=preparation.packet_digest,
            egress_ticket_id=None,
            egress_reservation_id=preparation.reservation_id,
            egress_reason_code="response_binding_mismatch",
            egress_trigger_ids=(),
        )

    reconcile_reserved_attempt(
        preparation.reservation_id or "",
        ai_job_id=queued.ai_job_id,
        network_attempt=True,
        actual_input_tokens=response.usage.input_tokens,
        actual_output_tokens=response.usage.output_tokens,
        usage_source="actual",
        registry=registry,
    )
    retryable_error_code = (
        response.error.code.value
        if response.error is not None and response.error.retryable
        else None
    )
    decision = RoutingDecision(
        provider_id=attempt_binding.provider_id,
        model_id=attempt_binding.model_id,
        decision_reason=f"bound:{selected_route_class}",
    )
    return ExternalTaskOutcome(
        status=status,
        ledger_id=queued.ai_job_id,
        selected_route_class=selected_route_class,
        decision=decision,
        response=response,
        error_type=error_type,
        context_digest=(
            context_authority.context_digest if context_authority is not None else None
        ),
        context_sources_count=len(effective_blocks),
        retryable_error_code=retryable_error_code,
        egress_decision_id=preparation.decision_id,
        egress_packet_digest=preparation.packet_digest,
        egress_ticket_id=None,
        egress_reservation_id=preparation.reservation_id,
        egress_reason_code=preparation.reason_code,
        egress_trigger_ids=(),
    )


def _prepacket_outcome(
    *,
    result: str,
    reason_code: str,
    prompt_digest: str,
    ai_prompt_digest: str,
    context_digest: str | None,
    prompt_level: str,
    context_level: str,
    route_class: str,
    requested_route_class: str | None,
    task_kind: str,
    binding: ProviderBinding,
    fallback_index: int,
    workspace_id: str | None,
    source_count: int,
    included_count: int,
    withheld_count: int,
    route_metadata: dict[str, object],
    started_at: float,
) -> ExternalTaskOutcome:
    final_level = _prepacket_final_level(prompt_level, context_level)
    recorded = record_prepacket_egress_decision(
        result=result,
        reason_code=reason_code,
        route_class=route_class,
        provider_id=binding.provider_id,
        model_id=binding.model_id,
        fallback_index=fallback_index,
        prompt_digest=prompt_digest,
        context_digest=context_digest,
        prompt_level=prompt_level,
        context_level=context_level,
        final_level=final_level,
        source_count=source_count,
        included_count=included_count,
        withheld_count=withheld_count,
        workspace_id=workspace_id,
    )
    route_metadata = {
        **route_metadata,
        "egress_decision_id": recorded.decision_id,
        "egress_reason_code": recorded.reason_code,
        "egress_safe_input_digest": recorded.safe_input_digest,
    }
    terminal_status = "validation_error" if result == "pause" else "config_error"
    ledger_id = _terminal_ai_job(
        task_kind=task_kind,
        requested_route_class=requested_route_class,
        selected_route_class=route_class,
        binding=binding,
        prompt_digest=ai_prompt_digest,
        context_digest=context_digest,
        context_sources=None,
        route_metadata=route_metadata,
        status=terminal_status,
        error_type=reason_code,
        started_at=started_at,
    )
    decision = RoutingDecision(
        provider_id=binding.provider_id,
        model_id=binding.model_id,
        blocked=True,
        blocked_reason=reason_code,
        decision_reason=f"egress:{reason_code}",
    )
    return ExternalTaskOutcome(
        status=terminal_status,
        ledger_id=ledger_id,
        selected_route_class=route_class,
        decision=decision,
        response=None,
        error_type=reason_code,
        context_digest=context_digest,
        context_sources_count=source_count,
        retryable_error_code=None,
        egress_decision_id=recorded.decision_id,
        egress_packet_digest=None,
        egress_ticket_id=None,
        egress_reservation_id=None,
        egress_reason_code=reason_code,
        egress_trigger_ids=(),
    )


def _terminal_ai_job(
    *,
    task_kind: str,
    requested_route_class: str | None,
    selected_route_class: str,
    binding: ProviderBinding,
    prompt_digest: str,
    context_digest: str | None,
    context_sources: list[dict[str, object]] | None,
    route_metadata: dict[str, object],
    status: str,
    error_type: str,
    started_at: float,
) -> str:
    queued = create_queued_ai_job(
        task_kind=task_kind,
        requested_route_class=requested_route_class,
        selected_route_class=selected_route_class,
        provider_id=binding.provider_id,
        model_id=binding.model_id,
        decision_reason=f"bound:{selected_route_class}",
        prompt_digest=prompt_digest,
        context_digest=context_digest,
        context_sources=context_sources,
        route_metadata=route_metadata,
    )
    finalize_queued_ai_job(
        queued.ai_job_id,
        status=status,
        response=None,
        latency_ms=_elapsed_ms(started_at),
        error_type=error_type,
    )
    return queued.ai_job_id


def _release_before_network(*, reservation_id: str | None, ai_job_id: str) -> None:
    if reservation_id is None:
        return
    try:
        reconcile_reserved_attempt(
            reservation_id,
            ai_job_id=ai_job_id,
            network_attempt=False,
        )
    except Exception:
        return


def _load_persisted_packet(packet_json: str) -> dict[str, object]:
    try:
        packet = json.loads(packet_json)
    except json.JSONDecodeError as exc:
        raise ValueError("persisted egress packet is malformed") from exc
    if not isinstance(packet, dict) or set(packet) != {"prompt", "context_blocks"}:
        raise ValueError("persisted egress packet has an unexpected shape")
    if not isinstance(packet["prompt"], str) or not packet["prompt"].strip():
        raise ValueError("persisted egress prompt is invalid")
    if not isinstance(packet["context_blocks"], list):
        raise ValueError("persisted egress context is invalid")
    blocks = canonicalize_blocks(packet["context_blocks"])
    return {"prompt": packet["prompt"], "context_blocks": blocks}


def _binding_chain(
    *,
    route_class: str,
    primary: ProviderBinding,
    bindings: dict[str, ProviderBinding] | None,
    registry: ProviderRegistry,
) -> list[ProviderBinding]:
    if bindings is not None:
        return [primary]
    configured = registry.fallback_chains.get(route_class)
    if not configured:
        return [primary]
    chain: list[ProviderBinding] = []
    for item in configured:
        provider = registry.providers[item.provider_id]
        model = registry.models[(item.provider_id, item.model_id)]
        chain.append(
            ProviderBinding(
                route_class=route_class,
                provider_id=item.provider_id,
                model_id=item.model_id,
                requires_network=provider.requires_network,
                max_output_tokens=model.max_output_tokens,
            )
        )
    return chain


def _route_metadata(
    *,
    selected_route_class: str,
    fallback_index: int,
    binding: ProviderBinding,
    prior_retryable_error_code: str | None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "fallback_attempt_index": fallback_index,
        "fallback_chain_route": selected_route_class,
        "fallback_model_id": binding.model_id,
        "fallback_provider_id": binding.provider_id,
    }
    if prior_retryable_error_code is not None:
        result["prior_retryable_error_code"] = prior_retryable_error_code
    return result


def _response_status(response: AIResponse) -> tuple[str, str | None]:
    if response.error is None and response.text is not None:
        return "success", None
    return (
        "provider_error",
        response.error.code.value if response.error is not None else "empty_response",
    )


def _prompt_floor_or_unknown(prompt: str) -> str:
    return sensitivity.deterministic_floor(prompt) or "unknown"


def _prepacket_final_level(prompt_level: str, context_level: str) -> str:
    if "S4" in {prompt_level, context_level}:
        return "S4"
    if "unknown" in {prompt_level, context_level}:
        return "unknown"
    return max((prompt_level, context_level), key=_LEVEL_RANK.__getitem__)


def _default_task_prompt(task_kind: str, blocks: list[dict], prompt: str) -> str:
    del task_kind
    return assemble_prompt(blocks, prompt)


def _elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


def load_default_provider_registry_context_budget() -> int:
    from app.modules.ai.egress_policy import load_default_egress_policy

    return load_default_egress_policy().max_context_chars
