from __future__ import annotations

from pathlib import Path

SOURCE = Path("backend/app/modules/bluecad/cad_link_topology_source.py")
TESTS = Path("backend/tests/test_cad_link_topology_preview.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one target, found {count}")
    return text.replace(old, new, 1)


def replace_function(text: str, name: str, replacement: str) -> str:
    start_marker = f"def {name}("
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"missing function {name}")
    next_start = text.find("\ndef ", start + len(start_marker))
    end = len(text) if next_start < 0 else next_start + 1
    return text[:start] + replacement.rstrip() + "\n\n\n" + text[end:]


source = SOURCE.read_text(encoding="utf-8")
source = replace_once(source, "import json\n", "import json\nimport math\n", "math import")
source = replace_once(
    source,
    """        SELECT mv.*, a.sha256 AS script_sha256, a.stored_path AS script_path,
               a.workspace_id AS script_workspace_id
""",
    """        SELECT mv.*, a.sha256 AS script_sha256, a.stored_path AS script_path,
               a.workspace_id AS script_workspace_id, a.status AS script_status
""",
    "model script metadata",
)
source = replace_once(
    source,
    """    if str(model[\"script_sha256\"]) != str(job[\"script_sha256\"]):
        raise CadLinkError(
            \"cad_link_model_identity_mismatch\",
            \"Source model and runner script identities disagree.\",
            status_code=422,
        )

    artifact_rows = connection.execute(
""",
    """    if str(model[\"script_sha256\"]) != str(job[\"script_sha256\"]):
        raise CadLinkError(
            \"cad_link_model_identity_mismatch\",
            \"Source model and runner script identities disagree.\",
            status_code=422,
        )
    _validate_model_script_artifact(model)

    artifact_rows = connection.execute(
""",
    "script byte validation call",
)
source = replace_once(
    source,
    """        resolved_path = stored_path.resolve(strict=True)
        resolved_output_dir = output_dir.resolve(strict=True)
        resolved_path.relative_to(data_root)
        resolved_output_dir.relative_to(data_root)
""",
    """        resolved_path = stored_path.resolve(strict=True)
        resolved_output_dir = output_dir.resolve(strict=True)
        resolved_expected_path = expected_path.resolve(strict=True)
        resolved_path.relative_to(data_root)
        resolved_output_dir.relative_to(data_root)
        resolved_expected_path.relative_to(data_root)
""",
    "expected manifest path resolution",
)
source = replace_once(
    source,
    """        or not resolved_path.is_file()
        or resolved_path != expected_path.resolve(strict=True)
""",
    """        or not resolved_path.is_file()
        or resolved_path != resolved_expected_path
""",
    "resolved expected path comparison",
)

helper = '''def _validate_model_script_artifact(model: Mapping[str, Any]) -> None:
    script_path = Path(str(model["script_path"]))
    try:
        resolved_path = script_path.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise CadLinkError(
            "cad_link_model_identity_mismatch",
            "Bundled topology script artifact is missing or invalid.",
            status_code=422,
        ) from exc
    if (
        model.get("script_status") != "registered"
        or script_path.is_symlink()
        or not resolved_path.is_file()
        or sha256_file(resolved_path) != str(model["script_sha256"])
    ):
        raise CadLinkError(
            "cad_link_model_identity_mismatch",
            "Bundled topology script bytes disagree with registered authority.",
            status_code=422,
        )'''
marker = "def _validate_manifest_geometry_agreement("
marker_index = source.find(marker)
if marker_index < 0:
    raise SystemExit("manifest agreement function missing")
source = source[:marker_index] + helper + "\n\n\n" + source[marker_index:]

agreement = '''def _validate_manifest_geometry_agreement(manifest: Mapping[str, Any]) -> None:
    inputs = _mapping(manifest, "executed_inputs")
    symmetry = _mapping(manifest, "symmetry")
    branch = _mapping(manifest, "branch_template")
    illuminated = _mapping(branch, "illuminated_straight")
    dark = _mapping(branch, "dark_straight")
    bends = _mapping(branch, "bend_group")
    totals = _mapping(manifest, "geometry_totals")

    def input_value(name: str) -> float:
        item = inputs.get(name)
        if not isinstance(item, Mapping):
            raise CadLinkError(
                "cad_link_topology_manifest_invalid",
                f"Topology manifest input {name} is missing.",
                status_code=422,
            )
        return float(_decimal(item.get("value")))

    parallel_count_value = input_value("parallel_path_count")
    bend_count_value = input_value("branch_bend_count")
    illuminated_bend_count_value = input_value("branch_illuminated_bend_count")
    if not parallel_count_value.is_integer() or not bend_count_value.is_integer() or not illuminated_bend_count_value.is_integer():
        raise CadLinkError(
            "cad_link_topology_manifest_identity_mismatch",
            "Topology manifest integer geometry disagrees with executed inputs.",
            status_code=409,
        )
    parallel_count = int(parallel_count_value)
    bend_count = int(bend_count_value)
    illuminated_bend_count = int(illuminated_bend_count_value)
    dark_bend_count = bend_count - illuminated_bend_count

    illuminated_straight_m = input_value("branch_illuminated_straight_length")
    dark_straight_m = input_value("branch_dark_straight_length")
    bend_radius_m = input_value("branch_bend_centerline_radius") / 1000.0
    bend_angle_deg = input_value("branch_bend_angle")
    bend_arc_each_m = bend_radius_m * math.radians(bend_angle_deg) if bend_count else 0.0
    bend_total_m = bend_count * bend_arc_each_m
    branch_length_each_m = illuminated_straight_m + bend_total_m + dark_straight_m
    common_supply_m = input_value("common_supply_length")
    common_return_m = input_value("common_return_length")
    branch_inner_m = input_value("branch_tube_inner_diameter") / 1000.0
    branch_outer_m = input_value("branch_tube_outer_diameter") / 1000.0
    common_inner_m = input_value("common_tube_inner_diameter") / 1000.0
    common_outer_m = input_value("common_tube_outer_diameter") / 1000.0
    branch_wall_m = (branch_outer_m - branch_inner_m) / 2.0
    common_wall_m = (common_outer_m - common_inner_m) / 2.0

    installed_branch_m = parallel_count * branch_length_each_m
    common_length_m = common_supply_m + common_return_m
    installed_total_m = installed_branch_m + common_length_m
    representative_path_m = common_supply_m + branch_length_each_m + common_return_m
    branch_area_m2 = math.pi * branch_inner_m**2 / 4.0
    common_area_m2 = math.pi * common_inner_m**2 / 4.0
    branch_liquid_total_m3 = parallel_count * branch_area_m2 * branch_length_each_m
    common_supply_volume_m3 = common_area_m2 * common_supply_m
    common_return_volume_m3 = common_area_m2 * common_return_m
    manifold_volume_m3 = (
        input_value("split_manifold_liquid_volume")
        + input_value("merge_manifold_liquid_volume")
    ) / 1000.0
    reservoir_volume_m3 = input_value("reservoir_liquid_volume") / 1000.0
    total_inventory_m3 = (
        branch_liquid_total_m3
        + common_supply_volume_m3
        + common_return_volume_m3
        + manifold_volume_m3
        + reservoir_volume_m3
    )
    illuminated_length_each_m = illuminated_straight_m + illuminated_bend_count * bend_arc_each_m
    dark_length_each_m = dark_straight_m + dark_bend_count * bend_arc_each_m
    illuminated_area_m2 = parallel_count * math.pi * branch_outer_m * illuminated_length_each_m
    dark_area_m2 = parallel_count * math.pi * branch_outer_m * dark_length_each_m
    common_external_area_m2 = math.pi * common_outer_m * common_length_m
    total_external_area_m2 = illuminated_area_m2 + dark_area_m2 + common_external_area_m2
    branch_wall_area_m2 = math.pi * (branch_outer_m**2 - branch_inner_m**2) / 4.0
    common_wall_area_m2 = math.pi * (common_outer_m**2 - common_inner_m**2) / 4.0
    tube_material_volume_m3 = (
        parallel_count * branch_wall_area_m2 * branch_length_each_m
        + common_wall_area_m2 * common_length_m
    )

    exact_counts = (
        (symmetry.get("parallel_path_count"), parallel_count),
        (bends.get("bend_count_each"), bend_count),
        (bends.get("illuminated_bend_count_each"), illuminated_bend_count),
        (bends.get("dark_bend_count_each"), dark_bend_count),
    )
    if any(_decimal(observed) != Decimal(expected) for observed, expected in exact_counts):
        raise CadLinkError(
            "cad_link_topology_manifest_identity_mismatch",
            "Topology manifest counts disagree with executed inputs.",
            status_code=409,
        )

    agreements = (
        (illuminated.get("length_m"), illuminated_straight_m),
        (illuminated.get("inner_diameter_m"), branch_inner_m),
        (illuminated.get("outer_diameter_m"), branch_outer_m),
        (illuminated.get("wall_thickness_m"), branch_wall_m),
        (dark.get("length_m"), dark_straight_m),
        (dark.get("inner_diameter_m"), branch_inner_m),
        (dark.get("outer_diameter_m"), branch_outer_m),
        (dark.get("wall_thickness_m"), branch_wall_m),
        (bends.get("centerline_radius_m"), bend_radius_m),
        (bends.get("angle_deg"), bend_angle_deg),
        (bends.get("arc_length_each_m"), bend_arc_each_m),
        (bends.get("total_length_each_m"), bend_total_m),
        (totals.get("branch_centerline_length_each_m"), branch_length_each_m),
        (totals.get("common_supply_length_m"), common_supply_m),
        (totals.get("common_return_length_m"), common_return_m),
        (totals.get("common_inner_diameter_m"), common_inner_m),
        (totals.get("common_outer_diameter_m"), common_outer_m),
        (totals.get("common_wall_thickness_m"), common_wall_m),
        (totals.get("installed_branch_centerline_length_total_m"), installed_branch_m),
        (totals.get("installed_tube_centerline_length_total_m"), installed_total_m),
        (totals.get("representative_hydraulic_path_length_m"), representative_path_m),
        (totals.get("branch_liquid_volume_total_m3"), branch_liquid_total_m3),
        (totals.get("common_supply_liquid_volume_m3"), common_supply_volume_m3),
        (totals.get("common_return_liquid_volume_m3"), common_return_volume_m3),
        (totals.get("manifold_liquid_volume_total_m3"), manifold_volume_m3),
        (totals.get("reservoir_liquid_volume_m3"), reservoir_volume_m3),
        (totals.get("total_liquid_inventory_m3"), total_inventory_m3),
        (totals.get("illuminated_branch_external_area_m2"), illuminated_area_m2),
        (totals.get("dark_branch_external_area_m2"), dark_area_m2),
        (totals.get("common_external_area_m2"), common_external_area_m2),
        (totals.get("tube_external_area_total_m2"), total_external_area_m2),
        (totals.get("tube_material_volume_proxy_m3"), tube_material_volume_m3),
    )
    for observed, expected in agreements:
        actual = float(_decimal(observed))
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-15):
            raise CadLinkError(
                "cad_link_topology_manifest_identity_mismatch",
                "Topology manifest geometry disagrees with executed inputs.",
                status_code=409,
            )'''
source = replace_function(source, "_validate_manifest_geometry_agreement", agreement)
SOURCE.write_text(source, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
if "test_source_authority_rejects_tampered_script_artifact_bytes" not in tests:
    tests += r'''


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
        tampered_path = Path(connection.execute(
            "SELECT stored_path FROM artifacts WHERE id = ?",
            (row["implementation_artifact_id"],),
        ).fetchone()["stored_path"]).with_name("tampered-topology-script.py")
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
        float(inputs["split_manifold_liquid_volume"]["value"])
        + float(inputs["merge_manifold_liquid_volume"]["value"])
    ) / 1000.0
    reservoir_volume = float(inputs["reservoir_liquid_volume"]["value"]) / 1000.0
    illuminated_area = n * math.pi * branch_outer * (li + illuminated_bends * arc)
    dark_area = n * math.pi * branch_outer * (ld + dark_bends * arc)
    common_area = math.pi * common_outer * (supply + ret)
    material_volume = (
        n * math.pi * (branch_outer**2 - branch_inner**2) / 4.0 * branch_length
        + math.pi * (common_outer**2 - common_inner**2) / 4.0 * (supply + ret)
    )
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
            "total_liquid_inventory_m3": branch_volume + supply_volume + return_volume + manifold_volume + reservoir_volume,
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
'''
    TESTS.write_text(tests, encoding="utf-8")
