from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "backend/app/modules/runner/examples/bluerev_process_topology_m1_v0.py"
SERVICE = ROOT / "backend/app/modules/runner/service.py"
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
    '''    and v_merge == 0.0
    and di_c == di_b
    and do_c == do_b
)
''',
    '''    and v_merge == 0.0
    and di_c == di_b
    and do_c == do_b
    and branch_dark_length == 0.0
)
''',
)
replace_once(
    MODEL,
    '''    and ld == 0.0
    and values["common_supply_minor_loss_coefficient"] == 0.0
    and values["split_manifold_loss_coefficient"] == 0.0
    and values["merge_manifold_loss_coefficient"] == 0.0
    and values["common_return_minor_loss_coefficient"] == 0.0
)
''',
    '''    and ld == 0.0
)
''',
)

replace_once(
    SERVICE,
    '''            topology_profile = is_exact_bundled_profile(model_version, script_sha)
            preflight_script_policy(
''',
    '''            topology_profile = is_exact_bundled_profile(model_version, script_sha)
            if topology_profile:
                _validate_topology_source_parameter_bindings(
                    connection,
                    workspace_id,
                    input_payload,
                )
            preflight_script_policy(
''',
)
helper = '''


def _validate_topology_source_parameter_bindings(
    connection,
    workspace_id: str,
    input_payload: str,
) -> None:
    inputs = json.loads(input_payload)
    for name, item in inputs.items():
        source_parameter_id = item.get("source_parameter_id")
        if source_parameter_id is None:
            continue
        row = connection.execute(
            """
            SELECT value, unit, status
            FROM parameters
            WHERE id = ? AND workspace_id = ?
            """,
            (source_parameter_id, workspace_id),
        ).fetchone()
        if row is None:
            raise RunnerSafetyError(
                "runner_topology_source_parameter_not_found",
                f"Topology input {name} references a Parameter that does not exist in the workspace.",
            )
        if row["status"] != "accepted":
            raise RunnerSafetyError(
                "runner_topology_source_parameter_not_accepted",
                f"Topology input {name} must reference an accepted Parameter.",
            )
        try:
            parameter_value = float(row["value"])
        except (TypeError, ValueError) as exc:
            raise RunnerSafetyError(
                "runner_topology_source_parameter_mismatch",
                f"Topology input {name} source Parameter value is not finite numeric data.",
            ) from exc
        if (
            not isfinite(parameter_value)
            or parameter_value != float(item["value"])
            or row["unit"] != item["unit"]
        ):
            raise RunnerSafetyError(
                "runner_topology_source_parameter_mismatch",
                f"Topology input {name} does not match its source Parameter value and unit.",
            )
'''
replace_once(
    SERVICE,
    '''

def _load_runner_job(connection, runner_job_id: str):
''',
    helper + '''

def _load_runner_job(connection, runner_job_id: str):
''',
)

replace_once(
    DIRECT_TEST,
    '''        common_supply_minor_loss_coefficient=(0.0, "1"),
        split_manifold_loss_coefficient=(0.0, "1"),
        merge_manifold_loss_coefficient=(0.0, "1"),
        common_return_minor_loss_coefficient=(0.0, "1"),
''',
    '''        common_supply_minor_loss_coefficient=(0.01, "1"),
        split_manifold_loss_coefficient=(0.02, "1"),
        branch_misc_minor_loss_coefficient=(0.03, "1"),
        merge_manifold_loss_coefficient=(0.02, "1"),
        common_return_minor_loss_coefficient=(0.02, "1"),
''',
)
DIRECT_TEST.write_text(
    DIRECT_TEST.read_text(encoding="utf-8")
    + r'''


def test_single_length_projection_rejects_dark_straight_split(tmp_path):
    payload = reduction_input()
    payload["branch_illuminated_straight_length"]["value"] = 11.0
    payload["branch_dark_straight_length"]["value"] = 1.0
    completed = run_model(tmp_path, payload)
    assert completed.returncode == 0, completed.stderr
    diagnostics = json.loads(
        (tmp_path / "result.json").read_text(encoding="utf-8")
    )["diagnostics"]
    assert diagnostics["single_length_projection_status"] == (
        "not_single_length_representable"
    )
    assert diagnostics["m0_reduction_status"] == "not_m0_reduction_case"


def test_single_length_projection_rejects_nonilluminated_bend(tmp_path):
    payload = reduction_input()
    payload["branch_bend_count"]["value"] = 1
    payload["branch_illuminated_bend_count"]["value"] = 0
    payload["branch_bend_centerline_radius"]["value"] = 100.0
    payload["branch_bend_angle"]["value"] = 90.0
    payload["branch_bend_loss_coefficient_per_bend"]["value"] = 0.2
    completed = run_model(tmp_path, payload)
    assert completed.returncode == 0, completed.stderr
    diagnostics = json.loads(
        (tmp_path / "result.json").read_text(encoding="utf-8")
    )["diagnostics"]
    assert diagnostics["single_length_projection_status"] == (
        "not_single_length_representable"
    )
    assert diagnostics["m0_reduction_status"] == "not_m0_reduction_case"
''',
    encoding="utf-8",
)

RUNNER_TEST.write_text(
    RUNNER_TEST.read_text(encoding="utf-8")
    + r'''


@pytest.mark.parametrize(
    ("case", "expected_code"),
    [
        ("missing", "runner_topology_source_parameter_not_found"),
        ("wrong_value", "runner_topology_source_parameter_mismatch"),
        ("wrong_unit", "runner_topology_source_parameter_mismatch"),
        ("not_accepted", "runner_topology_source_parameter_not_accepted"),
    ],
)
def test_direct_runner_rejects_invalid_source_parameter_binding(
    client: TestClient,
    case: str,
    expected_code: str,
) -> None:
    source_parameter_id = f"source-parameter-{case}"
    if case != "missing":
        parameter_value = "999" if case == "wrong_value" else "1000"
        parameter_unit = "g/L" if case == "wrong_unit" else "kg/m3"
        parameter_status = "proposed" if case == "not_accepted" else "accepted"
        now = utc_now()
        with open_sqlite_connection() as connection:
            connection.execute(
                """
                INSERT INTO parameters (
                    id, workspace_id, name, value, unit, value_status, status,
                    created_at, updated_at, origin
                ) VALUES (?, 'bluerev', ?, ?, ?, 'known', ?, ?, ?, 'manual')
                """,
                (
                    source_parameter_id,
                    f"Source parameter {case}",
                    parameter_value,
                    parameter_unit,
                    parameter_status,
                    now,
                    now,
                ),
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
    assert created.status_code == 400, created.text
    assert created.json()["detail"]["code"] == expected_code
    with open_sqlite_connection() as connection:
        assert int(
            connection.execute(
                "SELECT COUNT(*) AS count FROM simulation_runs"
            ).fetchone()["count"]
        ) == 0
''',
    encoding="utf-8",
)
