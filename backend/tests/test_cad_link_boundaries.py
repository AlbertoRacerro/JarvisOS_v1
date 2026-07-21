from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-cad-link")

    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _baseline() -> dict[str, dict[str, object]]:
    return {
        "tube_length": {"value": 20.0, "unit": "m"},
        "tube_inner_diameter": {"value": 30.0, "unit": "mm"},
        "tube_outer_diameter": {"value": 36.0, "unit": "mm"},
        "reservoir_liquid_volume": {"value": 5.0, "unit": "L"},
        "target_liquid_velocity": {"value": 0.25, "unit": "m/s"},
        "liquid_density": {"value": 1025.0, "unit": "kg/m3"},
        "dynamic_viscosity": {"value": 0.0011, "unit": "Pa*s"},
        "minor_loss_coefficient": {"value": 8.0, "unit": "1"},
        "pump_efficiency": {"value": 0.35, "unit": "1"},
    }


def _create_parameter(
    client: TestClient,
    *,
    workspace_id: str,
    name: str,
    value: str,
    unit: str,
    status: str = "accepted",
) -> str:
    response = client.post(
        f"/workspaces/{workspace_id}/parameters",
        json={
            "name": name,
            "value": value,
            "unit": unit,
            "value_status": "accepted" if status == "accepted" else "candidate",
            "status": status,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _source_run(
    client: TestClient,
    *,
    geometry_status: str = "accepted",
    cross_workspace_name: str | None = None,
) -> dict[str, Any]:
    registration = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-v0/register"
    )
    assert registration.status_code == 200, registration.text

    other_workspace_id = None
    if cross_workspace_name is not None:
        workspace = client.post(
            "/workspaces",
            json={"name": cross_workspace_name, "slug": cross_workspace_name.lower()},
        )
        assert workspace.status_code == 201, workspace.text
        other_workspace_id = workspace.json()["id"]

    inputs = _baseline()
    parameter_ids: dict[str, str] = {}
    for name in ("tube_length", "tube_inner_diameter", "tube_outer_diameter"):
        target_workspace = (
            other_workspace_id
            if other_workspace_id is not None and name == "tube_outer_diameter"
            else "bluerev"
        )
        parameter_id = _create_parameter(
            client,
            workspace_id=target_workspace,
            name=f"Boundary {name}",
            value=str(inputs[name]["value"]),
            unit=str(inputs[name]["unit"]),
            status=geometry_status,
        )
        parameter_ids[name] = parameter_id
        inputs[name]["source_parameter_id"] = parameter_id

    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": registration.json()["id"],
            "run_label": "cad-link-boundary-source",
            "input_set": inputs,
        },
    )
    assert created.status_code == 201, created.text
    executed = client.post(f"/runner-jobs/{created.json()['runner_job']['id']}/run")
    assert executed.status_code == 200, executed.text
    assert executed.json()["simulation_run"]["status"] == "succeeded"

    from app.core.database import open_sqlite_connection

    run_id = executed.json()["simulation_run"]["id"]
    job_id = executed.json()["runner_job"]["id"]
    with open_sqlite_connection() as connection:
        run = connection.execute(
            "SELECT model_version_id FROM simulation_runs WHERE id = ?", (run_id,)
        ).fetchone()
        model = connection.execute(
            "SELECT implementation_artifact_id FROM model_versions WHERE id = ?",
            (run["model_version_id"],),
        ).fetchone()

    return {
        "run_id": run_id,
        "job_id": job_id,
        "model_version_id": run["model_version_id"],
        "model_artifact_id": model["implementation_artifact_id"],
        "parameter_ids": parameter_ids,
    }


def _preview(client: TestClient, run_id: str, analysis_spec: dict[str, Any] | None = None):
    return client.post(
        "/workspaces/bluerev/bluecad/cad-link/047/preview",
        json={"source_simulation_run_id": run_id, "analysis_spec": analysis_spec},
    )


def _execute(
    client: TestClient,
    run_id: str,
    preview_digest: str,
    analysis_spec: dict[str, Any] | None = None,
):
    return client.post(
        "/workspaces/bluerev/bluecad/cad-link/047/execute",
        json={
            "source_simulation_run_id": run_id,
            "analysis_spec": analysis_spec,
            "preview_digest": preview_digest,
        },
    )


def _analysis_spec() -> dict[str, Any]:
    return {
        "schema_version": "bluecad_analysis_spec_v0_1",
        "analysis_id": "cad-link-analysis",
        "analysis_type": "static",
        "material": {
            "name": "polymer",
            "E": 2000.0,
            "nu": 0.35,
            "rho": 1.2e-9,
            "yield_strength": 40.0,
        },
        "bcs": [{"port_label": "illuminated_tube_proxy.port_a", "kind": "fixed"}],
        "loads": [
            {
                "port_label": "illuminated_tube_proxy.port_b",
                "type": "force_total",
                "force": [1.0, 0.0, 0.0],
            }
        ],
        "mesh": {"target_size": 10.0},
        "pass_criteria": [{"metric": "max_von_mises", "op": "<=", "value": 40.0}],
    }


def _mark_stale(
    client: TestClient,
    *,
    source_parameter_id: str,
    record_ref: str,
    record_kind: str,
    record_id: str,
) -> None:
    replacement_id = _create_parameter(
        client,
        workspace_id="bluerev",
        name="Freshness replacement fixture",
        value="21",
        unit="m",
        status="proposed",
    )
    invalidation_id = str(uuid4())
    now = "2026-07-21T00:00:00Z"

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO freshness_invalidations (
                id, workspace_id, superseded_parameter_id, replacement_parameter_id,
                source_graph_digest, affected_count, unresolved_diagnostic_count,
                cycle_count, created_at
            ) VALUES (?, 'bluerev', ?, ?, 'fixture-graph', 1, 0, 0, ?)
            """,
            (invalidation_id, source_parameter_id, replacement_id, now),
        )
        connection.execute(
            """
            INSERT INTO freshness_marks (
                id, workspace_id, invalidation_id, record_ref, record_kind,
                record_id, reason_code, path_json, path_digest, created_at
            ) VALUES (?, 'bluerev', ?, ?, ?, ?, 'fixture_stale', ?, ?, ?)
            """,
            (
                str(uuid4()),
                invalidation_id,
                record_ref,
                record_kind,
                record_id,
                json.dumps([record_ref]),
                f"fixture-path-{uuid4()}",
                now,
            ),
        )
        connection.commit()


@pytest.mark.parametrize("status", ["queued", "running", "failed", "timed_out"])
def test_non_succeeded_source_runs_fail_closed(client: TestClient, status: str) -> None:
    source = _source_run(client)
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE simulation_runs SET status = ? WHERE id = ?",
            (status, source["run_id"]),
        )
        connection.commit()

    response = _preview(client, source["run_id"])
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "cad_link_run_not_succeeded"


def test_stale_run_and_stale_parameter_have_distinct_bounded_errors(client: TestClient) -> None:
    source = _source_run(client)
    length_parameter = source["parameter_ids"]["tube_length"]
    _mark_stale(
        client,
        source_parameter_id=length_parameter,
        record_ref=f"simulation_run:{source['run_id']}",
        record_kind="simulation_run",
        record_id=source["run_id"],
    )
    response = _preview(client, source["run_id"])
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "cad_link_run_stale"

    second = _source_run(client)
    second_length = second["parameter_ids"]["tube_length"]
    _mark_stale(
        client,
        source_parameter_id=second_length,
        record_ref=f"parameter:{second_length}",
        record_kind="parameter",
        record_id=second_length,
    )
    parameter_response = _preview(client, second["run_id"])
    assert parameter_response.status_code == 409
    assert parameter_response.json()["detail"]["code"] == "cad_link_parameter_stale"


@pytest.mark.parametrize(
    ("target", "statement", "params"),
    [
        (
            "model label",
            "UPDATE model_versions SET version_label = 'tampered' WHERE id = ?",
            ("model_version_id",),
        ),
        (
            "input contract",
            "UPDATE model_versions SET input_contract_sha256 = 'tampered' WHERE id = ?",
            ("model_version_id",),
        ),
        (
            "registered script",
            "UPDATE artifacts SET sha256 = 'tampered' WHERE id = ?",
            ("model_artifact_id",),
        ),
        (
            "runner script",
            "UPDATE runner_jobs SET script_sha256 = 'tampered' WHERE id = ?",
            ("job_id",),
        ),
    ],
)
def test_model_identity_tampering_is_rejected(
    client: TestClient,
    target: str,
    statement: str,
    params: tuple[str, ...],
) -> None:
    source = _source_run(client)
    from app.core.database import open_sqlite_connection

    values = tuple(source[name] for name in params)
    with open_sqlite_connection() as connection:
        connection.execute(statement, values)
        connection.commit()

    response = _preview(client, source["run_id"])
    assert response.status_code == 422, target
    assert response.json()["detail"]["code"] == "cad_link_model_identity_mismatch"


def test_nonaccepted_and_cross_workspace_parameters_are_rejected(client: TestClient) -> None:
    proposed = _source_run(client, geometry_status="proposed")
    response = _preview(client, proposed["run_id"])
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "cad_link_parameter_not_accepted"

    cross_workspace = _source_run(client, cross_workspace_name="Other Project")
    cross_response = _preview(client, cross_workspace["run_id"])
    assert cross_response.status_code == 404
    assert cross_response.json()["detail"]["code"] == "cad_link_parameter_not_found"


def test_tampered_numeric_domain_and_outputs_fail_before_execution(client: TestClient) -> None:
    source = _source_run(client)
    outer_id = source["parameter_ids"]["tube_outer_diameter"]

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        run = connection.execute(
            "SELECT input_payload, output_payload FROM simulation_runs WHERE id = ?",
            (source["run_id"],),
        ).fetchone()
        inputs = json.loads(run["input_payload"])
        inputs["tube_outer_diameter"]["value"] = 30.0
        connection.execute(
            "UPDATE simulation_runs SET input_payload = ? WHERE id = ?",
            (json.dumps(inputs), source["run_id"]),
        )
        connection.execute("UPDATE parameters SET value = '30' WHERE id = ?", (outer_id,))
        connection.commit()

    invalid_geometry = _preview(client, source["run_id"])
    assert invalid_geometry.status_code == 422
    assert invalid_geometry.json()["detail"]["code"] == "cad_link_geometry_invalid"

    second = _source_run(client)
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT output_payload FROM simulation_runs WHERE id = ?",
            (second["run_id"],),
        ).fetchone()
        outputs = json.loads(row["output_payload"])
        outputs["outputs"]["tube_liquid_volume"]["value"] *= 1.1
        connection.execute(
            "UPDATE simulation_runs SET output_payload = ? WHERE id = ?",
            (json.dumps(outputs), second["run_id"]),
        )
        connection.commit()

    reconciliation = _preview(client, second["run_id"])
    assert reconciliation.status_code == 422
    assert reconciliation.json()["detail"]["code"] == "cad_link_reconciliation_failed"


def test_manifest_solid_volume_mismatch_parks_candidate(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_run(client)
    preview = _preview(client, source["run_id"]).json()

    from app.modules.bluecad import cad_link

    original_build = cad_link.build_geometry_spec

    def corrupt_manifest(spec: dict[str, Any], out_dir: str | Path):
        result = original_build(spec, out_dir)
        assert result.manifest is not None
        result.manifest["assembly"]["total_volume_mm3"] += 1000.0
        assert result.manifest_path is not None
        result.manifest_path.write_text(
            json.dumps(result.manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return result

    monkeypatch.setattr(cad_link, "build_geometry_spec", corrupt_manifest)
    response = _execute(client, source["run_id"], preview["preview_digest"])
    assert response.status_code == 200, response.text
    candidate = response.json()["candidate"]
    assert candidate["status"] == "parked"
    assert candidate["parked_reason"] == "cad_link_failed"
    assert candidate["attempts"][0]["validation_verdict"] == "fail"


def test_persistence_failure_never_exposes_valid_unlinked_candidate(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_run(client)
    preview = _preview(client, source["run_id"]).json()

    from app.modules.bluecad import cad_link

    def fail_registration(*args, **kwargs):
        raise RuntimeError("fixture artifact registration failure")

    monkeypatch.setattr(cad_link, "register_artifact", fail_registration)
    response = _execute(client, source["run_id"], preview["preview_digest"])
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "cad_link_persistence_failed"

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        candidates = connection.execute(
            "SELECT status, parked_reason FROM bluecad_candidates"
        ).fetchall()
        links = connection.execute("SELECT child_candidate_id FROM bluecad_cad_links").fetchall()
    assert len(candidates) == 1
    assert candidates[0]["status"] == "parked"
    assert candidates[0]["parked_reason"] == "cad_link_failed"
    assert len(links) == 1


def test_analysis_failure_preserves_registered_artifacts(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_run(client)
    analysis = _analysis_spec()
    preview = _preview(client, source["run_id"], analysis).json()

    from app.modules.bluecad import cad_link

    def fail_stage(*args, **kwargs) -> None:
        raise RuntimeError("fixture analysis-stage failure")

    monkeypatch.setattr(cad_link, "_run_simulation_stage", fail_stage)
    response = _execute(client, source["run_id"], preview["preview_digest"], analysis)
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "cad_link_persistence_failed"

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        candidate = connection.execute(
            "SELECT * FROM bluecad_candidates"
        ).fetchone()
        attempt = connection.execute(
            "SELECT * FROM bluecad_attempts"
        ).fetchone()
        artifact_rows = connection.execute(
            "SELECT stored_path FROM artifacts WHERE source_ref = ?",
            (f"bluecad_candidate:{candidate['id']}:attempt:1",),
        ).fetchall()
    assert candidate["status"] == "parked"
    assert candidate["parked_reason"] == "cad_link_failed"
    assert candidate["spec_artifact_id"] is not None
    assert candidate["report_artifact_id"] is not None
    assert candidate["glb_artifact_id"] is not None
    assert attempt["finished_at"] is not None
    assert len(artifact_rows) >= 4
    assert all(Path(row["stored_path"]).is_file() for row in artifact_rows)


def test_optional_analysis_reuses_existing_stage_without_ai(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_run(client)
    analysis = _analysis_spec()
    preview = _preview(client, source["run_id"], analysis).json()
    observed: dict[str, Any] = {}

    from app.modules.bluecad import cad_link

    def capture_stage(
        workspace_id: str,
        candidate_id: str,
        attempt_id: str,
        attempt_no: int,
        analysis_spec: dict[str, Any] | None,
        artifacts: dict[str, Any],
        *,
        producer_notes: str | None = None,
    ) -> None:
        observed.update(
            {
                "workspace_id": workspace_id,
                "candidate_id": candidate_id,
                "attempt_id": attempt_id,
                "attempt_no": attempt_no,
                "analysis_spec": analysis_spec,
                "artifacts": artifacts,
                "producer_notes": producer_notes,
            }
        )

    monkeypatch.setattr(cad_link, "_run_simulation_stage", capture_stage)
    response = _execute(client, source["run_id"], preview["preview_digest"], analysis)
    assert response.status_code == 200, response.text
    candidate = response.json()["candidate"]
    assert candidate["status"] == "valid"
    assert observed["workspace_id"] == "bluerev"
    assert observed["candidate_id"] == candidate["id"]
    assert observed["analysis_spec"] == analysis
    assert observed["artifacts"]["result"].manifest is not None
    assert observed["producer_notes"] == cad_link.ARTIFACT_PRODUCER

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        assert connection.execute("SELECT COUNT(*) AS count FROM ai_jobs").fetchone()["count"] == 0


def test_optional_analysis_artifacts_keep_process_linked_provenance(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_run(client)
    analysis = _analysis_spec()
    preview = _preview(client, source["run_id"], analysis).json()

    from app.modules.bluecad import cad_link, loop

    monkeypatch.setattr(
        loop,
        "mesh_analysis_spec",
        lambda *args, **kwargs: {
            "schema_version": "bluecad_mesh_result_v0_1",
            "verdict": "fail",
            "errors": [{"code": "MESH_GROUP_EMPTY", "detail": {"group": "LOAD_tube_proxy_port_b"}}],
            "attempts": [
                {
                    "attempt_no": 1,
                    "target_size": 5.0,
                    "counts": {},
                    "errors": [],
                }
            ],
            "artifacts": {},
        },
    )

    response = _execute(client, source["run_id"], preview["preview_digest"], analysis)
    assert response.status_code == 200, response.text

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT notes FROM artifacts WHERE artifact_type = 'bluecad_sim_report'"
        ).fetchall()
        ai_job_count = connection.execute(
            "SELECT COUNT(*) AS count FROM ai_jobs"
        ).fetchone()["count"]

    assert len(rows) == 1
    assert rows[0]["notes"] == cad_link.ARTIFACT_PRODUCER
    assert "AI loop" not in rows[0]["notes"]
    assert ai_job_count == 0



def test_replay_rejects_inconsistent_persisted_link(client: TestClient) -> None:
    source = _source_run(client)
    preview = _preview(client, source["run_id"]).json()
    first = _execute(client, source["run_id"], preview["preview_digest"])
    assert first.status_code == 200, first.text

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE bluecad_cad_links SET transformation_version = 'tampered' "
            "WHERE preview_digest = ?",
            (preview["preview_digest"],),
        )
        connection.commit()

    replay = _execute(client, source["run_id"], preview["preview_digest"])
    assert replay.status_code == 409
    assert replay.json()["detail"]["code"] == "cad_link_persistence_inconsistent"

    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS count FROM bluecad_candidates"
        ).fetchone()["count"] == 1
        assert connection.execute(
            "SELECT COUNT(*) AS count FROM bluecad_attempts"
        ).fetchone()["count"] == 1
        assert connection.execute(
            "SELECT COUNT(*) AS count FROM bluecad_cad_links"
        ).fetchone()["count"] == 1


def test_concurrent_execute_owns_one_candidate_and_one_link(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_run(client)
    preview = _preview(client, source["run_id"]).json()

    from app.modules.bluecad import cad_link

    request = cad_link.CadLinkExecuteRequest(
        source_simulation_run_id=source["run_id"],
        analysis_spec=None,
        preview_digest=preview["preview_digest"],
    )
    original_build = cad_link.build_geometry_spec
    entered_build = threading.Event()
    release_build = threading.Event()

    def slow_build(spec: dict[str, Any], out_dir: str | Path):
        entered_build.set()
        assert release_build.wait(timeout=15)
        return original_build(spec, out_dir)

    monkeypatch.setattr(cad_link, "build_geometry_spec", slow_build)
    results: list[Any] = []
    errors: list[BaseException] = []

    def call_execute() -> None:
        try:
            results.append(cad_link.execute_cad_link_047("bluerev", request))
        except BaseException as exc:  # pragma: no cover - diagnostic capture
            errors.append(exc)

    first = threading.Thread(target=call_execute)
    first.start()
    assert entered_build.wait(timeout=15)

    second = threading.Thread(target=call_execute)
    second.start()
    second.join(timeout=10)
    assert not second.is_alive()
    release_build.set()
    first.join(timeout=20)
    assert not first.is_alive()
    assert not errors
    assert len(results) == 2
    assert {result.replayed for result in results} == {False, True}
    assert len({result.link_id for result in results}) == 1
    assert len({result.candidate.id for result in results}) == 1

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS count FROM bluecad_candidates"
        ).fetchone()["count"] == 1
        assert connection.execute(
            "SELECT COUNT(*) AS count FROM bluecad_attempts"
        ).fetchone()["count"] == 1
        assert connection.execute(
            "SELECT COUNT(*) AS count FROM bluecad_cad_links"
        ).fetchone()["count"] == 1


def test_historical_ai_candidate_edges_remain_advisory(client: TestClient) -> None:
    from app.core.database import open_sqlite_connection

    now = "2026-07-21T00:00:00Z"
    candidate_id = str(uuid4())
    attempt_id = str(uuid4())
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO bluecad_candidates (
                id, workspace_id, brief_text, brief_digest, status, origin,
                loop_config_json, created_at, updated_at
            ) VALUES (?, 'bluerev', 'historical ai fixture', 'digest', 'generating',
                'ai', '{}', ?, ?)
            """,
            (candidate_id, now, now),
        )
        connection.execute(
            """
            INSERT INTO bluecad_attempts (
                id, candidate_id, attempt_no, route_class, proposal_outcome, started_at
            ) VALUES (?, ?, 1, 'external:cheap', 'blocked', ?)
            """,
            (attempt_id, candidate_id, now),
        )
        connection.commit()

    graph = client.get("/workspaces/bluerev/flowsheet/graph")
    assert graph.status_code == 200, graph.text
    edge = next(
        item
        for item in graph.json()["edges"]
        if item["upstream_ref"] == f"bluecad_candidate:{candidate_id}"
        and item["downstream_ref"] == f"bluecad_attempt:{attempt_id}"
    )
    assert edge["relation"] == "has_attempt"
    assert edge["edge_class"] == "provenance"
