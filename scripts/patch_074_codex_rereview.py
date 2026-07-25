from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one target in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_topology() -> None:
    path = Path("backend/app/modules/bluecad/cad_link_topology.py")
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "import sqlite3\nfrom typing import Any\n",
        "import sqlite3\nfrom copy import deepcopy\nfrom typing import Any\n",
        1,
    )
    start = text.index("def _build_preview(\n")
    end = text.index("\n\ndef _canonical_analysis_contract", start)
    block = '''def _build_preview(
    connection: sqlite3.Connection,
    workspace_id: str,
    payload: CadLink072PreviewRequest,
) -> dict[str, Any]:
    return _build_preview_evidence(
        connection,
        workspace_id,
        payload,
        kernel_preflight=None,
    )


def _rebuild_preview_without_kernel(
    connection: sqlite3.Connection,
    workspace_id: str,
    payload: CadLink072PreviewRequest,
    kernel_preflight: dict[str, Any],
) -> dict[str, Any]:
    """Recheck mutable authority under a short transaction without kernel work."""

    return _build_preview_evidence(
        connection,
        workspace_id,
        payload,
        kernel_preflight=kernel_preflight,
    )


def _build_preview_evidence(
    connection: sqlite3.Connection,
    workspace_id: str,
    payload: CadLink072PreviewRequest,
    *,
    kernel_preflight: dict[str, Any] | None,
) -> dict[str, Any]:
    source = load_topology_source(
        connection,
        workspace_id,
        payload.source_simulation_run_id,
    )
    layout = canonicalize_layout(source["manifest"], payload.layout_spec)
    resolved_spec, boundaries, component_inventory = resolve_geometry_spec(
        source["manifest"],
        layout,
    )
    preflight = (
        run_kernel_preflight(resolved_spec, boundaries)
        if kernel_preflight is None
        else deepcopy(kernel_preflight)
    )
    process_reconciliation = reconcile_topology(
        source["manifest"],
        layout,
        resolved_spec,
        preflight,
    )
    analysis_contract = _canonical_analysis_contract(payload.analysis_spec)
    layout_digest = digest(layout)
    preflight_digest = digest(preflight)
    execution_policy = {"build_timeout_seconds": BUILD_TIMEOUT_SECONDS}
    reconciliation = {
        "schema_version": "cad_link_072_link_evidence_v0_1",
        "layout_spec": layout,
        "layout_digest": layout_digest,
        "external_boundaries": boundaries,
        "component_inventory": component_inventory,
        "kernel_preflight": preflight,
        "kernel_preflight_digest": preflight_digest,
        "tolerances": dict(TOLERANCES),
        "execution_policy": execution_policy,
        "checks": process_reconciliation["checks"],
        "structural_checks": process_reconciliation["structural_checks"],
        "process_cad_reconciliation": process_reconciliation,
    }

    preview: dict[str, Any] = {
        "workspace_id": workspace_id,
        "source_simulation_run_id": source["simulation_run_id"],
        "source_runner_job_id": source["runner_job_id"],
        "source_model_identity": source["model_identity"],
        "source_model_identity_digest": digest(source["model_identity"]),
        "source_topology_manifest": source["manifest_artifact"],
        "source_geometry_parameters": source["parameter_snapshots"],
        "source_snapshot": source["source_snapshot"],
        "source_snapshot_digest": digest(source["source_snapshot"]),
        "layout_spec": layout,
        "layout_digest": layout_digest,
        "transformation_version": TRANSFORMATION_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "execution_policy": execution_policy,
        "resolved_spec": resolved_spec,
        "spec_id": resolved_spec["spec_id"],
        "resolved_spec_digest": str(resolved_spec["spec_id"]),
        "resolved_part_count": len(resolved_spec["parts"]),
        "resolved_connection_count": len(resolved_spec.get("connections", [])),
        "external_boundaries": boundaries,
        "component_inventory": component_inventory,
        "kernel_preflight": preflight,
        "kernel_preflight_digest": preflight_digest,
        "tolerances": dict(TOLERANCES),
        "reconciliation": reconciliation,
        "reconciliation_digest": digest(reconciliation),
        "analysis_contract": analysis_contract,
        "analysis_contract_digest": (
            None if analysis_contract is None else digest(analysis_contract)
        ),
    }
    preview["preview_digest"] = digest(preview)
    return preview
'''
    path.write_text(text[:start] + block + text[end:], encoding="utf-8")


def patch_execute() -> None:
    path = Path("backend/app/modules/bluecad/cad_link_topology_execute.py")
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "    _build_preview,\n    preview_cad_link_072,\n",
        "    _rebuild_preview_without_kernel,\n    preview_cad_link_072,\n",
        1,
    )
    old_call = '''                    current = _preview_from_connection(
                        connection,
                        workspace_id,
                        preview_request,
                    )
'''
    new_call = '''                    current = _preview_from_connection(
                        connection,
                        workspace_id,
                        preview_request,
                        preview["kernel_preflight"],
                    )
'''
    if text.count(old_call) != 1:
        raise SystemExit("execute transactional preview call target missing")
    text = text.replace(old_call, new_call, 1)
    old_helper = '''def _preview_from_connection(
    connection: sqlite3.Connection,
    workspace_id: str,
    request: CadLink072PreviewRequest,
) -> dict[str, Any]:
    try:
        return _build_preview(connection, workspace_id, request)
    except CadLinkError as exc:
        if exc.code.startswith("cad_link_kernel_"):
            raise
        raise _preview_stale() from exc
'''
    new_helper = '''def _preview_from_connection(
    connection: sqlite3.Connection,
    workspace_id: str,
    request: CadLink072PreviewRequest,
    kernel_preflight: dict[str, Any],
) -> dict[str, Any]:
    try:
        return _rebuild_preview_without_kernel(
            connection,
            workspace_id,
            request,
            kernel_preflight,
        )
    except CadLinkError as exc:
        if exc.code.startswith("cad_link_kernel_"):
            raise
        raise _preview_stale() from exc
'''
    if text.count(old_helper) != 1:
        raise SystemExit("execute preview helper target missing")
    path.write_text(text.replace(old_helper, new_helper, 1), encoding="utf-8")


def patch_source_snapshot() -> None:
    path = Path("backend/app/modules/bluecad/cad_link_topology_source.py")
    replace_once(
        path,
        '        "topology_manifest": artifact_snapshot,\n        "geometry_parameters": parameter_snapshots,\n',
        '        "topology_manifest": artifact_snapshot,\n'
        '        "topology_manifest_payload": json.loads(canonical_json(manifest)),\n'
        '        "geometry_parameters": parameter_snapshots,\n',
    )


def patch_residual_contact() -> None:
    path = Path("backend/app/modules/bluecad/cad_link_topology_preflight.py")
    old = '''    residual_distance = _shape_distance(left_residual, right_residual)
    residual_topology = _intersection_topology(residual_intersection)
    if residual_distance <= COINCIDENCE_ABS_TOL_MM or any(
        residual_topology[key] > 0 for key in ("face_count", "edge_count", "vertex_count")
    ):
        raise _contact_error()
    return residual_distance
'''
    new = '''    residual_distance = _shape_distance(left_residual, right_residual)
    residual_topology = _intersection_topology(residual_intersection)
    if _has_topological_contact(residual_topology):
        raise _contact_error()
    return residual_distance
'''
    replace_once(path, old, new)


def patch_preview_tests() -> None:
    path = Path("backend/tests/test_cad_link_topology_preview.py")
    text = path.read_text(encoding="utf-8")
    old_assertions = '''    snapshots = first.json()["source_geometry_parameters"]
    assert snapshots["parallel_path_count"]["parameter_id"] == "geometry-count-shared"
    assert snapshots["branch_bend_count"]["parameter_id"] == "geometry-count-shared"
    assert first.json()["resolved_part_count"] == 12
'''
    new_assertions = '''    snapshots = first.json()["source_geometry_parameters"]
    assert snapshots["parallel_path_count"]["parameter_id"] == "geometry-count-shared"
    assert snapshots["branch_bend_count"]["parameter_id"] == "geometry-count-shared"
    manifest_snapshot = first.json()["source_snapshot"]["topology_manifest_payload"]
    executed_inputs = manifest_snapshot["executed_inputs"]
    assert executed_inputs["reservoir_liquid_volume"] == _input_payload()[
        "reservoir_liquid_volume"
    ]
    assert set(executed_inputs) > set(GEOMETRY_PARAMETER_INPUTS)
    assert first.json()["resolved_part_count"] == 12
'''
    if text.count(old_assertions) != 1:
        raise SystemExit("preview snapshot assertions target missing")
    text = text.replace(old_assertions, new_assertions, 1)
    marker = '''


def _preview_request(simulation_run_id: str) -> dict[str, object]:
'''
    test = '''


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
'''
    if text.count(marker) != 1:
        raise SystemExit("preview recheck test insertion target missing")
    path.write_text(text.replace(marker, test + marker, 1), encoding="utf-8")


def patch_preflight_tests() -> None:
    path = Path("backend/tests/bluecad/test_cad_link_topology_preflight.py")
    text = path.read_text(encoding="utf-8")
    old_import = '''    _kernel_bbox,
    _validate_port_contact_topology,
    run_kernel_preflight,
'''
    new_import = '''    _kernel_bbox,
    _validate_no_extra_contact,
    _validate_port_contact_topology,
    run_kernel_preflight,
'''
    if text.count(old_import) != 1:
        raise SystemExit("preflight import target missing")
    text = text.replace(old_import, new_import, 1)
    test = '''


def test_connected_residual_positive_submicron_gap_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ResidualShape:
        def __sub__(self, _other):
            return self

    left = ResidualShape()
    right = ResidualShape()
    residual_intersection = object()
    port = PortFrame((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 60.0, 5.0)

    monkeypatch.setattr(
        preflight_module,
        "_allowed_contact_neighborhood",
        lambda _port: object(),
    )
    monkeypatch.setattr(
        preflight_module,
        "_shape_intersection",
        lambda *_args: residual_intersection,
    )
    monkeypatch.setattr(
        preflight_module,
        "_shape_volume",
        lambda shape: 0.0 if shape is residual_intersection else 1.0,
    )
    monkeypatch.setattr(
        preflight_module,
        "_shape_distance",
        lambda *_args: 5e-7,
    )
    monkeypatch.setattr(
        preflight_module,
        "_intersection_topology",
        lambda _shape: {
            "face_count": 0,
            "edge_count": 0,
            "vertex_count": 0,
            "faces": [],
            "edges": [],
        },
    )

    assert _validate_no_extra_contact(left, right, port) == pytest.approx(5e-7)
'''
    if "test_connected_residual_positive_submicron_gap_is_allowed" in text:
        raise SystemExit("residual clearance test already present")
    path.write_text(text + test, encoding="utf-8")


patch_topology()
patch_execute()
patch_source_snapshot()
patch_residual_contact()
patch_preview_tests()
patch_preflight_tests()
