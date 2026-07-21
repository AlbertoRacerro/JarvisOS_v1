from __future__ import annotations

import json

import pytest
import test_token_flow_confirmed_length_resume as confirmed_length
import test_token_flow_external_runtime_integration as integration

from app.core.database import open_sqlite_connection
from app.modules.ai.egress_confirmation import run_confirmation_ticket
from app.modules.ai.flow_record_capture import capture_final_flow_records
from app.modules.ai.token_flow_service import get_flow
from app.modules.memory import service as memory_service

initialized_database = integration.initialized_database

RECORD_OUTPUT = (
    "assembled decision\n"
    "```jarvis-records\n"
    '{"record_version":"jarvis_records_v0","records":['
    '{"record_kind":"decision","title":"Use bounded continuation",'
    '"decision_text":"Keep exact-stop capture transactional"},'
    '{"record_kind":"assumption","statement":"The final assembly is canonical"}'
    "]}\n"
    "```"
)


def _complete_confirmed_capture():
    paused = integration._pause_external_continuation(task_kind="decision_support")
    adapter = integration.ConfirmedExternalAdapter(text=RECORD_OUTPUT, finish_reason="stop")
    outcome = run_confirmation_ticket(
        str(paused.egress_ticket_id),
        adapters={integration.BINDING.provider_id: adapter},
    ).outcome
    assert outcome.response is not None
    return paused, outcome


def test_confirmed_final_assembly_captures_once_and_replays_same_ids(
    initialized_database,
) -> None:
    paused, outcome = _complete_confirmed_capture()

    assert outcome.status == "success"
    assert outcome.proposed_record_ids is not None
    assert len(outcome.proposed_record_ids) == 2
    assert outcome.records_parse_error is None
    flow = get_flow(str(paused.flow_id))
    assert flow["state"] == "complete"

    replay = capture_final_flow_records(
        task_kind="decision_support",
        response_text=outcome.response.text,
        terminal_attempt_id=outcome.ledger_id,
        workspace_id=integration.WORKSPACE_ID,
    )
    assert replay is not None
    assert replay.replayed is True
    assert list(replay.proposal_ids) == outcome.proposed_record_ids

    with open_sqlite_connection() as connection:
        receipt = connection.execute(
            "SELECT proposal_ids_json, parse_error FROM ai_flow_record_captures WHERE flow_id = ?",
            (paused.flow_id,),
        ).fetchone()
        decisions = connection.execute(
            "SELECT id, source_ai_job_id FROM decisions WHERE origin = 'ai_proposed'"
        ).fetchall()
        assumptions = connection.execute(
            "SELECT id, source_ai_job_id FROM assumptions WHERE origin = 'ai_proposed'"
        ).fetchall()
    assert json.loads(receipt["proposal_ids_json"]) == outcome.proposed_record_ids
    assert receipt["parse_error"] is None
    created = [*decisions, *assumptions]
    assert len(created) == 2
    assert {row["id"] for row in created} == set(outcome.proposed_record_ids)
    assert {row["source_ai_job_id"] for row in created} == {outcome.ledger_id}


class _ConfirmedLengthRecordAdapter(
    confirmed_length._ConfirmedLengthSequenceAdapter
):
    def complete(self, request):
        response = super().complete(request)
        if len(self.requests) == 2:
            return response.model_copy(
                update={"text": RECORD_OUTPUT, "content": RECORD_OUTPUT}
            )
        return response


def test_confirmed_repeated_length_captures_final_assembly_once(
    initialized_database,
) -> None:
    paused = integration._pause_external_continuation(task_kind="decision_support")
    adapter = _ConfirmedLengthRecordAdapter(final_finish_reason="stop")

    outcome = run_confirmation_ticket(
        str(paused.egress_ticket_id),
        adapters={integration.BINDING.provider_id: adapter},
    ).outcome

    assert outcome.status == "success"
    assert outcome.response is not None
    assert outcome.response.text.startswith("external alpha confirmed beta ")
    assert len(adapter.requests) == 2
    assert outcome.proposed_record_ids is not None
    assert len(outcome.proposed_record_ids) == 2
    with open_sqlite_connection() as connection:
        receipt_count = connection.execute(
            "SELECT COUNT(*) AS count FROM ai_flow_record_captures WHERE flow_id = ?",
            (paused.flow_id,),
        ).fetchone()["count"]
    assert receipt_count == 1


def test_complete_output_without_records_is_receipted_once(
    initialized_database,
) -> None:
    paused = integration._pause_external_continuation(task_kind="decision_support")
    adapter = integration.ConfirmedExternalAdapter(
        text="plain complete answer",
        finish_reason="stop",
    )

    outcome = run_confirmation_ticket(
        str(paused.egress_ticket_id),
        adapters={integration.BINDING.provider_id: adapter},
    ).outcome

    assert outcome.proposed_record_ids == []
    assert outcome.records_parse_error is None
    replay = capture_final_flow_records(
        task_kind="decision_support",
        response_text=outcome.response.text if outcome.response is not None else None,
        terminal_attempt_id=outcome.ledger_id,
        workspace_id=integration.WORKSPACE_ID,
    )
    assert replay is not None
    assert replay.replayed is True
    assert replay.proposal_ids == ()
    with open_sqlite_connection() as connection:
        receipt = connection.execute(
            "SELECT proposal_ids_json, parse_error FROM ai_flow_record_captures WHERE flow_id = ?",
            (paused.flow_id,),
        ).fetchone()
    assert tuple(receipt) == ("[]", None)


def test_capture_receipt_and_proposals_roll_back_together(
    initialized_database, monkeypatch
) -> None:
    paused = integration._pause_external_continuation(task_kind="decision_support")
    adapter = integration.ConfirmedExternalAdapter(text=RECORD_OUTPUT, finish_reason="stop")
    original = memory_service._create_proposal_in_transaction
    calls = 0

    def fail_second(connection, payload):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected capture failure")
        return original(connection, payload)

    monkeypatch.setattr(memory_service, "_create_proposal_in_transaction", fail_second)
    with pytest.raises(RuntimeError, match="injected capture failure"):
        run_confirmation_ticket(
            str(paused.egress_ticket_id),
            adapters={integration.BINDING.provider_id: adapter},
        )

    with open_sqlite_connection() as connection:
        receipt_count = connection.execute(
            "SELECT COUNT(*) AS count FROM ai_flow_record_captures WHERE flow_id = ?",
            (paused.flow_id,),
        ).fetchone()["count"]
        proposal_count = connection.execute(
            """
            SELECT (
                SELECT COUNT(*) FROM decisions WHERE origin = 'ai_proposed'
            ) + (
                SELECT COUNT(*) FROM assumptions WHERE origin = 'ai_proposed'
            ) AS count
            """
        ).fetchone()["count"]
    assert receipt_count == 0
    assert proposal_count == 0
    assert get_flow(str(paused.flow_id))["state"] == "complete"


def test_partial_confirmed_output_never_creates_capture_receipt(
    initialized_database,
) -> None:
    paused = integration._pause_external_continuation(task_kind="decision_support")
    adapter = integration.ConfirmedExternalAdapter(text=RECORD_OUTPUT, finish_reason=None)

    outcome = run_confirmation_ticket(
        str(paused.egress_ticket_id),
        adapters={integration.BINDING.provider_id: adapter},
    ).outcome

    assert outcome.proposed_record_ids in (None, [])
    assert get_flow(str(paused.flow_id))["state"] == "partial_terminal"
    with open_sqlite_connection() as connection:
        receipt_count = connection.execute(
            "SELECT COUNT(*) AS count FROM ai_flow_record_captures WHERE flow_id = ?",
            (paused.flow_id,),
        ).fetchone()["count"]
        proposal_count = connection.execute(
            "SELECT COUNT(*) AS count FROM decisions WHERE origin = 'ai_proposed'"
        ).fetchone()["count"]
    assert receipt_count == 0
    assert proposal_count == 0
