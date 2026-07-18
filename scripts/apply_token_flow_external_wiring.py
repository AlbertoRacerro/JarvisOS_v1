from __future__ import annotations

import re
from pathlib import Path

RUNTIME = Path("backend/app/modules/ai/egress_runtime.py")
EXECUTION = Path("backend/app/modules/ai/execution.py")
TEST = Path("backend/tests/test_ai_egress_runtime.py")


def replace_exact(source: str, old: str, new: str, *, expected: int = 1) -> str:
    count = source.count(old)
    if count != expected:
        raise RuntimeError(f"expected {expected} matches, found {count}: {old[:80]!r}")
    return source.replace(old, new)


def replace_regex(source: str, pattern: str, replacement: str, *, expected: int = 1) -> str:
    result, count = re.subn(pattern, replacement, source, flags=re.DOTALL)
    if count != expected:
        raise RuntimeError(f"expected {expected} regex matches, found {count}: {pattern[:80]!r}")
    return result


def patch_runtime() -> None:
    source = RUNTIME.read_text(encoding="utf-8")
    source = replace_exact(
        source,
        """from app.modules.ai.contracts import (
    AIProviderAdapter,
    AIRequest,
    AIResponse,
    AITaskType,
    RoutingDecision,
)
""",
        """from app.modules.ai.contracts import (
    AIExternalDispatchState,
    AIProviderAdapter,
    AIRequest,
    AIResponse,
    AITaskType,
    RoutingDecision,
)
""",
    )
    source = replace_exact(
        source,
        """from app.modules.ai.egress_spine import (
    EgressSpineStateError,
    create_queued_ai_job,
    finalize_queued_ai_job,
    record_prepacket_egress_decision,
)
""",
        """from app.modules.ai.egress_spine import (
    EgressSpineStateError,
    create_queued_ai_job,
    record_prepacket_egress_decision,
)
""",
    )
    source = replace_exact(
        source,
        """from app.modules.ai.settings import get_ai_settings
""",
        """from app.modules.ai.settings import ensure_ai_settings, get_ai_settings
from app.modules.ai.token_flow_external_transaction import finalize_external_attempt
from app.modules.ai.token_flow_runtime import normalize_outcome_reason
from app.modules.ai.token_flow_service import create_flow, transition_flow_state
""",
    )
    source = replace_exact(
        source,
        """    egress_reason_code: str | None
    egress_trigger_ids: tuple[str, ...]
""",
        """    egress_reason_code: str | None
    egress_trigger_ids: tuple[str, ...]
    flow_id: str
""",
    )

    helper = '''

def _flow_workspace_id(workspace_id: str | None) -> str | None:
    if workspace_id is None:
        return None
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM workspaces WHERE id = ?",
            (workspace_id,),
        ).fetchone()
    return workspace_id if row is not None else None


def _create_external_flow(
    *,
    task_kind: str,
    requested_route_class: str | None,
    workspace_id: str | None,
) -> str:
    ensure_ai_settings()
    flow = create_flow(
        task_kind=task_kind,
        requested_route_class=requested_route_class,
        workspace_id=_flow_workspace_id(workspace_id),
    )
    return str(flow["id"])


def _terminalize_external_flow(flow_id: str, outcome: ExternalTaskOutcome) -> None:
    if (
        outcome.status == "validation_error"
        and outcome.egress_reason_code == "confirmation_required"
        and outcome.egress_ticket_id is not None
    ):
        transition_flow_state(flow_id=flow_id, new_state="confirmation_required")
        return
    if outcome.status == "success":
        state = "complete"
        reason = "completed"
    else:
        state = "failed_terminal"
        reason = normalize_outcome_reason(
            outcome.egress_reason_code or outcome.error_type or outcome.status
        )
    transition_flow_state(
        flow_id=flow_id,
        new_state=state,
        terminal_reason=reason,
        terminal_attempt_id=outcome.ledger_id,
    )
'''
    source = replace_exact(source, "\n\ndef run_external_task(\n", helper + "\n\ndef run_external_task(\n")

    old_run = '''def run_external_task(
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
    policy: EgressPolicyConfig | None = None,
) -> ExternalTaskOutcome:
    """Execute an external route through the mandatory per-binding 059b boundary."""

    from app.modules.ai.execution import resolve_binding

    policy = policy or load_default_egress_policy()
    registry = registry or load_default_provider_registry()
    binding_table = bindings if bindings is not None else registry.bindings
    primary, _decision = resolve_binding(selected_route_class, binding_table)
    if primary is None:
        raise EgressContractError("external runtime requires a resolved route")
    chain = _binding_chain(
        route_class=selected_route_class,
        primary=primary,
        bindings=bindings,
        registry=registry,
    )
    prompt_builder = task_prompt_for or _default_task_prompt
    prior_retryable_error_code: str | None = None
    last_outcome: ExternalTaskOutcome | None = None

    for fallback_index, binding in enumerate(chain):
        outcome = _run_binding(
            user_prompt=user_prompt,
            task_kind=task_kind,
            selected_route_class=selected_route_class,
            requested_route_class=requested_route_class,
            context_blocks=context_blocks,
            max_output_tokens=max_output_tokens,
            adapters=adapters,
            workspace_id=workspace_id,
            context_build_error=context_build_error,
            external_blocked_reason=(
                external_blocked_reason if fallback_index == 0 else None
            ),
            task_type_for=task_type_for,
            task_prompt_for=prompt_builder,
            binding=binding,
            fallback_index=fallback_index,
            prior_retryable_error_code=prior_retryable_error_code,
            registry=registry,
            policy=policy,
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
        raise EgressSpineStateError("external binding chain was empty")
    return last_outcome
'''
    new_run = '''def run_external_task(
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
    policy: EgressPolicyConfig | None = None,
) -> ExternalTaskOutcome:
    """Execute an external route through the mandatory per-binding 059b boundary."""

    from app.modules.ai.execution import resolve_binding

    policy = policy or load_default_egress_policy()
    registry = registry or load_default_provider_registry()
    binding_table = bindings if bindings is not None else registry.bindings
    primary, _decision = resolve_binding(selected_route_class, binding_table)
    if primary is None:
        raise EgressContractError("external runtime requires a resolved route")
    flow_id = _create_external_flow(
        task_kind=task_kind,
        requested_route_class=requested_route_class,
        workspace_id=workspace_id,
    )
    chain = _binding_chain(
        route_class=selected_route_class,
        primary=primary,
        bindings=bindings,
        registry=registry,
    )
    prompt_builder = task_prompt_for or _default_task_prompt
    prior_retryable_error_code: str | None = None
    last_outcome: ExternalTaskOutcome | None = None

    for fallback_index, binding in enumerate(chain):
        outcome = _run_binding(
            user_prompt=user_prompt,
            task_kind=task_kind,
            selected_route_class=selected_route_class,
            requested_route_class=requested_route_class,
            context_blocks=context_blocks,
            max_output_tokens=max_output_tokens,
            adapters=adapters,
            workspace_id=workspace_id,
            context_build_error=context_build_error,
            external_blocked_reason=(
                external_blocked_reason if fallback_index == 0 else None
            ),
            task_type_for=task_type_for,
            task_prompt_for=prompt_builder,
            binding=binding,
            fallback_index=fallback_index,
            prior_retryable_error_code=prior_retryable_error_code,
            registry=registry,
            policy=policy,
            flow_id=flow_id,
        )
        last_outcome = outcome
        if (
            outcome.status == "provider_error"
            and outcome.retryable_error_code is not None
            and fallback_index + 1 < len(chain)
        ):
            prior_retryable_error_code = outcome.retryable_error_code
            continue
        _terminalize_external_flow(flow_id, outcome)
        return outcome

    if last_outcome is None:
        raise EgressSpineStateError("external binding chain was empty")
    _terminalize_external_flow(flow_id, last_outcome)
    return last_outcome
'''
    source = replace_exact(source, old_run, new_run)

    source = replace_exact(
        source,
        """    registry: ProviderRegistry,
    policy: EgressPolicyConfig,
) -> ExternalTaskOutcome:
""",
        """    registry: ProviderRegistry,
    policy: EgressPolicyConfig,
    flow_id: str,
) -> ExternalTaskOutcome:
""",
        expected=1,
    )

    def add_prepacket_args(match: re.Match[str]) -> str:
        body = match.group(1)
        if "flow_id=" in body:
            raise RuntimeError("prepacket call already wired")
        return (
            "return _persist_prepacket(" + body
            + "\n            requested_output_ceiling=max_output_tokens,"
            + "\n            registry=registry,"
            + "\n            flow_id=flow_id,"
            + "\n        )"
        )

    source, count = re.subn(
        r"return _persist_prepacket\((.*?)\n        \)",
        add_prepacket_args,
        source,
        flags=re.DOTALL,
    )
    if count != 3:
        raise RuntimeError(f"expected 3 prepacket calls, found {count}")

    source = replace_exact(
        source,
        """    policy: EgressPolicyConfig,
) -> ExternalTaskOutcome:
    final_level = _prepacket_final_level(stop.prompt_level, stop.context_level)
""",
        """    policy: EgressPolicyConfig,
    requested_output_ceiling: int | None,
    registry: ProviderRegistry,
    flow_id: str,
) -> ExternalTaskOutcome:
    final_level = _prepacket_final_level(stop.prompt_level, stop.context_level)
""",
        expected=1,
    )

    source = replace_exact(
        source,
        """    ledger_id = _terminal_job(
        task_kind=task_kind,
""",
        """    ledger_id = _terminal_job(
        flow_id=flow_id,
        task_kind=task_kind,
""",
        expected=2,
    )
    source = replace_exact(
        source,
        """        blocked_reason=detail_reason,
    )
    return _outcome(
""",
        """        blocked_reason=detail_reason,
        fallback_index=fallback_index,
        requested_output_ceiling=requested_output_ceiling,
        effective_output_ceiling=None,
        registry=registry,
    )
    return _outcome(
""",
        expected=1,
    )
    source = replace_exact(
        source,
        """            blocked_reason=preparation.reason_code,
        )
        return _outcome(
""",
        """            blocked_reason=preparation.reason_code,
            fallback_index=fallback_index,
            requested_output_ceiling=max_output_tokens,
            effective_output_ceiling=attempt_max,
            registry=registry,
        )
        return _outcome(
""",
        expected=1,
    )

    new_allowed = '''    reservation_id = preparation.reservation_id
    if reservation_id is None:
        raise EgressSpineStateError("silent allow did not create a reservation")
    queued = create_queued_ai_job(
        task_kind=task_kind,
        requested_route_class=requested_route_class,
        selected_route_class=selected_route_class,
        provider_id=binding.provider_id,
        model_id=binding.model_id,
        decision_reason=f"bound:{selected_route_class}",
        prompt_digest=ai_prompt_digest,
        context_digest=context.digest,
        context_sources=(
            context_sources_manifest(list(context.blocks)) if context.blocks else None
        ),
        route_metadata=route_metadata,
    )

    try:
        reserved = start_reserved_attempt(
            reservation_id,
            ai_job_id=queued.ai_job_id,
        )
        packet = _load_packet(reserved.packet_json)
        request = AIRequest(
            task_type=task_type_for(task_kind),
            prompt=task_prompt_for(
                task_kind,
                packet["context_blocks"],
                packet["prompt"],
            ),
            model_preference=reserved.model_id,
            max_output_tokens=reserved.max_output_tokens,
            metadata={
                "egress_decision_id": reserved.decision_id,
                "egress_packet_digest": reserved.packet_digest,
                "selected_route_class": reserved.route_class,
            },
        )
    except Exception as exc:
        finalize_external_attempt(
            flow_id=flow_id,
            ai_job_id=queued.ai_job_id,
            binding=binding,
            fallback_index=fallback_index,
            status="config_error",
            response=None,
            latency_ms=_elapsed_ms(started_at),
            error_type=type(exc).__name__,
            adapter_invoked=False,
            dispatch_state=AIExternalDispatchState.not_started,
            requested_output_ceiling=max_output_tokens,
            effective_output_ceiling=attempt_max,
            outcome_reason="egress_start_failed",
            reservation_id=reservation_id,
            registry=registry,
        )
        return _outcome(
            status="config_error",
            ledger_id=queued.ai_job_id,
            flow_id=flow_id,
            route_class=selected_route_class,
            binding=binding,
            response=None,
            error_type=type(exc).__name__,
            context=context,
            egress_decision_id=preparation.decision_id,
            packet_digest=preparation.packet_digest,
            ticket_id=None,
            reservation_id=reservation_id,
            reason_code="egress_start_failed",
            trigger_ids=(),
            blocked=True,
        )

    try:
        response = adapter.complete(request)
    except Exception as exc:
        finalize_external_attempt(
            flow_id=flow_id,
            ai_job_id=queued.ai_job_id,
            binding=binding,
            fallback_index=fallback_index,
            status="provider_error",
            response=None,
            latency_ms=_elapsed_ms(started_at),
            error_type=type(exc).__name__,
            adapter_invoked=True,
            dispatch_state=AIExternalDispatchState.unknown,
            requested_output_ceiling=max_output_tokens,
            effective_output_ceiling=reserved.max_output_tokens,
            outcome_reason=type(exc).__name__,
            reservation_id=reservation_id,
            registry=registry,
        )
        return _outcome(
            status="provider_error",
            ledger_id=queued.ai_job_id,
            flow_id=flow_id,
            route_class=selected_route_class,
            binding=binding,
            response=None,
            error_type=type(exc).__name__,
            context=context,
            egress_decision_id=preparation.decision_id,
            packet_digest=preparation.packet_digest,
            ticket_id=None,
            reservation_id=reservation_id,
            reason_code=preparation.reason_code,
            trigger_ids=(),
            blocked=False,
        )

    status, error_type = _response_status(response)
    binding_mismatch = (
        (response.provider_id, response.model_id)
        != (binding.provider_id, binding.model_id)
        or (response.usage.provider_id, response.usage.model_id)
        != (binding.provider_id, binding.model_id)
    )
    dispatch_invalid = response.external_dispatch_state not in {
        AIExternalDispatchState.not_started,
        AIExternalDispatchState.started,
        AIExternalDispatchState.unknown,
    } or (
        status == "success"
        and response.external_dispatch_state is AIExternalDispatchState.not_started
    )
    if binding_mismatch or dispatch_invalid:
        reason_code = (
            "response_binding_mismatch" if binding_mismatch else "response_dispatch_invalid"
        )
        error_name = "EgressSpineStateError" if binding_mismatch else "EgressContractError"
        finalize_external_attempt(
            flow_id=flow_id,
            ai_job_id=queued.ai_job_id,
            binding=binding,
            fallback_index=fallback_index,
            status="provider_error",
            response=None,
            latency_ms=_elapsed_ms(started_at),
            error_type=error_name,
            adapter_invoked=True,
            dispatch_state=AIExternalDispatchState.unknown,
            requested_output_ceiling=max_output_tokens,
            effective_output_ceiling=reserved.max_output_tokens,
            outcome_reason=reason_code,
            reservation_id=reservation_id,
            registry=registry,
        )
        return _outcome(
            status="provider_error",
            ledger_id=queued.ai_job_id,
            flow_id=flow_id,
            route_class=selected_route_class,
            binding=binding,
            response=None,
            error_type=error_name,
            context=context,
            egress_decision_id=preparation.decision_id,
            packet_digest=preparation.packet_digest,
            ticket_id=None,
            reservation_id=reservation_id,
            reason_code=reason_code,
            trigger_ids=(),
            blocked=False,
        )

    finalize_external_attempt(
        flow_id=flow_id,
        ai_job_id=queued.ai_job_id,
        binding=binding,
        fallback_index=fallback_index,
        status=status,
        response=response,
        latency_ms=_elapsed_ms(started_at),
        error_type=error_type,
        adapter_invoked=True,
        dispatch_state=response.external_dispatch_state,
        requested_output_ceiling=max_output_tokens,
        effective_output_ceiling=reserved.max_output_tokens,
        outcome_reason=error_type or status,
        reservation_id=reservation_id,
        registry=registry,
    )
    retryable = (
        response.error.code.value
        if response.error is not None and response.error.retryable
        else None
    )
    return _outcome(
        status=status,
        ledger_id=queued.ai_job_id,
        flow_id=flow_id,
        route_class=selected_route_class,
        binding=binding,
        response=response,
        error_type=error_type,
        context=context,
        egress_decision_id=preparation.decision_id,
        packet_digest=preparation.packet_digest,
        ticket_id=None,
        reservation_id=reservation_id,
        reason_code=preparation.reason_code,
        trigger_ids=(),
        blocked=False,
        retryable_error_code=retryable,
    )'''
    source = replace_regex(
        source,
        r"    reservation_id = preparation\.reservation_id.*?\n\n\ndef _authorize_context",
        new_allowed + "\n\n\ndef _authorize_context",
    )

    terminal = '''def _terminal_job(
    *,
    flow_id: str,
    task_kind: str,
    requested_route_class: str | None,
    route_class: str,
    binding: ProviderBinding,
    prompt_digest: str,
    context: _ContextView,
    route_metadata: dict[str, object],
    status: str,
    error_type: str,
    started_at: float,
    decision_reason: str,
    blocked_reason: str | None,
    fallback_index: int,
    requested_output_ceiling: int | None,
    effective_output_ceiling: int | None,
    registry: ProviderRegistry,
) -> str:
    queued = create_queued_ai_job(
        task_kind=task_kind,
        requested_route_class=requested_route_class,
        selected_route_class=route_class,
        provider_id=binding.provider_id,
        model_id=binding.model_id,
        decision_reason=decision_reason,
        blocked_reason=blocked_reason,
        prompt_digest=prompt_digest,
        context_digest=context.digest,
        context_sources=(
            context_sources_manifest(list(context.blocks)) if context.blocks else None
        ),
        route_metadata=route_metadata,
    )
    finalize_external_attempt(
        flow_id=flow_id,
        ai_job_id=queued.ai_job_id,
        binding=binding,
        fallback_index=fallback_index,
        status=status,
        response=None,
        latency_ms=_elapsed_ms(started_at),
        error_type=error_type,
        adapter_invoked=False,
        dispatch_state=AIExternalDispatchState.not_started,
        requested_output_ceiling=requested_output_ceiling,
        effective_output_ceiling=effective_output_ceiling,
        outcome_reason=blocked_reason or error_type,
        registry=registry,
    )
    return queued.ai_job_id
'''
    source = replace_regex(
        source,
        r"def _terminal_job\(.*?\n\n\ndef _outcome\(",
        terminal + "\n\n\ndef _outcome(",
    )

    source = replace_exact(
        source,
        """    status: str,
    ledger_id: str,
    route_class: str,
""",
        """    status: str,
    ledger_id: str,
    flow_id: str,
    route_class: str,
""",
        expected=1,
    )
    source, count = re.subn(
        r"(\n\s+ledger_id=[^\n]+,)(\n\s+route_class=)",
        r"\1\n            flow_id=flow_id,\2",
        source,
    )
    if count != 2:
        raise RuntimeError(f"expected 2 remaining outcome calls, found {count}")
    source = replace_exact(
        source,
        """        status=status,
        ledger_id=ledger_id,
        selected_route_class=route_class,
""",
        """        status=status,
        ledger_id=ledger_id,
        selected_route_class=route_class,
""",
        expected=1,
    )
    source = replace_exact(
        source,
        """        egress_reason_code=reason_code,
        egress_trigger_ids=trigger_ids,
    )
""",
        """        egress_reason_code=reason_code,
        egress_trigger_ids=trigger_ids,
        flow_id=flow_id,
    )
""",
        expected=1,
    )

    RUNTIME.write_text(source, encoding="utf-8")


def patch_execution() -> None:
    source = EXECUTION.read_text(encoding="utf-8")
    source = replace_exact(
        source,
        """        egress_reason_code=external.egress_reason_code,
        egress_trigger_ids=external.egress_trigger_ids,
    )
""",
        """        egress_reason_code=external.egress_reason_code,
        egress_trigger_ids=external.egress_trigger_ids,
        flow_id=external.flow_id,
    )
""",
    )
    EXECUTION.write_text(source, encoding="utf-8")


def patch_tests() -> None:
    source = TEST.read_text(encoding="utf-8")
    source = replace_exact(
        source,
        """from app.modules.ai.contracts import (
    AIRequest,
""",
        """from app.modules.ai.contracts import (
    AIExternalDispatchState,
    AIRequest,
""",
    )
    source = replace_exact(
        source,
        """            finish_reason="stop",
            safety_status="allowed",
        )
""",
        """            finish_reason="stop",
            safety_status="allowed",
            external_dispatch_state=AIExternalDispatchState.started,
        )
""",
        expected=1,
    )
    source = replace_exact(
        source,
        """        finish_reason="stop",
        safety_status="allowed",
    )
""",
        """        finish_reason="stop",
        safety_status="allowed",
        external_dispatch_state=AIExternalDispatchState.started,
    )
""",
        expected=1,
    )
    source = replace_exact(
        source,
        """    assert outcome.egress_packet_digest is not None
    assert adapter.calls == 0
""",
        """    assert outcome.egress_packet_digest is not None
    assert outcome.flow_id is not None
    assert adapter.calls == 0
""",
    )
    source = replace_exact(
        source,
        """        job = connection.execute("SELECT status FROM ai_jobs").fetchone()
""",
        """        job = connection.execute(
            "SELECT status, flow_id, execution_class, adapter_invoked, "
            "external_dispatch_state, accounting_basis FROM ai_jobs"
        ).fetchone()
        flow = connection.execute(
            "SELECT state, terminal_attempt_id FROM ai_flows WHERE id = ?",
            (outcome.flow_id,),
        ).fetchone()
""",
    )
    source = replace_exact(
        source,
        """    assert job["status"] == "validation_error"
""",
        """    assert job["status"] == "validation_error"
    assert job["flow_id"] == outcome.flow_id
    assert job["execution_class"] == "external_provider"
    assert job["adapter_invoked"] == 0
    assert job["external_dispatch_state"] == "not_started"
    assert job["accounting_basis"] == "external_not_sent"
    assert flow["state"] == "confirmation_required"
    assert flow["terminal_attempt_id"] is None
""",
        expected=1,
    )
    source = replace_exact(
        source,
        """    assert outcome.egress_reservation_id is not None
    assert adapter.calls == 1
""",
        """    assert outcome.egress_reservation_id is not None
    assert outcome.flow_id is not None
    assert adapter.calls == 1
""",
    )
    source = replace_exact(
        source,
        """        job = connection.execute(
            "SELECT status, output_digest FROM ai_jobs WHERE id = ?",
""",
        """        job = connection.execute(
            "SELECT status, output_digest, flow_id, execution_class, adapter_invoked, "
            "external_dispatch_state, normalized_usage_source, accounting_basis, "
            "accounted_provider_spend_usd_decimal FROM ai_jobs WHERE id = ?",
""",
    )
    source = replace_exact(
        source,
        """        packet = connection.execute(
            "SELECT packet_json FROM egress_packets WHERE packet_digest = ?",
            (outcome.egress_packet_digest,),
        ).fetchone()
""",
        """        packet = connection.execute(
            "SELECT packet_json FROM egress_packets WHERE packet_digest = ?",
            (outcome.egress_packet_digest,),
        ).fetchone()
        flow = connection.execute(
            "SELECT state, terminal_attempt_id FROM ai_flows WHERE id = ?",
            (outcome.flow_id,),
        ).fetchone()
""",
    )
    source = replace_exact(
        source,
        """    assert job["output_digest"] == canonical_digest({"text": "Bound generic answer."})
""",
        """    assert job["output_digest"] == canonical_digest({"text": "Bound generic answer."})
    assert job["flow_id"] == outcome.flow_id
    assert job["execution_class"] == "external_provider"
    assert job["adapter_invoked"] == 1
    assert job["external_dispatch_state"] == "started"
    assert job["normalized_usage_source"] == "actual"
    assert job["accounting_basis"] == "provider_exact"
    assert float(job["accounted_provider_spend_usd_decimal"]) > 0
    assert flow["state"] == "complete"
    assert flow["terminal_attempt_id"] == outcome.ledger_id
""",
    )
    source = replace_exact(
        source,
        """        job = connection.execute(
            "SELECT status, output_digest, error_type FROM ai_jobs WHERE id = ?",
""",
        """        job = connection.execute(
            "SELECT status, output_digest, error_type, flow_id, external_dispatch_state, "
            "normalized_usage_source, accounting_basis, "
            "accounted_provider_spend_usd_decimal FROM ai_jobs WHERE id = ?",
""",
    )
    source = replace_exact(
        source,
        """    assert job["error_type"] == "EgressSpineStateError"
""",
        """    assert job["error_type"] == "EgressSpineStateError"
    assert job["flow_id"] == outcome.flow_id
    assert job["external_dispatch_state"] == "unknown"
    assert job["normalized_usage_source"] == "estimated"
    assert job["accounting_basis"] == "conservative_estimated_usage"
    assert float(job["accounted_provider_spend_usd_decimal"]) > 0
""",
    )
    TEST.write_text(source, encoding="utf-8")


def main() -> None:
    patch_runtime()
    patch_execution()
    patch_tests()


if __name__ == "__main__":
    main()
