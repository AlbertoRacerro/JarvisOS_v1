from __future__ import annotations

import importlib.util
import json
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from app.core.database import open_sqlite_connection
from app.core.paths import build_paths


def _load_preview_support() -> ModuleType:
    path = Path(__file__).with_name("test_cad_link_topology_preview.py")
    spec = importlib.util.spec_from_file_location("cad_link_074_preview_support", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUPPORT = _load_preview_support()


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-cad-link-072-execute")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _use_in_process_kernel(monkeypatch) -> None:
    import app.modules.bluecad.cad_link_topology as topology
    from app.modules.bluecad.cad_link_topology_preflight import (
        _build_preflight_evidence,
    )

    monkeypatch.setattr(topology, "run_kernel_preflight", _build_preflight_evidence)


def _golden_layout() -> dict[str, object]:
    manifold = {
        "branch_gap_mm": 20.0,
        "end_gap_mm": 20.0,
        "branch_stub_length_mm": 80.0,
        "cap_thickness_mm": 8.0,
    }
    return {
        "schema_version": "bluerev_cad_layout_m1_v0_1",
        "layout_kind": "planar_mirrored_parallel_headers",
        "plane": "xy",
        "boundary_policy": "open_common_supply_and_return",
        "split_manifold": dict(manifold),
        "merge_manifold": dict(manifold),
        "branch_route": {
            "steps": [
                {
                    "kind": "straight",
                    "length_mm": 500.0,
                    "illumination": "illuminated",
                }
            ]
        },
    }


def _create_golden_source_run(client: TestClient) -> str:
    from app.modules.bluecad.cad_link_topology import GEOMETRY_PARAMETER_INPUTS
    from app.modules.bluecad.capped_manifold import build_capped_manifold_kernel
    from app.modules.events.service import utc_now

    payload = SUPPORT._input_payload()
    values = {
        "parallel_path_count": 2,
        "branch_illuminated_straight_length": 0.5,
        "branch_dark_straight_length": 0.0,
        "branch_bend_count": 0,
        "branch_illuminated_bend_count": 0,
        "branch_bend_centerline_radius": 0.0,
        "branch_bend_angle": 0.0,
        "branch_bend_loss_coefficient_per_bend": 0.0,
        "common_supply_length": 0.0,
        "common_return_length": 0.0,
        "branch_tube_inner_diameter": 50.0,
        "branch_tube_outer_diameter": 60.0,
        "common_tube_inner_diameter": 80.0,
        "common_tube_outer_diameter": 90.0,
    }
    for name, value in values.items():
        payload[name]["value"] = value

    manifold_part = {
        "part_id": "golden_manifold",
        "kind": "capped_manifold",
        "params": {
            "main_outer_d": 90.0,
            "main_wall_t": 5.0,
            "branch_count": 2,
            "branch_outer_d": 60.0,
            "branch_wall_t": 5.0,
            "branch_gap": 20.0,
            "end_gap": 20.0,
            "branch_stub_length": 80.0,
            "cap_thickness": 8.0,
        },
    }
    cavity_liters = (
        float(build_capped_manifold_kernel(manifold_part).void_shape.volume) / 1_000_000.0
    )
    payload["split_manifold_liquid_volume"]["value"] = cavity_liters
    payload["merge_manifold_liquid_volume"]["value"] = cavity_liters

    now = utc_now()
    with open_sqlite_connection() as connection:
        for name in GEOMETRY_PARAMETER_INPUTS:
            item = payload[name]
            parameter_id = f"golden-{name}"
            item["source_parameter_id"] = parameter_id
            connection.execute(
                """
                INSERT INTO parameters (
                    id, workspace_id, name, value, unit, value_status, status,
                    created_at, updated_at, origin, source_ref
                ) VALUES (?, 'bluerev', ?, ?, ?, 'known', 'accepted', ?, ?, 'manual', ?)
                """,
                (
                    parameter_id,
                    f"Golden {name}",
                    str(item["value"]),
                    str(item["unit"]),
                    now,
                    now,
                    f"test:golden:{name}",
                ),
            )
        connection.commit()

    registered = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-process-topology-m1-v0/register"
    )
    assert registered.status_code == 200, registered.text
    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": registered.json()["id"], "input_set": payload},
    )
    assert created.status_code == 201, created.text
    runner_job_id = created.json()["runner_job"]["id"]
    executed = client.post(f"/runner-jobs/{runner_job_id}/run")
    assert executed.status_code == 200, executed.text
    assert executed.json()["runner_job"]["status"] == "succeeded", executed.text
    return executed.json()["simulation_run"]["id"]


def _preview(client: TestClient, simulation_run_id: str) -> dict[str, object]:
    response = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/preview",
        json={
            "source_simulation_run_id": simulation_run_id,
            "layout_spec": _golden_layout(),
            "analysis_spec": None,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _execute_request(
    simulation_run_id: str,
    preview_digest: str,
) -> dict[str, object]:
    return {
        "source_simulation_run_id": simulation_run_id,
        "layout_spec": _golden_layout(),
        "analysis_spec": None,
        "preview_digest": preview_digest,
    }


def _execution_counts() -> dict[str, int]:
    with open_sqlite_connection() as connection:
        return {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in (
                "bluecad_candidates",
                "bluecad_attempts",
                "bluecad_cad_links",
                "artifacts",
                "evidence_records",
                "ai_jobs",
            )
        }


def _data_files() -> list[Path]:
    root = build_paths().data_root
    return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())


def test_execute_creates_one_non_ai_link_and_replays_idempotently(
    client: TestClient,
    monkeypatch,
) -> None:
    _use_in_process_kernel(monkeypatch)
    simulation_run_id = _create_golden_source_run(client)
    preview = _preview(client, simulation_run_id)
    request = _execute_request(simulation_run_id, str(preview["preview_digest"]))
    before_ai = _execution_counts()["ai_jobs"]

    first = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/execute",
        json=request,
    )
    assert first.status_code == 200, first.text
    first_payload = first.json()
    assert first_payload["replayed"] is False
    assert first_payload["candidate"]["origin"] == "process_linked"
    with open_sqlite_connection() as connection:
        report_row = connection.execute(
            """
            SELECT a.stored_path
            FROM bluecad_candidates c
            LEFT JOIN artifacts a ON a.id = c.report_artifact_id
            WHERE c.id = ?
            """,
            (first_payload["candidate"]["id"],),
        ).fetchone()
    report_payload = (
        None
        if report_row is None or report_row["stored_path"] is None
        else json.loads(Path(report_row["stored_path"]).read_text(encoding="utf-8"))
    )
    assert first_payload["candidate"]["status"] == "valid", report_payload
    assert "not represented: pump, reservoir vessel" in first_payload["candidate"][
        "notes"
    ]

    counts_after_first = _execution_counts()
    assert counts_after_first["bluecad_candidates"] == 1
    assert counts_after_first["bluecad_attempts"] == 1
    assert counts_after_first["bluecad_cad_links"] == 1
    assert counts_after_first["evidence_records"] >= 1
    assert counts_after_first["ai_jobs"] == before_ai

    with open_sqlite_connection() as connection:
        attempt = connection.execute("SELECT * FROM bluecad_attempts").fetchone()
        link = connection.execute("SELECT * FROM bluecad_cad_links").fetchone()
        assert attempt is not None and link is not None
        assert attempt["route_class"] == "deterministic:cad_link:072"
        assert attempt["proposal_ai_job_id"] is None
        assert attempt["proposal_outcome"] == "not_applicable"
        assert link["preview_digest"] == preview["preview_digest"]
        reconciliation = json.loads(link["reconciliation_json"])
        assert reconciliation["schema_version"] == "cad_link_072_link_evidence_v0_1"
        assert reconciliation["external_boundaries"] == preview["external_boundaries"]
        assert reconciliation["component_inventory"] == preview["component_inventory"]
        assert all(check["passed"] for check in reconciliation["checks"])

    from app.modules.flowsheet.service import get_flowsheet_graph

    graph = get_flowsheet_graph("bluerev")
    lineage_edges = [
        edge
        for edge in graph.edges
        if edge.upstream_ref == f"simulation_run:{simulation_run_id}"
        and edge.downstream_ref
        == f"bluecad_candidate:{first_payload['candidate']['id']}"
    ]
    assert len(lineage_edges) == 1
    assert lineage_edges[0].relation == "m1_topology_geometry_link"
    assert lineage_edges[0].edge_class == "dependency"

    second = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/execute",
        json=request,
    )
    assert second.status_code == 200, second.text
    second_payload = second.json()
    assert second_payload["replayed"] is True
    assert second_payload["link_id"] == first_payload["link_id"]
    assert second_payload["candidate"]["id"] == first_payload["candidate"]["id"]
    assert _execution_counts() == counts_after_first

    with open_sqlite_connection() as connection:
        connection.execute("UPDATE bluecad_cad_links SET reconciliation_json = '{}' ")
        connection.commit()
    tampered = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/execute",
        json=request,
    )
    assert tampered.status_code == 409, tampered.text
    assert tampered.json()["detail"]["code"] == "cad_link_persistence_inconsistent"


def test_execute_stale_parameter_has_zero_writes_and_zero_files(
    client: TestClient,
    monkeypatch,
) -> None:
    _use_in_process_kernel(monkeypatch)
    simulation_run_id = _create_golden_source_run(client)
    preview = _preview(client, simulation_run_id)
    request = _execute_request(simulation_run_id, str(preview["preview_digest"]))
    before_counts = _execution_counts()
    before_files = _data_files()

    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE parameters SET value = '3' WHERE id = 'golden-parallel_path_count'"
        )
        connection.commit()

    response = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/execute",
        json=request,
    )
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "cad_link_preview_stale"
    assert _execution_counts() == before_counts
    assert _data_files() == before_files


def test_execute_build_failure_parks_inspectable_candidate_without_ai(
    client: TestClient,
    monkeypatch,
) -> None:
    _use_in_process_kernel(monkeypatch)
    simulation_run_id = _create_golden_source_run(client)
    preview = _preview(client, simulation_run_id)
    request = _execute_request(simulation_run_id, str(preview["preview_digest"]))

    import app.modules.bluecad.cad_link_topology_execute as execute_module

    def fail_build(*_args, **_kwargs):
        raise RuntimeError("forced deterministic build failure")

    monkeypatch.setattr(execute_module, "build_geometry_spec", fail_build)
    response = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/execute",
        json=request,
    )
    assert response.status_code == 500, response.text
    assert response.json()["detail"]["code"] == "cad_link_persistence_failed"

    with open_sqlite_connection() as connection:
        candidate = connection.execute("SELECT * FROM bluecad_candidates").fetchone()
        attempt = connection.execute("SELECT * FROM bluecad_attempts").fetchone()
        link = connection.execute("SELECT * FROM bluecad_cad_links").fetchone()
        assert candidate is not None and attempt is not None and link is not None
        assert candidate["status"] == "parked"
        assert candidate["parked_reason"] == "cad_link_failed"
        assert attempt["route_class"] == "deterministic:cad_link:072"
        assert attempt["proposal_ai_job_id"] is None
        assert attempt["build_outcome"] == "cad_link_execution_error"
        assert connection.execute("SELECT COUNT(*) FROM ai_jobs").fetchone()[0] == 0
        candidate_id = str(candidate["id"])

    assert not (
        build_paths().workspaces_dir
        / "bluerev"
        / "bluecad"
        / candidate_id
        / "attempt_01"
    ).exists()



def test_replay_waits_for_generating_candidate(client: TestClient, monkeypatch) -> None:
    import threading
    import time
    from uuid import uuid4

    import app.modules.bluecad.cad_link_topology_execute as execute_module
    from app.modules.events.service import utc_now

    candidate_id = str(uuid4())
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO bluecad_candidates (
                id, workspace_id, brief_text, brief_digest, status,
                parked_reason, spec_artifact_id, glb_artifact_id,
                report_artifact_id, promoted_decision_id, origin,
                parent_candidate_id, loop_config_json, created_at,
                updated_at, notes
            ) VALUES (?, 'bluerev', 'concurrency probe', ?, 'generating',
                NULL, NULL, NULL, NULL, NULL, 'process_linked', NULL,
                '{}', ?, ?, 'concurrency probe')
            """,
            (candidate_id, "sha256:" + "1" * 64, now, now),
        )
        connection.commit()

    monkeypatch.setattr(execute_module, "_REPLAY_WAIT_SECONDS", 1.0)
    monkeypatch.setattr(execute_module, "_REPLAY_POLL_SECONDS", 0.01)

    def complete_candidate() -> None:
        time.sleep(0.1)
        with open_sqlite_connection() as connection:
            connection.execute(
                "UPDATE bluecad_candidates SET status = 'valid', updated_at = ? WHERE id = ?",
                (utc_now(), candidate_id),
            )
            connection.commit()

    worker = threading.Thread(target=complete_candidate)
    worker.start()
    started = time.monotonic()
    candidate = execute_module._wait_for_replay_candidate("bluerev", candidate_id)
    elapsed = time.monotonic() - started
    worker.join()

    assert candidate.id == candidate_id
    assert candidate.status == "valid"
    assert elapsed >= 0.08
