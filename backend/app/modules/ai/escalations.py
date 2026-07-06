from __future__ import annotations

import json

from app.core.database import open_sqlite_connection
from app.modules.ai.budget import evaluate_ai_status
from app.modules.ai.execution import resolve_binding, run_ai_task
from app.modules.ai.models import AITaskRunResponse, EscalationConfirmRequest, EscalationConfirmResponse
from app.modules.ai.settings import get_ai_settings


def confirm_escalation(request: EscalationConfirmRequest) -> EscalationConfirmResponse:
    proposal = request.proposal
    proposal_ledger_id = str(proposal.get("proposal_ledger_id") or "")
    route_class = str(proposal.get("proposed_route_class") or "external:reasoning")
    outbound_text = str(proposal.get("outbound_text") or "")
    max_tokens = None
    estimated = proposal.get("estimated_cost")
    if isinstance(estimated, dict) and estimated.get("max_output_tokens") is not None:
        max_tokens = int(estimated["max_output_tokens"])

    settings = get_ai_settings()
    binding, _decision = resolve_binding(route_class)
    provider_mode = binding.provider_id if binding is not None else route_class
    status = evaluate_ai_status(settings, provider_mode)
    external_blocked_reason = None if status.external_calls_allowed else status.blocking_reason or "external_calls_disabled"
    outcome = run_ai_task(
        user_prompt=outbound_text,
        task_kind=request.task_kind,
        route_class=route_class,
        context_blocks=None,
        max_output_tokens=max_tokens,
        external_blocked_reason=external_blocked_reason,
    )
    _link_execution_job(outcome.ledger_id, proposal_ledger_id)
    response = outcome.response
    task_response = AITaskRunResponse(
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
        include_project_context=False,
        workspace_id=None,
        context_digest=outcome.context_digest,
        context_sources_count=outcome.context_sources_count,
    )
    return EscalationConfirmResponse(
        status=outcome.status,
        proposal_ledger_id=proposal_ledger_id,
        execution_ledger_id=outcome.ledger_id,
        task_response=task_response,
    )


def _link_execution_job(execution_ledger_id: str, proposal_ledger_id: str) -> None:
    with open_sqlite_connection() as connection:
        row = connection.execute("SELECT route_reason_json FROM ai_jobs WHERE id = ?", (execution_ledger_id,)).fetchone()
        if row is None:
            return
        route_reason = json.loads(row["route_reason_json"])
        route_reason["escalation_proposal_ledger_id"] = proposal_ledger_id
        connection.execute(
            "UPDATE ai_jobs SET route_reason_json = ? WHERE id = ?",
            (json.dumps(route_reason, sort_keys=True), execution_ledger_id),
        )
        connection.commit()
