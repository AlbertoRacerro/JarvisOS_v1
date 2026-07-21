from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import test_flow_grade_cohorts as cohort_tests

from app.core.database import open_sqlite_connection
from app.modules.ai import flow_grade_cohort_store
from app.modules.ai.flow_grade_cohorts import get_flow_grade_cohort

initialized_database = cohort_tests.initialized_database


def test_cohort_queries_never_select_private_grade_notes(
    initialized_database,
    monkeypatch,
) -> None:
    flow_id = cohort_tests._seed_flow(
        execution_class="local_compute",
        dispatch_state="not_applicable",
        accounting_basis="local_compute_unpriced",
        spend="0",
    )
    cohort_tests._grade(flow_id, "useful", "private-note-grade")
    statements: list[str] = []

    @contextmanager
    def traced_connection() -> Iterator[object]:
        with open_sqlite_connection() as connection:
            connection.set_trace_callback(statements.append)
            yield connection

    monkeypatch.setattr(
        flow_grade_cohort_store,
        "open_sqlite_connection",
        traced_connection,
    )

    cohort = get_flow_grade_cohort()

    assert cohort.current_grade_counts["useful"] == 1
    executed_sql = "\n".join(statements).casefold()
    assert "note_text" not in executed_sql
    assert "select event.*" not in executed_sql
