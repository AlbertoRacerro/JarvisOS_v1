from __future__ import annotations

import importlib.util
import json
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.database import open_sqlite_connection
from app.modules.events.service import utc_now


def _load_execute_support() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "test_cad_link_topology_execute.py"
    spec = importlib.util.spec_from_file_location("cad_link_074_execute_support", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUPPORT = _load_execute_support()


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-cad-link-074-failure-cleanup")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _analysis_spec(timeout_s: float) -> dict[str, Any]:
    return {
        "schema_version": "bluecad_analysis_spec_v0_1",
        "analysis_id": "cad-link-timeout-probe",
        "analysis_type": "static",
        "material": {
            "name": "Steel",
            "E": 210e9,
            "nu": 0.3,
            "rho": 7850.0,
            "yield_strength": 250e6,
        },
        "bcs": [{"port_label": "part.fixed", "kind": "fixed"}],
        "loads": [
            {
                "port_label": "part.loaded",
                "type": "force_total",
                "force": [1.0, 0.0, 0.0],
            }
        ],
        "mesh": {"target_size": 10.0, "element_order": 1},
        "pass_criteria": [],
        "timeout_s": timeout_s,
    }


def test_shared_analysis_timeout_contract_remains_unchanged() -> None:
    from app.modules.bluecad.models import BluecadLoopConfig

    assert BluecadLoopConfig(analysis_spec=_analysis_spec(301.0)).analysis_spec is not None


def test_cad_link_analysis_timeout_has_a_separate_lifecycle_bound() -> None:
    from app.modules.bluecad.cad_link_topology import CadLink072PreviewRequest

    request = CadLink072PreviewRequest(
        source_simulation_run_id="run-timeout-probe",
        layout_spec={},
        analysis_spec=_analysis_spec(300.0),
    )
    assert request.analysis_spec is not None
    with pytest.raises(ValidationError):
        CadLink072PreviewRequest(
            source_simulation_run_id="run-timeout-probe",
            layout_spec={},
            analysis_spec=_analysis_spec(300.0001),
        )


def test_running_analysis_is_failed_before_candidate_parking(client: TestClient) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    attempt_id = str(uuid4())
    run_id = str(uuid4())
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO simulation_runs (
                id, workspace_id, model_version_id, run_label, status,
                input_payload, parameter_payload, output_payload,
                started_at, completed_at, created_at, notes
            ) VALUES (?, 'bluerev', NULL, ?, 'running', '{}', '{}', NULL,
                ?, NULL, ?, 'Spec 074 completion-failure probe.')
            """,
            (run_id, f"bluecad_attempt_{attempt_id}", now, now),
        )
        connection.commit()

    with pytest.raises(RuntimeError, match="exactly one terminal run"):
        execute_module._require_terminal_analysis_stage(
            "bluerev",
            "candidate-completion-probe",
            attempt_id,
            {"schema_version": "probe"},
        )

    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT status, output_payload, completed_at FROM simulation_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
    assert row is not None
    assert row["status"] == "failed"
    assert row["completed_at"] is not None
    assert json.loads(row["output_payload"])["error"]["code"] == (
        "cad_link_analysis_completion_persistence_failed"
    )


def test_heartbeat_start_failure_parks_reserved_candidate(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    SUPPORT._use_in_process_kernel(monkeypatch)
    simulation_run_id = SUPPORT._create_golden_source_run(client)
    preview = SUPPORT._preview(client, simulation_run_id)
    request = SUPPORT._execute_request(
        simulation_run_id,
        str(preview["preview_digest"]),
    )

    import app.modules.bluecad.cad_link_topology_execute as execute_module

    def fail_heartbeat(*_args: Any, **_kwargs: Any):
        raise RuntimeError("forced heartbeat startup failure")

    monkeypatch.setattr(
        execute_module,
        "_start_reservation_heartbeat",
        fail_heartbeat,
    )
    response = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/execute",
        json=request,
    )

    assert response.status_code == 500, response.text
    assert response.json()["detail"]["code"] == "cad_link_persistence_failed"
    with open_sqlite_connection() as connection:
        candidate = connection.execute("SELECT * FROM bluecad_candidates").fetchone()
        attempt = connection.execute("SELECT * FROM bluecad_attempts").fetchone()
    assert candidate is not None and attempt is not None
    assert candidate["status"] == "parked"
    assert candidate["parked_reason"] == "cad_link_failed"
    assert attempt["build_outcome"] == "cad_link_execution_error"
    assert attempt["finished_at"] is not None


# Regression: a parking persistence error must never leave a live reservation heartbeat.
def test_parking_failure_still_stops_reservation_heartbeat(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    SUPPORT._use_in_process_kernel(monkeypatch)
    simulation_run_id = SUPPORT._create_golden_source_run(client)
    preview = SUPPORT._preview(client, simulation_run_id)
    request = SUPPORT._execute_request(
        simulation_run_id,
        str(preview["preview_digest"]),
    )

    import app.modules.bluecad.cad_link_topology_execute as execute_module

    stop_marker = object()
    thread_marker = object()
    stopped: list[tuple[object, object]] = []

    monkeypatch.setattr(
        execute_module,
        "_start_reservation_heartbeat",
        lambda *_args, **_kwargs: (stop_marker, thread_marker),
    )

    def fail_build(*_args: Any, **_kwargs: Any):
        raise RuntimeError("forced build failure before parking")

    def fail_park(*_args: Any, **_kwargs: Any):
        raise RuntimeError("forced parking failure")

    monkeypatch.setattr(execute_module, "build_geometry_spec", fail_build)
    monkeypatch.setattr(execute_module, "park_candidate", fail_park)
    monkeypatch.setattr(
        execute_module,
        "_stop_reservation_heartbeat",
        lambda stop, thread: stopped.append((stop, thread)),
    )

    response = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/execute",
        json=request,
    )

    assert response.status_code == 500, response.text
    assert response.json()["detail"]["code"] == "cad_link_persistence_failed"
    assert stopped == [(stop_marker, thread_marker)]
