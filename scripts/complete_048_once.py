from pathlib import Path
import re


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def regex_once(path: str, pattern: str, replacement: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f"{path}: expected one regex match, found {count}: {pattern[:100]!r}")
    target.write_text(updated, encoding="utf-8")


script = "backend/app/modules/runner/examples/bluerev_biomass_nutrients_harvest_v0.py"
replace_once(
    script,
    '"oxygen_volume_stp_equivalent": {"value": oxygen_volume_stp, "unit": "L/d"},',
    '"oxygen_volume_stp_equivalent": {"value": oxygen_volume_stp, "unit": "L O2/d"},',
)

service = "backend/app/modules/runner/service.py"
replace_once(
    service,
    'BUNDLED_BLUEREV_PROCESS0_LABEL = "bluerev-geometry-hydraulics-v0-bundled"\n'
    'BUNDLED_BLUEREV_PROCESS0_TITLE = "BlueRev geometry and hydraulics bundled V0"\n',
    'BUNDLED_BLUEREV_PROCESS0_LABEL = "bluerev-geometry-hydraulics-v0-bundled"\n'
    'BUNDLED_BLUEREV_PROCESS0_TITLE = "BlueRev geometry and hydraulics bundled V0"\n'
    'BUNDLED_BLUEREV_PROCESS1_LABEL = "bluerev-biomass-nutrients-harvest-v0-bundled"\n'
    'BUNDLED_BLUEREV_PROCESS1_TITLE = "BlueRev biomass, nutrients, and harvesting bundled V0"\n',
)
process1_function = '''

def register_bundled_bluerev_process1(workspace_id: str) -> ModelImplementationRead:
    script_path = _bluerev_process1_script_path()
    contract_path = _bluerev_process1_contract_path()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    _, contract_sha256, _ = canonicalize_input_contract(contract)
    script_sha256 = sha256_file(script_path)

    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        existing = connection.execute(
            """
            SELECT mv.*, a.sha256 AS script_sha256, a.stored_path AS script_path
            FROM model_versions mv
            JOIN artifacts a ON a.id = mv.implementation_artifact_id
            WHERE mv.workspace_id = ?
              AND mv.version_label = ?
              AND mv.input_contract_sha256 = ?
              AND a.sha256 = ?
            ORDER BY mv.created_at ASC
            LIMIT 1
            """,
            (
                workspace_id,
                BUNDLED_BLUEREV_PROCESS1_LABEL,
                contract_sha256,
                script_sha256,
            ),
        ).fetchone()
        if existing is not None:
            return _model_implementation_from_row(existing)
        model_spec = connection.execute(
            """
            SELECT id FROM model_specs
            WHERE workspace_id = ? AND title = ?
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (workspace_id, BUNDLED_BLUEREV_PROCESS1_TITLE),
        ).fetchone()

    if model_spec is None:
        created_spec = create_model_spec(
            workspace_id,
            ModelSpecCreate(
                title=BUNDLED_BLUEREV_PROCESS1_TITLE,
                engineering_question=(
                    "Evaluate caller-selected biomass production, nutrient incorporation, "
                    "gas proxies, harvesting, pump electricity, and bounded preliminary economics."
                ),
                scope=(
                    "Reviewed 048 forward M0 model; all project and operating values are supplied "
                    "per scenario and the economic boundary is pump electricity only."
                ),
            ),
        )
        model_spec_id = created_spec.id
    else:
        model_spec_id = str(model_spec["id"])

    return create_model_implementation(
        workspace_id,
        ModelImplementationCreate(
            model_spec_id=model_spec_id,
            version_label=BUNDLED_BLUEREV_PROCESS1_LABEL,
            implementation_kind=CALC_V0_IMPLEMENTATION_KIND,
            notes="Bundled reviewed 048 forward model with a value-free input contract.",
            script_text=script_path.read_text(encoding="utf-8"),
            input_contract=contract,
        ),
    )
'''
replace_once(
    service,
    "\n\ndef get_model_implementation(workspace_id: str, model_version_id: str) -> ModelImplementationRead:\n",
    process1_function
    + "\n\ndef get_model_implementation(workspace_id: str, model_version_id: str) -> ModelImplementationRead:\n",
)
replace_once(
    service,
    'def _bluerev_process0_contract_path() -> Path:\n'
    '    return Path(__file__).resolve().parent / "examples" / "bluerev_geometry_hydraulics_v0.contract.json"\n'
    '\n\n'
    'def _pretty_json(canonical_payload: str) -> str:\n',
    'def _bluerev_process0_contract_path() -> Path:\n'
    '    return Path(__file__).resolve().parent / "examples" / "bluerev_geometry_hydraulics_v0.contract.json"\n'
    '\n\n'
    'def _bluerev_process1_script_path() -> Path:\n'
    '    return Path(__file__).resolve().parent / "examples" / "bluerev_biomass_nutrients_harvest_v0.py"\n'
    '\n\n'
    'def _bluerev_process1_contract_path() -> Path:\n'
    '    return (\n'
    '        Path(__file__).resolve().parent\n'
    '        / "examples"\n'
    '        / "bluerev_biomass_nutrients_harvest_v0.contract.json"\n'
    '    )\n'
    '\n\n'
    'def _pretty_json(canonical_payload: str) -> str:\n',
)

routes = "backend/app/modules/runner/routes.py"
replace_once(
    routes,
    "    register_bundled_bluerev_process0,\n    run_runner_job,\n",
    "    register_bundled_bluerev_process0,\n"
    "    register_bundled_bluerev_process1,\n"
    "    run_runner_job,\n",
)
endpoint = '''

@router.post(
    "/workspaces/{workspace_id}/bundled-models/bluerev-biomass-nutrients-harvest-v0/register",
    response_model=ModelImplementationRead,
)
def register_bundled_bluerev_process1_endpoint(
    workspace_id: str,
) -> ModelImplementationRead:
    try:
        return register_bundled_bluerev_process1(workspace_id)
    except RunnerSafetyError as exc:
        raise _runner_error(exc) from exc
'''
replace_once(
    routes,
    '\n\n@router.get("/workspaces/{workspace_id}/model-implementations", response_model=list[ModelImplementationRead])\n',
    endpoint
    + '\n\n@router.get("/workspaces/{workspace_id}/model-implementations", response_model=list[ModelImplementationRead])\n',
)

ui = "frontend/src/pages/DomainFoundation.tsx"
replace_once(
    ui,
    'type ScenarioBinding = {\n  value: string;\n  parameterId: string;\n};\n',
    'type ScenarioBinding = {\n  value: string;\n  parameterId: string;\n};\n\n'
    'const BUNDLED_PROCESS0_LABEL = "bluerev-geometry-hydraulics-v0-bundled";\n'
    'const BUNDLED_PROCESS1_LABEL = "bluerev-biomass-nutrients-harvest-v0-bundled";\n',
)
replace_once(
    ui,
    '  return response.json() as Promise<ModelImplementation>;\n}\n\nfunction DomainFoundation() {\n',
    '  return response.json() as Promise<ModelImplementation>;\n}\n\n'
    'async function registerBundledBlueRevProcess1(workspaceId: string): Promise<ModelImplementation> {\n'
    '  const response = await fetch(\n'
    '    `${API_BASE_URL}/workspaces/${workspaceId}/bundled-models/bluerev-biomass-nutrients-harvest-v0/register`,\n'
    '    {\n'
    '      method: "POST",\n'
    '      headers: { "Content-Type": "application/json" },\n'
    '      body: JSON.stringify({})\n'
    '    }\n'
    '  );\n\n'
    '  if (!response.ok) {\n'
    '    throw new Error(`Request failed with ${response.status}`);\n'
    '  }\n\n'
    '  return response.json() as Promise<ModelImplementation>;\n'
    '}\n\n'
    'function DomainFoundation() {\n',
)
replace_once(
    ui,
    '  const selectedImplementation = useMemo(\n'
    '    () => eligibleImplementations.find((item) => item.id === implementationId) ?? null,\n'
    '    [eligibleImplementations, implementationId]\n'
    '  );\n',
    '  const selectedImplementation = useMemo(\n'
    '    () => eligibleImplementations.find((item) => item.id === implementationId) ?? null,\n'
    '    [eligibleImplementations, implementationId]\n'
    '  );\n'
    '  const bundledProcess0Registered = implementations.some(\n'
    '    (item) => item.version_label === BUNDLED_PROCESS0_LABEL\n'
    '  );\n'
    '  const bundledProcess1Registered = implementations.some(\n'
    '    (item) => item.version_label === BUNDLED_PROCESS1_LABEL\n'
    '  );\n'
    '  const canRegisterBundled = !bundledProcess0Registered || !bundledProcess1Registered;\n',
)
regex_once(
    ui,
    r"  const onRegisterBundledModel = \(\) => \{.*?\n  \};\n\n  const onModelSpecSubmit",
    '''  const onRegisterBundledModels = async () => {
    setScenarioBusy(true);
    setMessage(null);
    let selectedId = "";
    try {
      if (!bundledProcess0Registered) {
        selectedId = (await registerBundledBlueRevProcess0(workspaceId)).id;
      }
      if (!bundledProcess1Registered) {
        selectedId = (await registerBundledBlueRevProcess1(workspaceId)).id;
      }
      await refreshWorkspaceRecords(workspaceId);
      if (selectedId) {
        setImplementationId(selectedId);
      }
      setMessage("Missing bundled BlueRev models registered.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setScenarioBusy(false);
    }
  };

  const onModelSpecSubmit''',
)
replace_once(
    ui,
    '        onRegisterBundled={onRegisterBundledModel}\n        result={scenarioResult}\n',
    '        onRegisterBundled={onRegisterBundledModels}\n'
    '        canRegisterBundled={canRegisterBundled}\n'
    '        result={scenarioResult}\n',
)
replace_once(
    ui,
    '  onRun,\n  onRegisterBundled,\n  result,\n',
    '  onRun,\n  onRegisterBundled,\n  canRegisterBundled,\n  result,\n',
)
replace_once(
    ui,
    '  onRun: () => void;\n  onRegisterBundled: () => void;\n  result: RunnerJobRunResponse | null;\n',
    '  onRun: () => void;\n'
    '  onRegisterBundled: () => void;\n'
    '  canRegisterBundled: boolean;\n'
    '  result: RunnerJobRunResponse | null;\n',
)
replace_once(
    ui,
    '            Register bundled BlueRev 047 model\n',
    '            Register missing bundled BlueRev models\n',
)
replace_once(
    ui,
    '        <>\n          <label className="scenario-model-select">\n',
    '        <>\n'
    '          {canRegisterBundled && (\n'
    '            <div className="scenario-empty">\n'
    '              <button type="button" className="secondary-button" disabled={busy} onClick={onRegisterBundled}>\n'
    '                Register missing bundled BlueRev models\n'
    '              </button>\n'
    '            </div>\n'
    '          )}\n'
    '          <label className="scenario-model-select">\n',
)

status = "docs/specs/STATUS.md"
replace_once(
    status,
    '| 048 | ready | — | BLUEREV-PROCESS-1: biomass, nutrients, gas, harvest, and energy/cost KPIs |',
    '| 048 | in_review | [#150](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/150) | BLUEREV-PROCESS-1: biomass, nutrients, gas, harvest, and energy/cost KPIs |',
)
