from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.database import open_sqlite_connection
from app.modules.bluecad.cad_link_topology import GEOMETRY_PARAMETER_INPUTS
from app.modules.events.service import utc_now


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _input_payload() -> dict[str, object]:
    fixture = Path(__file__).parent / "fixtures" / "bluerev_process_topology_m1_valid.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


def _layout() -> dict[str, object]:
    manifold = {
        "branch_gap_mm": 25.0,
        "end_gap_mm": 15.0,
        "branch_stub_length_mm": 20.0,
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
                    "length_mm": 10000.0,
                    "illumination": "illuminated",
                },
                {"kind": "bend", "turn": "left", "illumination": "illuminated"},
                {
                    "kind": "straight",
                    "length_mm": 2000.0,
                    "illumination": "dark",
                },
                {"kind": "bend", "turn": "right", "illumination": "dark"},
            ]
        },
    }


def _create_source_run(client: TestClient) -> str:
    payload = _input_payload()
    now = utc_now()
    shared_count_id = "geometry-count-shared"
    with open_sqlite_connection() as connection:
        for name in GEOMETRY_PARAMETER_INPUTS:
            item = payload[name]
            parameter_id = (
                shared_count_id if name in {"parallel_path_count", "branch_bend_count"} else f"geometry-{name}"
            )
            item["source_parameter_id"] = parameter_id
            connection.execute(
                """
                INSERT OR IGNORE INTO parameters (
                    id, workspace_id, name, value, unit, value_status, status,
                    created_at, updated_at, origin, source_ref
                ) VALUES (?, 'bluerev', ?, ?, ?, 'known', 'accepted', ?, ?, 'manual', ?)
                """,
                (
                    parameter_id,
                    f"Source {name}",
                    str(item["value"]),
                    str(item["unit"]),
                    now,
                    now,
                    f"test:{name}",
                ),
            )
        connection.commit()

    registered = client.post("/workspaces/bluerev/bundled-models/bluerev-process-topology-m1-v0/register")
    assert registered.status_code == 200, registered.text
    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": registered.json()["id"], "input_set": payload},
    )
    assert created.status_code == 201, created.text
    runner_job_id = created.json()["runner_job"]["id"]
    executed = client.post(f"/runner-jobs/{runner_job_id}/run")
    assert executed.status_code == 200, executed.text
    assert executed.json()["runner_job"]["status"] == "succeeded"
    return executed.json()["simulation_run"]["id"]


def _table_counts() -> dict[str, int]:
    tables = (
        "bluecad_candidates",
        "bluecad_attempts",
        "artifacts",
        "events",
        "evidence_records",
        "freshness_marks",
        "bluecad_cad_links",
        "ai_jobs",
    )
    with open_sqlite_connection() as connection:
        return {
            table: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
            for table in tables
        }


def _fake_preflight(spec, boundaries):
    part_map = {part["part_id"]: part for part in spec["parts"]}

    def manifold_evidence(part_id: str) -> dict[str, object]:
        params = part_map[part_id]["params"]
        branch_count = int(params["branch_count"])
        pitch = float(params["branch_outer_d"]) + float(params["branch_gap"])
        end_gap = float(params["end_gap"])
        branch_outer = float(params["branch_outer_d"])
        branch_stub = float(params["branch_stub_length"])
        main_outer = float(params["main_outer_d"])
        sweep = main_outer / 2.0 + branch_stub
        ports: dict[str, object] = {
            "common": {
                "origin": [0.0, 0.0, 0.0],
                "direction": [-1.0, 0.0, 0.0],
                "interface": "tube",
                "outer_d": main_outer,
                "wall_t": float(params["main_wall_t"]),
            }
        }
        for index in range(branch_count):
            ports[f"branch_{index + 1}"] = {
                "origin": [
                    end_gap + branch_outer / 2.0 + pitch * index,
                    sweep,
                    0.0,
                ],
                "direction": [0.0, 1.0, 0.0],
                "interface": "tube",
                "outer_d": branch_outer,
                "wall_t": float(params["branch_wall_t"]),
            }
        return {
            "frame": {
                "rotation_z_rad": 0.0,
                "translation_mm": [0.0, 0.0, 0.0],
            },
            "bbox_mm": {
                "min": [0.0, -main_outer / 2.0, -main_outer / 2.0],
                "max": [1.0, sweep, main_outer / 2.0],
            },
            "material_volume_mm3": 1.0,
            "ports": ports,
        }

    placed_parts = {
        "split_manifold": manifold_evidence("split_manifold"),
        "merge_manifold": manifold_evidence("merge_manifold"),
    }
    return {
        "worker_timeout_seconds": 30.0,
        "spawn_isolated": True,
        "part_count": len(spec["parts"]),
        "connection_count": len(spec["connections"]),
        "external_boundaries": boundaries,
        "open_endpoints": sorted(boundaries.values()),
        "kernel_checks": {},
        "manifold_cavities": {
            "split_manifold": {"volume_mm3": 5_000_000.0, "brep_valid": True},
            "merge_manifold": {"volume_mm3": 5_000_000.0, "brep_valid": True},
        },
        "assembly_material_volume_mm3": 2.0,
        "assembly_bbox_mm": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 1.0]},
        "placed_parts": placed_parts,
        "contact_pairs": [],
        "pair_evaluation": {
            "total_pair_count": 66,
            "broad_phase_candidate_count": 12,
            "broad_phase_skipped_count": 54,
            "evaluated_pair_count": 12,
            "zero_contact_candidate_count": 0,
        },
        "positive_interference_tolerance_mm3": 1e-6,
    }


def test_preview_is_deterministic_allows_compatible_parameter_reuse_and_writes_nothing(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.paths import build_paths
    from app.modules.bluecad import cad_link_topology

    simulation_run_id = _create_source_run(client)
    monkeypatch.setattr(cad_link_topology, "run_kernel_preflight", _fake_preflight)
    request = {
        "source_simulation_run_id": simulation_run_id,
        "layout_spec": _layout(),
        "analysis_spec": None,
    }
    before_counts = _table_counts()
    data_root = build_paths().data_root
    before_files = sorted(path.relative_to(data_root) for path in data_root.rglob("*") if path.is_file())

    first = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/preview",
        json=request,
    )
    second = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/preview",
        json=request,
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["preview_digest"] == second.json()["preview_digest"]
    assert first.json()["source_snapshot_digest"] == second.json()["source_snapshot_digest"]
    snapshots = first.json()["source_geometry_parameters"]
    assert snapshots["parallel_path_count"]["parameter_id"] == "geometry-count-shared"
    assert snapshots["branch_bend_count"]["parameter_id"] == "geometry-count-shared"
    manifest_snapshot = first.json()["source_snapshot"]["topology_manifest_payload"]
    executed_inputs = manifest_snapshot["executed_inputs"]
    assert executed_inputs["reservoir_liquid_volume"] == _input_payload()["reservoir_liquid_volume"]
    assert set(executed_inputs) > set(GEOMETRY_PARAMETER_INPUTS)
    assert first.json()["resolved_part_count"] == 12
    assert first.json()["resolved_connection_count"] == 12
    assert all(check["passed"] for check in first.json()["reconciliation"]["checks"])
    assert _table_counts() == before_counts
    after_files = sorted(path.relative_to(data_root) for path in data_root.rglob("*") if path.is_file())
    assert after_files == before_files


def test_transactional_recheck_reuses_fresh_kernel_evidence_without_kernel_work(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.bluecad import cad_link_topology

    simulation_run_id = _create_source_run(client)
    request = cad_link_topology.CadLink072PreviewRequest(
        source_simulation_run_id=simulation_run_id,
        layout_spec=_layout(),
        analysis_spec=None,
    )
    monkeypatch.setattr(cad_link_topology, "run_kernel_preflight", _fake_preflight)
    initial = cad_link_topology.preview_cad_link_072("bluerev", request)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("kernel preflight must run outside the SQLite writer lock")

    monkeypatch.setattr(cad_link_topology, "run_kernel_preflight", fail_if_called)
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            current = cad_link_topology._rebuild_preview_without_kernel(
                connection,
                "bluerev",
                request,
                initial["kernel_preflight"],
            )
        finally:
            connection.rollback()

    assert current["preview_digest"] == initial["preview_digest"]
    assert current["kernel_preflight_digest"] == initial["kernel_preflight_digest"]


def _preview_request(simulation_run_id: str) -> dict[str, object]:
    return {
        "source_simulation_run_id": simulation_run_id,
        "layout_spec": _layout(),
        "analysis_spec": None,
    }


def test_source_authority_rejects_tampered_script_artifact_bytes(
    client: TestClient,
) -> None:
    simulation_run_id = _create_source_run(client)
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT mv.implementation_artifact_id
            FROM simulation_runs sr
            JOIN model_versions mv ON mv.id = sr.model_version_id
            WHERE sr.id = ? AND sr.workspace_id = 'bluerev'
            """,
            (simulation_run_id,),
        ).fetchone()
        assert row is not None
        tampered_path = Path(
            connection.execute(
                "SELECT stored_path FROM artifacts WHERE id = ?",
                (row["implementation_artifact_id"],),
            ).fetchone()["stored_path"]
        ).with_name("tampered-topology-script.py")
        tampered_path.write_text("print('tampered')\n", encoding="utf-8")
        connection.execute(
            "UPDATE artifacts SET stored_path = ? WHERE id = ?",
            (str(tampered_path), row["implementation_artifact_id"]),
        )
        connection.commit()

    response = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/preview",
        json=_preview_request(simulation_run_id),
    )
    assert response.status_code == 422, response.text
    assert response.json()["detail"]["code"] == "cad_link_model_identity_mismatch"


def test_source_authority_missing_expected_manifest_path_fails_closed(
    client: TestClient,
) -> None:
    simulation_run_id = _create_source_run(client)
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT a.id AS artifact_id, a.stored_path
            FROM run_artifacts ra
            JOIN artifacts a ON a.id = ra.artifact_id
            WHERE ra.workspace_id = 'bluerev'
              AND ra.simulation_run_id = ?
              AND ra.role = 'bluerev_topology_manifest'
            """,
            (simulation_run_id,),
        ).fetchone()
        assert row is not None
        original = Path(row["stored_path"])
        moved = original.parent.parent / "moved-topology-manifest.json"
        original.rename(moved)
        connection.execute(
            "UPDATE artifacts SET stored_path = ? WHERE id = ?",
            (str(moved), row["artifact_id"]),
        )
        connection.commit()

    response = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/preview",
        json=_preview_request(simulation_run_id),
    )
    assert response.status_code == 422, response.text
    assert response.json()["detail"]["code"] == "cad_link_topology_manifest_invalid"


def test_manifest_geometry_agreement_rejects_semantic_drift() -> None:
    import math

    from app.modules.bluecad.cad_link import CadLinkError
    from app.modules.bluecad.cad_link_topology_source import (
        _validate_manifest_geometry_agreement,
    )

    inputs = _input_payload()
    n = int(inputs["parallel_path_count"]["value"])
    bend_count = int(inputs["branch_bend_count"]["value"])
    illuminated_bends = int(inputs["branch_illuminated_bend_count"]["value"])
    dark_bends = bend_count - illuminated_bends
    li = float(inputs["branch_illuminated_straight_length"]["value"])
    ld = float(inputs["branch_dark_straight_length"]["value"])
    rb = float(inputs["branch_bend_centerline_radius"]["value"]) / 1000.0
    angle = float(inputs["branch_bend_angle"]["value"])
    arc = rb * math.radians(angle)
    bend_total = bend_count * arc
    branch_length = li + ld + bend_total
    supply = float(inputs["common_supply_length"]["value"])
    ret = float(inputs["common_return_length"]["value"])
    branch_inner = float(inputs["branch_tube_inner_diameter"]["value"]) / 1000.0
    branch_outer = float(inputs["branch_tube_outer_diameter"]["value"]) / 1000.0
    common_inner = float(inputs["common_tube_inner_diameter"]["value"]) / 1000.0
    common_outer = float(inputs["common_tube_outer_diameter"]["value"]) / 1000.0
    branch_wall = (branch_outer - branch_inner) / 2.0
    common_wall = (common_outer - common_inner) / 2.0
    branch_volume = n * math.pi * branch_inner**2 / 4.0 * branch_length
    supply_volume = math.pi * common_inner**2 / 4.0 * supply
    return_volume = math.pi * common_inner**2 / 4.0 * ret
    manifold_volume = (
        float(inputs["split_manifold_liquid_volume"]["value"]) + float(inputs["merge_manifold_liquid_volume"]["value"])
    ) / 1000.0
    reservoir_volume = float(inputs["reservoir_liquid_volume"]["value"]) / 1000.0
    illuminated_area = n * math.pi * branch_outer * (li + illuminated_bends * arc)
    dark_area = n * math.pi * branch_outer * (ld + dark_bends * arc)
    common_area = math.pi * common_outer * (supply + ret)
    material_volume = n * math.pi * (branch_outer**2 - branch_inner**2) / 4.0 * branch_length + math.pi * (
        common_outer**2 - common_inner**2
    ) / 4.0 * (supply + ret)
    manifest = {
        "executed_inputs": inputs,
        "symmetry": {"parallel_path_count": n},
        "branch_template": {
            "illuminated_straight": {
                "length_m": li,
                "inner_diameter_m": branch_inner,
                "outer_diameter_m": branch_outer,
                "wall_thickness_m": branch_wall,
            },
            "dark_straight": {
                "length_m": ld,
                "inner_diameter_m": branch_inner,
                "outer_diameter_m": branch_outer,
                "wall_thickness_m": branch_wall,
            },
            "bend_group": {
                "bend_count_each": bend_count,
                "illuminated_bend_count_each": illuminated_bends,
                "dark_bend_count_each": dark_bends,
                "arc_length_each_m": arc,
                "total_length_each_m": bend_total,
                "centerline_radius_m": rb,
                "angle_deg": angle,
            },
        },
        "geometry_totals": {
            "branch_centerline_length_each_m": branch_length,
            "common_supply_length_m": supply,
            "common_return_length_m": ret,
            "common_inner_diameter_m": common_inner,
            "common_outer_diameter_m": common_outer,
            "common_wall_thickness_m": common_wall,
            "installed_branch_centerline_length_total_m": n * branch_length,
            "installed_tube_centerline_length_total_m": n * branch_length + supply + ret,
            "representative_hydraulic_path_length_m": supply + branch_length + ret,
            "branch_liquid_volume_total_m3": branch_volume,
            "common_supply_liquid_volume_m3": supply_volume,
            "common_return_liquid_volume_m3": return_volume,
            "manifold_liquid_volume_total_m3": manifold_volume,
            "reservoir_liquid_volume_m3": reservoir_volume,
            "total_liquid_inventory_m3": branch_volume
            + supply_volume
            + return_volume
            + manifold_volume
            + reservoir_volume,
            "illuminated_branch_external_area_m2": illuminated_area,
            "dark_branch_external_area_m2": dark_area,
            "common_external_area_m2": common_area,
            "tube_external_area_total_m2": illuminated_area + dark_area + common_area,
            "tube_material_volume_proxy_m3": material_volume,
        },
    }
    _validate_manifest_geometry_agreement(manifest)
    manifest["geometry_totals"]["installed_tube_centerline_length_total_m"] += 1.0
    with pytest.raises(CadLinkError) as exc_info:
        _validate_manifest_geometry_agreement(manifest)
    assert exc_info.value.code == "cad_link_topology_manifest_identity_mismatch"
