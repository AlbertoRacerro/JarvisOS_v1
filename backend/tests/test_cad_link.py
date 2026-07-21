import json
from collections.abc import Iterator
from pathlib import Path

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
    name: str,
    value: str,
    unit: str,
    status: str = "accepted",
    supersedes_parameter_id: str | None = None,
) -> str:
    payload: dict[str, object] = {
        "name": name,
        "value": value,
        "unit": unit,
        "value_status": "accepted" if status == "accepted" else "candidate",
        "status": status,
    }
    if supersedes_parameter_id is not None:
        payload["supersedes_parameter_id"] = supersedes_parameter_id
    response = client.post("/workspaces/bluerev/parameters", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _successful_source_run(client: TestClient, *, manual_geometry: set[str] | None = None) -> dict[str, object]:
    registration = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-v0/register"
    )
    assert registration.status_code == 200, registration.text
    inputs = _baseline()
    parameter_ids: dict[str, str] = {}
    manual_geometry = manual_geometry or set()
    for name in ("tube_length", "tube_inner_diameter", "tube_outer_diameter"):
        if name in manual_geometry:
            continue
        value = str(inputs[name]["value"])
        parameter_id = _create_parameter(
            client,
            name=f"Canonical {name}",
            value=value,
            unit=str(inputs[name]["unit"]),
        )
        parameter_ids[name] = parameter_id
        inputs[name]["source_parameter_id"] = parameter_id

    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": registration.json()["id"],
            "run_label": "cad-link-source-047",
            "input_set": inputs,
        },
    )
    assert created.status_code == 201, created.text
    executed = client.post(f"/runner-jobs/{created.json()['runner_job']['id']}/run")
    assert executed.status_code == 200, executed.text
    assert executed.json()["simulation_run"]["status"] == "succeeded"
    return {
        "run_id": executed.json()["simulation_run"]["id"],
        "runner_job_id": executed.json()["runner_job"]["id"],
        "parameter_ids": parameter_ids,
        "output": executed.json()["output"],
    }


def _table_counts() -> dict[str, int]:
    from app.core.database import open_sqlite_connection

    tables = (
        "bluecad_candidates",
        "bluecad_attempts",
        "bluecad_cad_links",
        "artifacts",
        "evidence_records",
        "simulation_runs",
        "ai_jobs",
        "events",
    )
    with open_sqlite_connection() as connection:
        return {
            table: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
            for table in tables
        }


def _data_root_paths() -> set[str]:
    from app.core.paths import build_paths

    root = build_paths().data_root
    if not root.exists():
        return set()
    return {str(path.relative_to(root)) for path in root.rglob("*")}


def _preview(client: TestClient, run_id: str):
    return client.post(
        "/workspaces/bluerev/bluecad/cad-link/047/preview",
        json={"source_simulation_run_id": run_id, "analysis_spec": None},
    )


def _execute(client: TestClient, run_id: str, preview_digest: str):
    return client.post(
        "/workspaces/bluerev/bluecad/cad-link/047/execute",
        json={
            "source_simulation_run_id": run_id,
            "analysis_spec": None,
            "preview_digest": preview_digest,
        },
    )


def test_preview_is_zero_write_and_reconciles_exact_047_proxy(client: TestClient) -> None:
    source = _successful_source_run(client)
    before_counts = _table_counts()
    before_paths = _data_root_paths()

    response = _preview(client, str(source["run_id"]))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["preview_digest"].startswith("sha256:")
    assert body["transformation_version"] == "bluerev_047_m0_tube_proxy_v0_1"
    assert body["source_simulation_run_id"] == source["run_id"]
    assert body["source_runner_job_id"] == source["runner_job_id"]
    assert body["source_input_payload_digest"].startswith("sha256:")
    assert body["source_output_payload_digest"].startswith("sha256:")
    assert body["geometry_spec_version"] == "bluecad_geometry_spec_v0_1"
    assert body["resolved_geometry_spec"] == {
        "spec_version": "bluecad_geometry_spec_v0_1",
        "name": "bluerev_047_m0_tube_proxy",
        "parts": [
            {
                "part_id": "illuminated_tube_proxy",
                "kind": "tube_run",
                "params": {"outer_d": 36.0, "wall_t": 3.0, "length": 20000.0},
            }
        ],
        "connections": [],
        "spec_id": body["resolved_spec_digest"],
    }
    assert body["transformed_values"] == {
        "length_mm": "20000",
        "outer_d_mm": "36",
        "wall_t_mm": "3",
    }
    assert all(check["passed"] for check in body["reconciliation"]["checks"])
    assert body["reconciliation"]["cad_values"]["solid_material_volume_mm3"] > 0
    assert set(body["source_snapshot"]) == {
        "tube_length",
        "tube_inner_diameter",
        "tube_outer_diameter",
    }
    assert all(item["status"] == "accepted" for item in body["source_snapshot"].values())
    assert all(item["name"].startswith("Canonical ") for item in body["source_snapshot"].values())
    assert _table_counts() == before_counts
    assert _data_root_paths() == before_paths


def test_execute_is_non_ai_idempotent_and_uses_honest_artifact_provenance(client: TestClient) -> None:
    source = _successful_source_run(client)
    preview = _preview(client, str(source["run_id"])).json()
    before_ai = _table_counts()["ai_jobs"]

    first = _execute(client, str(source["run_id"]), preview["preview_digest"])
    assert first.status_code == 200, first.text
    first_body = first.json()
    candidate = first_body["candidate"]
    assert first_body["replayed"] is False
    assert candidate["origin"] == "process_linked"
    assert candidate["status"] == "valid"
    assert candidate["parent_candidate_id"] is None
    assert candidate["loop_config_json"] == "{}"
    assert len(candidate["attempts"]) == 1
    attempt = candidate["attempts"][0]
    assert attempt["route_class"] == "deterministic:cad_link:047"
    assert attempt["proposal_outcome"] == "not_applicable"
    assert attempt["proposal_ai_job_id"] is None
    assert attempt["validation_verdict"] == "pass"

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        link = connection.execute(
            "SELECT * FROM bluecad_cad_links WHERE child_candidate_id = ?",
            (candidate["id"],),
        ).fetchone()
        assert link is not None
        assert link["preview_digest"] == preview["preview_digest"]
        artifact_ids = [
            candidate["spec_artifact_id"],
            candidate["report_artifact_id"],
            candidate["glb_artifact_id"],
            attempt["manifest_artifact_id"],
        ]
        rows = connection.execute(
            f"SELECT id, notes FROM artifacts WHERE id IN ({','.join('?' for _ in artifact_ids)})",
            artifact_ids,
        ).fetchall()
        assert len(rows) == len(artifact_ids)
        assert all("deterministic CAD-LINK-0" in row["notes"] for row in rows)
        assert all("AI loop" not in row["notes"] for row in rows)
        report_path = connection.execute(
            "SELECT stored_path FROM artifacts WHERE id = ?",
            (candidate["report_artifact_id"],),
        ).fetchone()["stored_path"]
        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
        solid_check = next(
            check for check in report["checks"]
            if check["id"] == "CAD_LINK_SOLID_VOLUME_RECONCILIATION"
        )
        assert solid_check["status"] == "pass"
        assert connection.execute("SELECT COUNT(*) AS count FROM ai_jobs").fetchone()["count"] == before_ai

    second = _execute(client, str(source["run_id"]), preview["preview_digest"])
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["replayed"] is True
    assert second_body["link_id"] == first_body["link_id"]
    assert second_body["candidate"]["id"] == candidate["id"]
    counts = _table_counts()
    assert counts["bluecad_candidates"] == 1
    assert counts["bluecad_attempts"] == 1
    assert counts["bluecad_cad_links"] == 1
    assert counts["ai_jobs"] == before_ai


def test_manual_or_changed_geometry_sources_fail_closed(client: TestClient) -> None:
    manual = _successful_source_run(client, manual_geometry={"tube_outer_diameter"})
    response = _preview(client, str(manual["run_id"]))
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "cad_link_parameter_binding_missing"
    assert _table_counts()["bluecad_candidates"] == 0

    source = _successful_source_run(client)
    parameter_id = source["parameter_ids"]["tube_length"]
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        connection.execute("UPDATE parameters SET value = '21' WHERE id = ?", (parameter_id,))
        connection.commit()
    changed = _preview(client, str(source["run_id"]))
    assert changed.status_code == 409
    assert changed.json()["detail"]["code"] == "cad_link_parameter_snapshot_mismatch"
    assert _table_counts()["bluecad_candidates"] == 0


def test_preview_digest_rejects_toctou_before_candidate_writes(client: TestClient) -> None:
    source = _successful_source_run(client)
    preview = _preview(client, str(source["run_id"])).json()
    parameter_id = source["parameter_ids"]["tube_inner_diameter"]
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        connection.execute("UPDATE parameters SET value = '31' WHERE id = ?", (parameter_id,))
        connection.commit()
    response = _execute(client, str(source["run_id"]), preview["preview_digest"])
    assert response.status_code == 409
    assert response.json()["detail"]["code"] in {
        "cad_link_parameter_snapshot_mismatch",
        "cad_link_preview_stale",
    }
    counts = _table_counts()
    assert counts["bluecad_candidates"] == 0
    assert counts["bluecad_attempts"] == 0
    assert counts["bluecad_cad_links"] == 0


def test_flowsheet_and_replacement_propagate_stale_through_process_link(client: TestClient) -> None:
    source = _successful_source_run(client)
    preview = _preview(client, str(source["run_id"])).json()
    executed = _execute(client, str(source["run_id"]), preview["preview_digest"])
    assert executed.status_code == 200, executed.text
    candidate = executed.json()["candidate"]
    attempt = candidate["attempts"][0]

    graph = client.get("/workspaces/bluerev/flowsheet/graph")
    assert graph.status_code == 200, graph.text
    edges = {
        (
            edge["upstream_ref"],
            edge["downstream_ref"],
            edge["relation"],
            edge["edge_class"],
        )
        for edge in graph.json()["edges"]
    }
    assert (
        f"simulation_run:{source['run_id']}",
        f"bluecad_candidate:{candidate['id']}",
        "m0_geometry_link",
        "dependency",
    ) in edges
    assert (
        f"bluecad_candidate:{candidate['id']}",
        f"bluecad_attempt:{attempt['id']}",
        "process_link_build",
        "dependency",
    ) in edges
    assert (
        f"bluecad_candidate:{candidate['id']}",
        f"artifact:{candidate['spec_artifact_id']}",
        "process_link_artifact",
        "dependency",
    ) in edges

    old_parameter = source["parameter_ids"]["tube_length"]
    replacement = _create_parameter(
        client,
        name="Corrected tube length",
        value="22",
        unit="m",
        status="proposed",
        supersedes_parameter_id=old_parameter,
    )
    promoted = client.post(f"/memory/parameter/{replacement}/promote-replacement")
    assert promoted.status_code == 200, promoted.text

    candidate_freshness = client.get(
        f"/workspaces/bluerev/flowsheet/nodes/bluecad_candidate:{candidate['id']}/freshness"
    )
    assert candidate_freshness.status_code == 200, candidate_freshness.text
    assert candidate_freshness.json()["state"] == "stale"
    assert candidate_freshness.json()["latest_invalidation"]["path"] == [
        f"parameter:{old_parameter}",
        f"simulation_run:{source['run_id']}",
        f"bluecad_candidate:{candidate['id']}",
    ]

    attempt_freshness = client.get(
        f"/workspaces/bluerev/flowsheet/nodes/bluecad_attempt:{attempt['id']}/freshness"
    )
    assert attempt_freshness.status_code == 200
    assert attempt_freshness.json()["state"] == "stale"
    assert attempt_freshness.json()["latest_invalidation"]["path"][-2:] == [
        f"bluecad_candidate:{candidate['id']}",
        f"bluecad_attempt:{attempt['id']}",
    ]

    artifact_freshness = client.get(
        f"/workspaces/bluerev/flowsheet/nodes/artifact:{candidate['spec_artifact_id']}/freshness"
    )
    assert artifact_freshness.status_code == 200
    assert artifact_freshness.json()["state"] == "stale"
    assert artifact_freshness.json()["latest_invalidation"]["path"][-2:] == [
        f"bluecad_candidate:{candidate['id']}",
        f"artifact:{candidate['spec_artifact_id']}",
    ]


def test_migration_and_registry_contract_are_live(client: TestClient) -> None:
    from app.core.database import get_current_schema_migration, open_sqlite_connection

    current = get_current_schema_migration()
    assert current.migration_id == "0015_cad_link_0"
    with open_sqlite_connection() as connection:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(bluecad_cad_links)")
        }
        assert {
            "source_simulation_run_id",
            "source_runner_job_id",
            "child_candidate_id",
            "preview_digest",
            "resolved_spec_digest",
            "reconciliation_digest",
        }.issubset(columns)

    status = Path(__file__).resolve().parents[2] / "docs/specs/STATUS.md"
    line = next(line for line in status.read_text(encoding="utf-8").splitlines() if line.startswith("| 052 |"))
    assert "| merged |" in line
    assert "/pull/170" in line
