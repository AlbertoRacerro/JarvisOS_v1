from __future__ import annotations

from pathlib import Path

EGRESS = Path("backend/app/modules/ai/egress_runtime.py")
EXECUTION = Path("backend/app/modules/ai/execution.py")
EGRESS_TEST = Path("backend/tests/test_ai_egress_runtime.py")


def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    path.write_text(source.replace(old, new), encoding="utf-8")


replace_once(
    EGRESS,
    "from app.modules.ai.token_flow_runtime import normalize_outcome_reason\n",
    "from app.modules.ai.token_flow_runtime import normalize_finish_reason, normalize_outcome_reason\n",
)
replace_once(
    EGRESS,
    '''def _create_external_flow(
''',
    '''def _reconcilable_start_failure_reservation(reservation_id: str) -> str | None:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT state FROM egress_budget_reservations WHERE id = ?",
            (reservation_id,),
        ).fetchone()
    if row is None or row["state"] in _TERMINAL_RESERVATION_STATES:
        return None
    return reservation_id


def _create_external_flow(
''',
)
replace_once(
    EGRESS,
    '''    if outcome.status == "success":
        state = "complete"
        reason = "completed"
    else:
''',
    '''    finish_reason = (
        normalize_finish_reason(outcome.response.finish_reason, failed=False)
        if outcome.status == "success" and outcome.response is not None
        else None
    )
    if outcome.status == "success" and finish_reason == "length":
        state = "partial_terminal"
        reason = "output_length_limit"
    elif outcome.status == "success":
        state = "complete"
        reason = "completed"
    else:
''',
)
replace_once(
    EGRESS,
    '''            outcome_reason="egress_start_failed",
            reservation_id=reservation_id,
            registry=registry,
''',
    '''            outcome_reason="egress_start_failed",
            reservation_id=_reconcilable_start_failure_reservation(reservation_id),
            registry=registry,
''',
)

replace_once(
    EXECUTION,
    '''    no_execution_evidence,
    normalize_outcome_reason,
''',
    '''    no_execution_evidence,
    normalize_finish_reason,
    normalize_outcome_reason,
''',
)
replace_once(
    EXECUTION,
    '''    attempt_id: str,
    reason: str | None,
) -> None:
    if status == "success":
        state = "complete"
        terminal_reason = "completed"
    else:
''',
    '''    attempt_id: str,
    reason: str | None,
    finish_reason: str | None = None,
) -> None:
    normalized_finish = normalize_finish_reason(finish_reason, failed=False)
    if status == "success" and normalized_finish == "length":
        state = "partial_terminal"
        terminal_reason = "output_length_limit"
    elif status == "success":
        state = "complete"
        terminal_reason = "completed"
    else:
''',
)
replace_once(
    EXECUTION,
    '''        _terminalize_local_flow(
            flow_id=flow_id,
            status=status,
            attempt_id=ledger_id,
            reason=error_type,
        )
        if status == "success":
''',
    '''        _terminalize_local_flow(
            flow_id=flow_id,
            status=status,
            attempt_id=ledger_id,
            reason=error_type,
            finish_reason=response.finish_reason,
        )
        if status == "success" and normalize_finish_reason(
            response.finish_reason, failed=False
        ) != "length":
''',
)

with EGRESS_TEST.open("a", encoding="utf-8") as handle:
    handle.write(
        '''


def test_length_response_is_recorded_as_partial_terminal(monkeypatch):
    _bootstrap(monkeypatch)
    _seed_prior_network_attempt()

    class LengthAdapter(CountingAdapter):
        def complete(self, request: AIRequest) -> AIResponse:
            response = super().complete(request)
            return response.model_copy(update={"finish_reason": "length"})

    adapter = LengthAdapter(text="Truncated provider answer.")
    outcome = _run(adapter)

    assert outcome.status == "success"
    assert adapter.calls == 1
    with open_sqlite_connection() as connection:
        flow = connection.execute(
            "SELECT state, terminal_reason, terminal_attempt_id FROM ai_flows WHERE id = ?",
            (outcome.flow_id,),
        ).fetchone()
    assert flow["state"] == "partial_terminal"
    assert flow["terminal_reason"] == "output_length_limit"
    assert flow["terminal_attempt_id"] == outcome.ledger_id


def test_expired_reservation_start_failure_finalizes_job_and_flow(monkeypatch):
    _bootstrap(monkeypatch)
    _seed_prior_network_attempt()
    from app.modules.ai import egress_runtime

    real_start = egress_runtime.start_reserved_attempt

    def expire_before_start(reservation_id: str, *, ai_job_id: str):
        return real_start(
            reservation_id,
            ai_job_id=ai_job_id,
            now=datetime(2100, 1, 1, tzinfo=UTC),
        )

    monkeypatch.setattr(egress_runtime, "start_reserved_attempt", expire_before_start)
    adapter = CountingAdapter()
    outcome = _run(adapter)

    assert outcome.status == "config_error"
    assert outcome.egress_reason_code == "egress_start_failed"
    assert adapter.calls == 0
    with open_sqlite_connection() as connection:
        reservation = connection.execute(
            "SELECT state, reconciliation_status FROM egress_budget_reservations WHERE id = ?",
            (outcome.egress_reservation_id,),
        ).fetchone()
        job = connection.execute(
            """
            SELECT status, flow_id, execution_class, adapter_invoked,
                   external_dispatch_state, normalized_usage_source, accounting_basis
            FROM ai_jobs WHERE id = ?
            """,
            (outcome.ledger_id,),
        ).fetchone()
        flow = connection.execute(
            "SELECT state, terminal_reason, terminal_attempt_id FROM ai_flows WHERE id = ?",
            (outcome.flow_id,),
        ).fetchone()
    assert reservation["state"] == "expired"
    assert reservation["reconciliation_status"] == "expired_before_start"
    assert job["status"] == "config_error"
    assert job["flow_id"] == outcome.flow_id
    assert job["execution_class"] == "external_provider"
    assert job["adapter_invoked"] == 0
    assert job["external_dispatch_state"] == "not_started"
    assert job["normalized_usage_source"] == "none"
    assert job["accounting_basis"] == "external_not_sent"
    assert flow["state"] == "failed_terminal"
    assert flow["terminal_reason"] == "egress_start_failed"
    assert flow["terminal_attempt_id"] == outcome.ledger_id
'''
    )
