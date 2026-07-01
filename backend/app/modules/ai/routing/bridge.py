from __future__ import annotations

import json
import time
from collections.abc import Callable
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.modules.ai.context_builder import canonical_digest, context_sources_manifest
from app.modules.ai.execution import AiTaskOutcome
from app.modules.ai.models import AITaskRunRequest, AITaskRunResponse
from app.modules.ai.routing.decision import decide_router_policy
from app.modules.ai.routing.safe_local import is_safe_local_execution
from app.modules.events.service import utc_now

AUTO_ROUTE_CLASS = "auto"
AUTO_LOCAL_DEFAULT_ROUTE_CLASS = "local:fast"
AUTO_LOCAL_ROUTE_BY_TASK_KIND = {
    "general": "local:fast",
    "test": "local:fast",
    "synthesis": "local:general",
    "decision_support": "local:general",
    "code_review": "local:coder",
    "architecture_review": "local:coder_heavy",
}

RunAiTaskFunc = Callable[..., AiTaskOutcome]


def build_auto_router_input(request: AITaskRunRequest) -> dict:
    return {
        "message_text": request.prompt,
        "phase_a_signals": {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "external_provider_allowed": False,
            "clarification_required": False,
            "hard_reason_codes": ["low_risk"],
            "sensitivity_bucket_proposal": "internal" if request.include_project_context else "unknown",
            "requires_manual_review": False,
            "source_policy_for_future_retrieval": "not_applicable",
            "allowed_future_retrieval_behavior": "none",
        },
        "phase_b_soft_proposal": {
            "project_bucket": "general",
            "primary_domain": "general",
            "domain_tags": ["answer"],
            "soft_reason_code": "contextual_summary",
            "suggested_followup_question": "",
        },
        "router_hint": {
            "task_type": "answer",
            "complexity": "low",
            "domain": "general",
            "confidence": "high",
            "estimated_tokens": 200,
            "needs_reasoning": False,
            "needs_current_info": False,
            "needs_file_context": False,
            "needs_code_execution": False,
            "needs_scientific_depth": False,
        },
        "action_hint": {
            "requested_action_type": "answer",
            "modifies_state": False,
            "side_effect_level": "none",
            "reversibility": "reversible",
            "environment_type": "chat",
            "state_scope": "none",
            "needs_terminal": False,
            "needs_file_write": False,
            "needs_memory_write": False,
            "needs_provider_call": False,
            "confidence": "high",
        },
        "user_policy": {
            "external_routing_enabled": False,
            "external_requires_confirmation": True,
            "allow_persistent_auto_allow": False,
        },
        "provider_policy": {
            "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST"],
            "blocked_provider_tiers": ["CHEAP_EXTERNAL", "SCIENTIFIC_MEDIUM", "FRONTIER"],
        },
        "budget_policy": {
            "max_tier": "LOCAL_FAST",
            "max_tokens": request.max_tokens or 2048,
            "require_confirmation_above_tier": "CHEAP_EXTERNAL",
        },
        "context_metadata": {
            "attached_files_present": bool(request.context_blocks),
            "conversation_context_available": True,
        },
    }


def build_auto_decision(request: AITaskRunRequest, *, now: str | None = None) -> tuple[dict, dict]:
    router_input = build_auto_router_input(request)
    return router_input, decide_router_policy(router_input, now=now)


def resolve_bridge_outcome_from_decision(
    *,
    request: AITaskRunRequest,
    decision: dict,
    run_ai_task_func: RunAiTaskFunc | None = None,
    context_blocks: list[dict] | None = None,
    context_build_error: str | None = None,
    requested_workspace_id: str | None = None,
) -> AITaskRunResponse:
    from app.modules.ai import execution

    runner = run_ai_task_func or execution.run_ai_task
    if _is_executable_auto_local(decision):
        outcome = runner(
            user_prompt=request.prompt,
            task_kind=request.task_kind,
            route_class=auto_local_route_class_for_task(request.task_kind),
            context_blocks=context_blocks,
            max_output_tokens=request.max_tokens,
            context_build_error=context_build_error,
        )
        return _response_from_outcome(
            request=request,
            outcome=outcome,
            requested_workspace_id=requested_workspace_id,
        )

    started = time.perf_counter()
    status = _control_status(decision)
    ledger_id = _write_auto_control_job(
        status=status,
        task_kind=request.task_kind,
        prompt=request.prompt,
        decision=decision,
        context_blocks=context_blocks,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
    return AITaskRunResponse(
        status=status,
        ledger_id=ledger_id,
        selected_route_class=AUTO_ROUTE_CLASS,
        decision_reason=_decision_reason(decision),
        blocked_reason=_blocked_reason(decision, status),
        response_text=None,
        provider_id=None,
        model_id=None,
        usage=None,
        error_type=status,
        include_project_context=request.include_project_context,
        workspace_id=requested_workspace_id,
        context_digest=canonical_digest(context_blocks) if context_blocks else None,
        context_sources_count=len(context_sources_manifest(context_blocks)) if context_blocks else 0,
    )


def run_auto_task(
    request: AITaskRunRequest,
    *,
    context_blocks: list[dict] | None = None,
    context_build_error: str | None = None,
    requested_workspace_id: str | None = None,
) -> AITaskRunResponse:
    _router_input, decision = build_auto_decision(request)
    return resolve_bridge_outcome_from_decision(
        request=request,
        decision=decision,
        context_blocks=context_blocks,
        context_build_error=context_build_error,
        requested_workspace_id=requested_workspace_id,
    )


def _is_executable_auto_local(decision: dict) -> bool:
    return decision.get("proposed_external_target") is None and is_safe_local_execution(decision)


def auto_local_route_class_for_task(task_kind: str) -> str:
    return AUTO_LOCAL_ROUTE_BY_TASK_KIND.get(task_kind, AUTO_LOCAL_DEFAULT_ROUTE_CLASS)


def _control_status(decision: dict) -> str:
    if decision.get("proposed_external_target") is not None:
        return "proposed_external"
    route_action = decision.get("route_action")
    if route_action == "ask_user_confirm":
        return "needs_confirmation"
    if route_action == "ask_clarification":
        return "needs_clarification"
    if route_action == "blocked":
        return "blocked"
    return "propose_only"


def _decision_reason(decision: dict) -> str:
    reason_codes = decision.get("reason_codes")
    if isinstance(reason_codes, list) and reason_codes:
        return ",".join(str(reason) for reason in reason_codes)
    route_action = decision.get("route_action")
    route_tier = decision.get("route_tier")
    return f"auto:{route_action}:{route_tier}"


def _blocked_reason(decision: dict, status: str) -> str:
    if status == "proposed_external":
        return "auto_external_proposal_refused"
    route_action = decision.get("route_action")
    if isinstance(route_action, str) and route_action:
        return route_action
    return status


def _response_from_outcome(
    *,
    request: AITaskRunRequest,
    outcome: AiTaskOutcome,
    requested_workspace_id: str | None,
) -> AITaskRunResponse:
    response = outcome.response
    return AITaskRunResponse(
        status=outcome.status,
        ledger_id=outcome.ledger_id,
        selected_route_class=outcome.selected_route_class,
        decision_reason=outcome.decision.decision_reason,
        blocked_reason=outcome.decision.blocked_reason,
        response_text=response.text if response is not None else None,
        provider_id=response.provider_id if response is not None else outcome.decision.provider_id,
        model_id=response.model_id if response is not None else outcome.decision.model_id,
        usage=response.usage if response is not None else None,
        error_type=outcome.error_type,
        include_project_context=request.include_project_context,
        workspace_id=requested_workspace_id,
        context_digest=outcome.context_digest,
        context_sources_count=outcome.context_sources_count,
    )


def _write_auto_control_job(
    *,
    status: str,
    task_kind: str,
    prompt: str,
    decision: dict,
    context_blocks: list[dict] | None,
    latency_ms: int,
) -> str:
    job_id = str(uuid4())
    context_digest = canonical_digest(context_blocks) if context_blocks else None
    context_sources = context_sources_manifest(context_blocks) if context_blocks else None
    route_reason_json = json.dumps(
        {
            "decision_reason": _decision_reason(decision),
            "route_action": decision.get("route_action"),
            "route_tier": decision.get("route_tier"),
            "permissions": {
                "response_allowed_now": decision.get("response_allowed_now"),
                "external_allowed": decision.get("external_allowed"),
                "provider_call_allowed_now": decision.get("provider_call_allowed_now"),
                "external_network_allowed_now": decision.get("external_network_allowed_now"),
                "tool_execution_allowed_now": decision.get("tool_execution_allowed_now"),
                "state_change_allowed_now": decision.get("state_change_allowed_now"),
                "allowed_execution_mode": decision.get("allowed_execution_mode"),
            },
            "reason_codes": decision.get("reason_codes"),
            "blocked_reason": _blocked_reason(decision, status),
        },
        sort_keys=True,
    )
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_jobs (
                id, created_at, status, task_kind, requested_route_class, selected_route_class,
                provider_id, model_id, route_reason_json, prompt_digest, context_digest,
                context_sources_json, output_digest, input_tokens, output_tokens, cost_estimate,
                latency_ms, error_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                utc_now(),
                status,
                task_kind,
                AUTO_ROUTE_CLASS,
                AUTO_ROUTE_CLASS,
                None,
                None,
                route_reason_json,
                canonical_digest({"prompt": prompt}),
                context_digest,
                json.dumps(context_sources) if context_sources else None,
                None,
                None,
                None,
                None,
                latency_ms,
                status,
            ),
        )
        connection.commit()
    return job_id
