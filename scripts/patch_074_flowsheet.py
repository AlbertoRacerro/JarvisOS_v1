from __future__ import annotations

from pathlib import Path

SERVICE = Path("backend/app/modules/flowsheet/service.py")
TEST = Path("backend/tests/test_cad_link_topology_execute.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one target, found {count}")
    return text.replace(old, new, 1)


service = SERVICE.read_text(encoding="utf-8")
service = replace_once(
    service,
    '''        "cad_link": (
            "SELECT source_simulation_run_id, child_candidate_id "
            "FROM bluecad_cad_links WHERE workspace_id = ?"
        ),
''',
    '''        "cad_link": (
            "SELECT source_simulation_run_id, child_candidate_id, transformation_version "
            "FROM bluecad_cad_links WHERE workspace_id = ?"
        ),
''',
    "cad-link row projection",
)
service = replace_once(
    service,
    '''    for row in rows["cad_link"]:
        _add_typed_edge(
            builder,
            "simulation_run",
            row.get("source_simulation_run_id"),
            _ref("bluecad_candidate", row.get("child_candidate_id")),
            "m0_geometry_link",
            "dependency",
            "bluecad_cad_links.source_simulation_run_id",
        )
''',
    '''    for row in rows["cad_link"]:
        relation = (
            "m1_topology_geometry_link"
            if row.get("transformation_version")
            == "bluerev_072_m1_planar_tubing_v0_1"
            else "m0_geometry_link"
        )
        _add_typed_edge(
            builder,
            "simulation_run",
            row.get("source_simulation_run_id"),
            _ref("bluecad_candidate", row.get("child_candidate_id")),
            relation,
            "dependency",
            "bluecad_cad_links.source_simulation_run_id",
        )
''',
    "cad-link lineage relation",
)
SERVICE.write_text(service, encoding="utf-8")

test = TEST.read_text(encoding="utf-8")
helper_marker = '''def _preview(client: TestClient, simulation_run_id: str) -> dict[str, object]:
'''
golden_helpers = '''def _golden_layout() -> dict[str, object]:
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


''' + helper_marker
if "def _golden_layout" not in test:
    test = replace_once(test, helper_marker, golden_helpers, "golden execute helpers")
test = test.replace("SUPPORT._layout()", "_golden_layout()")
test = test.replace(
    "SUPPORT._create_source_run(client)",
    "_create_golden_source_run(client)",
)
test = test.replace(
    "WHERE id = 'geometry-count-shared'",
    "WHERE id = 'golden-parallel_path_count'",
)
marker = '''    second = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/execute",
        json=request,
    )
'''
insert = '''    from app.modules.flowsheet.service import get_flowsheet_graph

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

''' + marker
if "m1_topology_geometry_link" not in test:
    test = replace_once(test, marker, insert, "execute lineage assertion")
TEST.write_text(test, encoding="utf-8")
