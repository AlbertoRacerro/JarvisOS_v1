from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.database import open_sqlite_connection
from app.modules.ai.execution import ProviderBinding
from app.modules.bluecad.export import sha256_file


def analysis_spec() -> dict[str, Any]:
    return {
        "schema_version": "bluecad_analysis_spec_v0_1",
        "analysis_id": "alpha-real-tools",
        "analysis_type": "static",
        "material": {"name": "steel", "E": 200000.0, "nu": 0.3, "rho": 7.8e-9, "yield_strength": 250.0},
        "bcs": [{"port_label": "tube1.port_a", "kind": "fixed"}],
        "loads": [{"port_label": "tube1.port_b", "type": "force_total", "force": [100.0, 0.0, 0.0]}],
        "mesh": {"target_size": 25.0},
        "pass_criteria": [
            {"metric": "max_displacement", "op": "<=", "value": 100.0},
            {"metric": "max_von_mises", "op": "<=", "value": 1_000_000.0},
        ],
        "timeout_s": 120.0,
    }


def offline_bindings() -> dict[str, ProviderBinding]:
    return {
        route: ProviderBinding(route, "scaleway", "scripted-alpha-proof", False, 4000)
        for route in ("external:cheap", "external:reasoning")
    }


def _artifact_rows(candidate_id: str) -> list[dict[str, Any]]:
    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT filename, stored_path, artifact_type, sha256 FROM artifacts WHERE source_ref LIKE ? ORDER BY created_at, id",
            (f"bluecad_candidate:{candidate_id}:%",),
        ).fetchall()
    return [dict(row) for row in rows]


def _evidence_rows(candidate_id: str) -> list[dict[str, Any]]:
    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT kind, verdict, candidate_id, attempt_id, source_run_id, report_artifact_id FROM evidence_records WHERE candidate_id = ? ORDER BY created_at, id",
            (candidate_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _simulation_row(candidate_id: str) -> dict[str, Any]:
    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT status, input_payload, output_payload FROM simulation_runs ORDER BY created_at, id"
        ).fetchall()
    for row in rows:
        if json.loads(row["input_payload"] or "{}").get("candidate_id") == candidate_id:
            return dict(row)
    raise AssertionError(f"simulation run missing for candidate {candidate_id}")


def assert_full_chain(candidate: Any) -> Path:
    assert candidate.status == "valid"
    assert len(candidate.attempts) == 1
    attempt = candidate.attempts[0]
    assert (attempt.proposal_outcome, attempt.build_outcome, attempt.validation_verdict) == ("ok", "ok", "pass")

    evidence = _evidence_rows(candidate.id)
    assert [(row["kind"], row["verdict"]) for row in evidence] == [
        ("validation_v0", "pass"),
        ("mesh_quality_v0", "pass"),
        ("fem_static_v0", "pass"),
    ]
    assert all(row["candidate_id"] == candidate.id and row["attempt_id"] == attempt.id for row in evidence)
    assert all(row["source_run_id"] and row["report_artifact_id"] for row in evidence[1:])

    simulation = _simulation_row(candidate.id)
    assert simulation["status"] == "completed"
    assert json.loads(simulation["output_payload"]) == {
        "status": "completed",
        "mesh_verdict": "pass",
        "fem_verdict": "pass",
    }

    artifacts = _artifact_rows(candidate.id)
    roles = [row["artifact_type"] for row in artifacts]
    for role, expected in {
        "bluecad_spec": 1,
        "bluecad_report": 1,
        "bluecad_manifest": 1,
        "bluecad_glb": 1,
        "bluecad_sim_report": 2,
    }.items():
        assert roles.count(role) == expected
    for row in artifacts:
        path = Path(row["stored_path"])
        assert path.is_file() and path.stat().st_size > 0
        assert sha256_file(path) == row["sha256"]

    reports = {
        row["filename"]: json.loads(Path(row["stored_path"]).read_text(encoding="utf-8"))
        for row in artifacts
        if row["artifact_type"] == "bluecad_sim_report"
    }
    mesh = reports["mesh_result.json"]
    fem = reports["fem_result.json"]["result_summary"]
    assert mesh["attempts"][0]["gmsh_returncode"] == 0
    counts = mesh["attempts"][0]["counts"]
    assert counts["nodes_total"] > 0 and counts["elements_total"] > 0
    assert all(count > 0 for count in counts["physical_groups"].values())
    assert fem["solver"]["returncode"] == 0
    assert not str(fem["solver"]["version"]).lower().startswith("fake")
    for metric in ("max_displacement", "max_von_mises"):
        value = float(fem[metric]["value"])
        assert 0.0 <= value < float("inf")

    return Path(next(row["stored_path"] for row in artifacts if row["artifact_type"] == "bluecad_manifest"))
