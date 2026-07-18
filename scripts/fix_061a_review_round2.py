from pathlib import Path

EXECUTION = Path("backend/app/modules/ai/execution.py")
TEST = Path("backend/tests/test_token_flow_review_round2.py")

text = EXECUTION.read_text(encoding="utf-8")

old_capture = """    if external.status == \"success\" and external.response is not None:\n        proposed_record_ids, records_parse_error = _create_proposed_records_from_response(\n"""
new_capture = """    if (\n        external.status == \"success\"\n        and external.response is not None\n        and normalize_finish_reason(\n            external.response.finish_reason, failed=external.response.error is not None\n        )\n        != \"length\"\n    ):\n        proposed_record_ids, records_parse_error = _create_proposed_records_from_response(\n"""
if text.count(old_capture) != 1:
    raise SystemExit("unexpected external record-capture gate")
text = text.replace(old_capture, new_capture, 1)

old_budget = """        fallback_index = 0 if early_binding is not None else None\n        evidence = no_execution_evidence(\n            selected_route_class=selected_route_class,\n            binding=early_binding,\n            outcome_reason=\"context_budget_exceeded\",\n            requested_output_ceiling=max_output_tokens,\n            effective_output_ceiling=None,\n            fallback_index=fallback_index,\n        )\n        ledger_id = _write_ai_job(\n            status=\"validation_error\",\n            task_kind=task_kind,\n            requested_route_class=requested_route_class,\n            selected_route_class=selected_route_class,\n"""
new_budget = """        fallback_index = 0 if early_binding is not None else None\n        persisted_route = _flow_requested_route(selected_route_class)\n        evidence = no_execution_evidence(\n            selected_route_class=persisted_route,\n            binding=early_binding,\n            outcome_reason=\"context_budget_exceeded\",\n            requested_output_ceiling=max_output_tokens,\n            effective_output_ceiling=None,\n            fallback_index=fallback_index,\n        )\n        ledger_id = _write_ai_job(\n            status=\"validation_error\",\n            task_kind=task_kind,\n            requested_route_class=requested_route_class,\n            selected_route_class=persisted_route,\n"""
if text.count(old_budget) != 1:
    raise SystemExit("unexpected context-budget branch")
text = text.replace(old_budget, new_budget, 1)
EXECUTION.write_text(text, encoding="utf-8")

TEST.write_text(
    '''from __future__ import annotations

import pytest

from app.modules.ai.context_builder import DEFAULT_CONTEXT_BUDGET_CHARS
from app.modules.ai.contracts import AIResponse, AIUsage, RoutingDecision
from app.modules.ai.egress_runtime import ExternalTaskOutcome


def test_external_length_response_skips_record_capture(monkeypatch) -> None:
    from app.modules.ai import execution

    response = AIResponse(
        provider_id="fake",
        model_id="fake-modeling-draft-v1",
        text="Truncated external answer.",
        content="Truncated external answer.",
        finish_reason="length",
        usage=AIUsage(
            provider_id="fake",
            model_id="fake-modeling-draft-v1",
            input_tokens=3,
            output_tokens=4,
        ),
    )
    external = ExternalTaskOutcome(
        status="success",
        ledger_id="job-1",
        selected_route_class="external:cheap",
        decision=RoutingDecision(
            provider_id="fake",
            model_id="fake-modeling-draft-v1",
            decision_reason="test",
        ),
        response=response,
        error_type=None,
        context_digest=None,
        context_sources_count=0,
        retryable_error_code=None,
        egress_decision_id=None,
        egress_packet_digest=None,
        egress_ticket_id=None,
        egress_reservation_id=None,
        egress_reason_code=None,
        egress_trigger_ids=(),
        flow_id="flow-1",
    )
    monkeypatch.setattr(
        "app.modules.ai.egress_runtime.run_external_task",
        lambda **_kwargs: external,
    )

    def fail_capture(**_kwargs):
        pytest.fail("partial external output must not create proposed records")

    monkeypatch.setattr(execution, "_create_proposed_records_from_response", fail_capture)

    outcome = execution._run_external_network_task(
        user_prompt="Return a bounded decision.",
        task_kind="decision_support",
        requested_route_class="external:cheap",
        selected_route_class="external:cheap",
        context_blocks=None,
        max_output_tokens=32,
        adapters={},
        bindings={},
        external_blocked_reason=None,
        context_build_error=None,
        workspace_id="workspace-1",
    )

    assert outcome.status == "success"
    assert outcome.proposed_record_ids is None
    assert outcome.records_parse_error is None


def test_malformed_route_budget_failure_records_terminal_flow(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "malformed-budget"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.database import initialize_database, open_sqlite_connection
    from app.modules.ai.execution import run_ai_task
    from app.modules.ai.settings import ensure_ai_settings

    initialize_database()
    ensure_ai_settings()

    outcome = run_ai_task(
        user_prompt="Validate bounded context handling.",
        task_kind="general",
        route_class="bad route",
        context_blocks=[
            {
                "source": "test:oversized",
                "content": "x" * (DEFAULT_CONTEXT_BUDGET_CHARS + 1024),
            }
        ],
        max_output_tokens=16,
        adapters={},
        bindings={},
    )

    assert outcome.status == "validation_error"
    assert outcome.error_type == "context_budget_exceeded"
    assert outcome.flow_id is not None
    with open_sqlite_connection() as connection:
        job = connection.execute(
            "SELECT selected_route_class, flow_id, execution_class, outcome_reason "
            "FROM ai_jobs WHERE id = ?",
            (outcome.ledger_id,),
        ).fetchone()
        flow = connection.execute(
            "SELECT state, terminal_reason, terminal_attempt_id FROM ai_flows WHERE id = ?",
            (outcome.flow_id,),
        ).fetchone()

    assert job["selected_route_class"] is None
    assert job["flow_id"] == outcome.flow_id
    assert job["execution_class"] == "none"
    assert job["outcome_reason"] == "context_budget_exceeded"
    assert flow["state"] == "failed_terminal"
    assert flow["terminal_reason"] == "context_budget_exceeded"
    assert flow["terminal_attempt_id"] == outcome.ledger_id
''',
    encoding="utf-8",
)
