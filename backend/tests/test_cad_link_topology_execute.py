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


def _preview(client: TestClient, simulation_run_id: str) -> dict[str, object]:
    response = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/preview",
        json={
            "source_simulation_run_id": simulation_run_id,
            "layout_spec": SUPPORT._layout(),
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
        "layout_spec": SUPPORT._layout(),
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
    simulation_run_id = SUPPORT._create_source_run(client)
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
    assert first_payload["candidate"]["status"] == "valid"
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
    simulation_run_id = SUPPORT._create_source_run(client)
    preview = _preview(client, simulation_run_id)
    request = _execute_request(simulation_run_id, str(preview["preview_digest"]))
    before_counts = _execution_counts()
    before_files = _data_files()

    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE parameters SET value = '3' WHERE id = 'geometry-count-shared'"
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
    simulation_run_id = SUPPORT._create_source_run(client)
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
