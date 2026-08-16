from __future__ import annotations

import app.modules.ai.thread_service as thread_service
import test_token_flow_external_runtime_integration as external_integration

from app.core.database import open_sqlite_connection
from app.modules.ai.thread_models import AIThreadCreate, AIThreadSubmit
from app.modules.ai.thread_service import create_thread, submit_interaction
from app.modules.ai.token_flow_service import get_flow


initialized_database = external_integration.initialized_database


def test_thread_submit_reuses_precreated_flow_through_external_059b_runtime(
    initialized_database,
    monkeypatch,
) -> None:
    workspace_id = external_integration.WORKSPACE_ID
    thread = create_thread(
        AIThreadCreate(workspace_id=workspace_id, title="External 059b verification")
    )
    adapter = external_integration.ConfirmedExternalAdapter(text="external thread result")
    canonical_run_ai_task = thread_service.run_ai_task

    def run_with_fake_external(**kwargs):
        return canonical_run_ai_task(
            **kwargs,
            adapters={external_integration.BINDING.provider_id: adapter},
            bindings={external_integration.BINDING.route_class: external_integration.BINDING},
        )

    monkeypatch.setattr(thread_service, "run_ai_task", run_with_fake_external)

    interaction = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(
            request_id="external-request-1",
            prompt="Return one bounded external answer.",
            task_kind="general",
            route_class=external_integration.BINDING.route_class,
            max_tokens=64,
        ),
    ).interaction

    assert interaction.persistence_state == "captured"
    assert interaction.flow_state == "complete"
    assert interaction.attempt_count == 1
    assert interaction.assistant_text == "external thread result"
    assert len(adapter.requests) == 1

    flow = get_flow(interaction.flow_id)
    assert flow["requested_route_class"] == external_integration.BINDING.route_class
    assert flow["attempt_count"] == 1
    assert float(flow["external_provider_spend_usd_decimal"]) > 0

    with open_sqlite_connection() as connection:
        owned_flow_count = connection.execute(
            "SELECT COUNT(*) AS n FROM ai_flows WHERE id = ?",
            (interaction.flow_id,),
        ).fetchone()["n"]
        jobs = connection.execute(
            """
            SELECT flow_id, requested_route_class, selected_route_class,
                   provider_id, external_dispatch_state
            FROM ai_jobs
            WHERE flow_id = ?
            """,
            (interaction.flow_id,),
        ).fetchall()
        interaction_flow = connection.execute(
            "SELECT flow_id FROM ai_thread_interactions WHERE id = ?",
            (interaction.id,),
        ).fetchone()["flow_id"]

    assert owned_flow_count == 1
    assert interaction_flow == interaction.flow_id
    assert len(jobs) == 1
    assert jobs[0]["flow_id"] == interaction.flow_id
    assert jobs[0]["requested_route_class"] == external_integration.BINDING.route_class
    assert jobs[0]["selected_route_class"] == external_integration.BINDING.route_class
    assert jobs[0]["provider_id"] == external_integration.BINDING.provider_id
    assert jobs[0]["external_dispatch_state"] == "started"
