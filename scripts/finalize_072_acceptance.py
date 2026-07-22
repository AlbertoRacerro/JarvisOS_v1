import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "backend/app/modules/runner/examples/bluerev_process_topology_m1_v0.py"
SCHEMA = ROOT / "schemas/bluerev_process_topology_m1_v0_1.schema.json"
DIRECT_TEST = ROOT / "backend/tests/test_bluerev_process_topology_m1.py"
RUNNER_TEST = ROOT / "backend/tests/test_bluerev_process_topology_m1_runner.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


replace_once(
    MODEL,
    '''        "branch_centerline_length_each_m": branch_length,
        "installed_branch_centerline_length_total_m": installed_branch_length,
''',
    '''        "branch_centerline_length_each_m": branch_length,
        "common_supply_length_m": ls,
        "common_return_length_m": lr,
        "common_inner_diameter_m": di_c,
        "common_outer_diameter_m": do_c,
        "common_wall_thickness_m": common_wall_thickness_mm / 1000.0,
        "installed_branch_centerline_length_total_m": installed_branch_length,
''',
)

schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
geometry = schema["properties"]["geometry_totals"]
properties = geometry["properties"]
required = geometry["required"]
new_properties = {
    "common_supply_length_m": {"type": "number", "minimum": 0},
    "common_return_length_m": {"type": "number", "minimum": 0},
    "common_inner_diameter_m": {"type": "number", "exclusiveMinimum": 0},
    "common_outer_diameter_m": {"type": "number", "exclusiveMinimum": 0},
    "common_wall_thickness_m": {"type": "number", "exclusiveMinimum": 0},
}
for name, definition in new_properties.items():
    if name in properties or name in required:
        raise SystemExit(f"schema field already present: {name}")
    properties[name] = definition
insert_at = required.index("installed_branch_centerline_length_total_m")
for name in reversed(list(new_properties)):
    required.insert(insert_at, name)
SCHEMA.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")

replace_once(
    DIRECT_TEST,
    '''    assert manifest["symmetry"]["parallel_path_count"] == 2
    assert manifest["ordered_components"][3] == "parallel_branch_group"
''',
    '''    assert manifest["symmetry"]["parallel_path_count"] == 2
    assert manifest["ordered_components"][3] == "parallel_branch_group"
    geometry = manifest["geometry_totals"]
    assert geometry["common_supply_length_m"] == pytest.approx(1.0)
    assert geometry["common_return_length_m"] == pytest.approx(1.5)
    assert geometry["common_inner_diameter_m"] == pytest.approx(0.08)
    assert geometry["common_outer_diameter_m"] == pytest.approx(0.09)
    assert geometry["common_wall_thickness_m"] == pytest.approx(0.005)
''',
)
replace_once(
    DIRECT_TEST,
    '''    assert outputs["pump_electric_power"]["value"] == pytest.approx(hydraulic_power / 0.7)
    assert result["diagnostics"]["m0_reduction_status"] == "exact_047_reduction"
''',
    '''    assert outputs["pump_electric_power"]["value"] == pytest.approx(hydraulic_power / 0.7)
    expected_material = math.pi * (outer**2 - diameter**2) / 4.0 * length
    assert outputs["tube_material_volume_proxy"]["value"] == pytest.approx(expected_material)
    assert result["diagnostics"]["m0_reduction_status"] == "exact_047_reduction"
''',
)
DIRECT_TEST.write_text(
    DIRECT_TEST.read_text(encoding="utf-8")
    + r'''


def test_manifest_bytes_are_identical_for_repeated_identical_runs(tmp_path):
    payload = input_set()
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    assert run_model(first, payload).returncode == 0
    assert run_model(second, payload).returncode == 0
    assert (first / "topology_manifest.json").read_bytes() == (
        second / "topology_manifest.json"
    ).read_bytes()
''',
    encoding="utf-8",
)

replace_once(
    RUNNER_TEST,
    '''from app.modules.runner.input_contracts import canonicalize_input_contract
''',
    '''from app.core.database import open_sqlite_connection
from app.modules.events.service import utc_now
from app.modules.flowsheet.freshness import (
    persist_freshness_invalidation,
    prepare_freshness_invalidation,
)
from app.modules.runner.input_contracts import canonicalize_input_contract
''',
)
replace_once(
    RUNNER_TEST,
    '''    assert all(row["sha256"] and len(row["sha256"]) == 64 for row in rows)
    manifest_row = next(row for row in rows if row["role"] == "bluerev_topology_manifest")
''',
    '''    assert all(row["sha256"] and len(row["sha256"]) == 64 for row in rows)
    with open_sqlite_connection() as connection:
        assert int(connection.execute("SELECT COUNT(*) AS count FROM ai_jobs").fetchone()["count"]) == 0
    manifest_row = next(row for row in rows if row["role"] == "bluerev_topology_manifest")
''',
)
replace_once(
    RUNNER_TEST,
    '''        ("digest", "runner_topology_manifest_digest_mismatch"),
    ],
)
''',
    '''        ("digest", "runner_topology_manifest_digest_mismatch"),
        ("extra", "runner_topology_manifest_schema_invalid"),
        ("oversized", "runner_topology_manifest_too_large"),
        ("symlink", "runner_topology_manifest_invalid"),
    ],
)
''',
)
replace_once(
    RUNNER_TEST,
    '''    if mutation == "missing":
        path.unlink()
    elif mutation == "malformed":
        path.write_text("{", encoding="utf-8")
    else:
''',
    '''    if mutation == "missing":
        path.unlink()
    elif mutation == "malformed":
        path.write_text("{", encoding="utf-8")
    elif mutation == "symlink":
        target = tmp_path / "manifest-target.json"
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
    else:
''',
)
replace_once(
    RUNNER_TEST,
    '''        if mutation == "schema":
            manifest["topology_kind"] = "wrong"
        elif mutation == "input":
            manifest["executed_inputs"]["liquid_density"]["value"] = 999.0
''',
    '''        if mutation == "schema":
            manifest["topology_kind"] = "wrong"
        elif mutation == "input":
            manifest["executed_inputs"]["liquid_density"]["value"] = 999.0
        elif mutation == "extra":
            manifest["unexpected"] = True
''',
)
replace_once(
    RUNNER_TEST,
    '''            max_bytes=1024 * 1024,
        )
''',
    '''            max_bytes=(1 if mutation == "oversized" else 1024 * 1024),
        )
''',
)
replace_once(
    RUNNER_TEST,
    '''    assert artifacts.status_code == 200
    assert artifacts.json() == []
''',
    '''    assert artifacts.status_code == 200
    assert artifacts.json() == []
    with open_sqlite_connection() as connection:
        assert int(
            connection.execute(
                "SELECT COUNT(*) AS count FROM parameters WHERE origin = 'calc'"
            ).fetchone()["count"]
        ) == 0
''',
)
RUNNER_TEST.write_text(
    RUNNER_TEST.read_text(encoding="utf-8")
    + r'''


def test_topology_run_reuses_flowsheet_lineage_and_staleness(client: TestClient) -> None:
    source_parameter_id = "source-parameter-072"
    replacement_parameter_id = "replacement-parameter-072"
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO parameters (
                id, workspace_id, name, value, unit, value_status, status,
                created_at, updated_at, origin
            ) VALUES (?, 'bluerev', 'Liquid density source', '1000', 'kg/m3',
                      'known', 'accepted', ?, ?, 'manual')
            """,
            (source_parameter_id, now, now),
        )
        connection.execute(
            """
            INSERT INTO parameters (
                id, workspace_id, name, value, unit, value_status, status,
                created_at, updated_at, origin, supersedes_parameter_id
            ) VALUES (?, 'bluerev', 'Liquid density replacement', '998', 'kg/m3',
                      'known', 'proposed', ?, ?, 'manual', ?)
            """,
            (replacement_parameter_id, now, now, source_parameter_id),
        )
        connection.commit()

    endpoint = "/workspaces/bluerev/bundled-models/bluerev-process-topology-m1-v0/register"
    implementation = client.post(endpoint).json()
    payload = _valid_input()
    payload["liquid_density"]["source_parameter_id"] = source_parameter_id
    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation["id"], "input_set": payload},
    )
    assert created.status_code == 201, created.text
    runner_job = created.json()["runner_job"]
    executed = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert executed.status_code == 200, executed.text
    body = executed.json()
    assert body["runner_job"]["status"] == "succeeded"
    run_id = body["simulation_run"]["id"]

    artifacts = client.get(
        f"/workspaces/bluerev/simulation-runs/{run_id}/artifacts"
    ).json()
    artifact_refs = {f"artifact:{row['artifact_id']}" for row in artifacts}
    graph_response = client.get("/workspaces/bluerev/flowsheet/graph")
    assert graph_response.status_code == 200, graph_response.text
    graph = graph_response.json()
    edges = {
        (edge["upstream_ref"], edge["downstream_ref"], edge["relation"])
        for edge in graph["edges"]
    }
    run_ref = f"simulation_run:{run_id}"
    runner_ref = f"runner_job:{runner_job['id']}"
    assert (f"parameter:{source_parameter_id}", run_ref, "bound_input") in edges
    assert (f"model_version:{implementation['id']}", run_ref, "configured_run") in edges
    assert (run_ref, runner_ref, "executed_by") in edges
    for artifact_ref in artifact_refs:
        assert (run_ref, artifact_ref, "produced_artifact") in edges

    with open_sqlite_connection() as connection:
        prepared = prepare_freshness_invalidation(
            connection,
            workspace_id="bluerev",
            superseded_parameter_id=source_parameter_id,
            replacement_parameter_id=replacement_parameter_id,
            created_at=utc_now(),
        )
        persist_freshness_invalidation(connection, prepared)
        connection.commit()

    run_freshness = client.get(
        f"/workspaces/bluerev/flowsheet/nodes/{run_ref}/freshness"
    )
    assert run_freshness.status_code == 200, run_freshness.text
    assert run_freshness.json()["state"] == "stale"
    for artifact_ref in artifact_refs:
        freshness = client.get(
            f"/workspaces/bluerev/flowsheet/nodes/{artifact_ref}/freshness"
        )
        assert freshness.status_code == 200, freshness.text
        assert freshness.json()["state"] == "stale"
''',
    encoding="utf-8",
)
