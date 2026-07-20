import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";

import {
  API_BASE_URL,
  createAssumption,
  createDecision,
  createModelSpec,
  createParameter,
  createRunnerJob,
  createSimulationRun,
  createWorkspace,
  initializeSystem,
  listAssumptions,
  listDecisions,
  listModelImplementations,
  listModelSpecs,
  listParameters,
  listSimulationRuns,
  listWorkspaces,
  previewModelBindings,
  runRunnerJob,
  type Assumption,
  type BindingPreviewResponse,
  type Decision,
  type ModelImplementation,
  type ModelInputVariable,
  type ModelSpec,
  type Parameter,
  type RunnerJobRunResponse,
  type SimulationRun,
  type Workspace
} from "../api/client";

type ScenarioBinding = {
  value: string;
  parameterId: string;
};

const BUNDLED_PROCESS0_LABEL = "bluerev-geometry-hydraulics-v0-bundled";
const BUNDLED_PROCESS1_LABEL = "bluerev-biomass-nutrients-harvest-v0-bundled";
const BUNDLED_PROCESS2_LABEL = "bluerev-buoyancy-optical-screening-v0-bundled";

async function registerBundledBlueRevProcess0(workspaceId: string): Promise<ModelImplementation> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/bundled-models/bluerev-geometry-hydraulics-v0/register`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    }
  );

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return response.json() as Promise<ModelImplementation>;
}

async function registerBundledBlueRevProcess1(workspaceId: string): Promise<ModelImplementation> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/bundled-models/bluerev-biomass-nutrients-harvest-v0/register`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    }
  );

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return response.json() as Promise<ModelImplementation>;
}


async function registerBundledBlueRevProcess2(workspaceId: string): Promise<ModelImplementation> {
  const response = await fetch(
    `${API_BASE_URL}/workspaces/${workspaceId}/bundled-models/bluerev-buoyancy-optical-screening-v0/register`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    }
  );

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return response.json() as Promise<ModelImplementation>;
}

function DomainFoundation() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState("bluerev");
  const [modelSpecs, setModelSpecs] = useState<ModelSpec[]>([]);
  const [implementations, setImplementations] = useState<ModelImplementation[]>([]);
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [runs, setRuns] = useState<SimulationRun[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [implementationId, setImplementationId] = useState("");
  const [scenarioBindings, setScenarioBindings] = useState<Record<string, ScenarioBinding>>({});
  const [preview, setPreview] = useState<BindingPreviewResponse | null>(null);
  const [runLabel, setRunLabel] = useState("");
  const [scenarioResult, setScenarioResult] = useState<RunnerJobRunResponse | null>(null);
  const [scenarioBusy, setScenarioBusy] = useState(false);

  const eligibleImplementations = useMemo(
    () => implementations.filter((item) => item.input_contract?.variables.length),
    [implementations]
  );
  const selectedImplementation = useMemo(
    () => eligibleImplementations.find((item) => item.id === implementationId) ?? null,
    [eligibleImplementations, implementationId]
  );
  const bundledProcess0Registered = implementations.some(
    (item) => item.version_label === BUNDLED_PROCESS0_LABEL
  );
  const bundledProcess1Registered = implementations.some(
    (item) => item.version_label === BUNDLED_PROCESS1_LABEL
  );
  const bundledProcess2Registered = implementations.some(
    (item) => item.version_label === BUNDLED_PROCESS2_LABEL
  );
  const canRegisterBundled =
    !bundledProcess0Registered || !bundledProcess1Registered || !bundledProcess2Registered;

  const refreshWorkspaces = () =>
    listWorkspaces().then((items) => {
      setWorkspaces(items);
      if (items.length > 0 && !items.some((item) => item.id === workspaceId)) {
        setWorkspaceId(items[0].id);
      }
    });

  const refreshWorkspaceRecords = (id: string) =>
    Promise.all([
      listModelSpecs(id).then(setModelSpecs),
      listModelImplementations(id).then(setImplementations),
      listAssumptions(id).then(setAssumptions),
      listParameters(id).then(setParameters),
      listSimulationRuns(id).then(setRuns),
      listDecisions(id).then(setDecisions)
    ]);

  useEffect(() => {
    refreshWorkspaces().catch((error: Error) => setMessage(`Storage may need initialization: ${error.message}`));
  }, []);

  useEffect(() => {
    if (workspaceId) {
      refreshWorkspaceRecords(workspaceId).catch((error: Error) => setMessage(error.message));
    }
  }, [workspaceId]);

  useEffect(() => {
    if (!eligibleImplementations.some((item) => item.id === implementationId)) {
      setImplementationId(eligibleImplementations[0]?.id ?? "");
    }
  }, [eligibleImplementations, implementationId]);

  useEffect(() => {
    const variables = selectedImplementation?.input_contract?.variables ?? [];
    setScenarioBindings(
      Object.fromEntries(variables.map((variable) => [variable.name, { value: "", parameterId: "" }]))
    );
    setPreview(null);
    setScenarioResult(null);
    setRunLabel("");
  }, [selectedImplementation?.id]);

  const onWorkspaceSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    createWorkspace({
      name: String(form.get("name") ?? ""),
      slug: String(form.get("slug") ?? ""),
      description: String(form.get("description") ?? "")
    })
      .then((workspace) => {
        event.currentTarget.reset();
        setWorkspaceId(workspace.id);
        return refreshWorkspaces();
      })
      .catch((error: Error) => setMessage(error.message));
  };

  const onInitializeClick = () => {
    initializeSystem()
      .then(() => {
        setMessage("Storage initialized and BlueRev workspace is available.");
        return refreshWorkspaces();
      })
      .catch((error: Error) => setMessage(error.message));
  };

  const onRegisterBundledModels = async () => {
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
      if (!bundledProcess2Registered) {
        selectedId = (await registerBundledBlueRevProcess2(workspaceId)).id;
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

  const onModelSpecSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    createModelSpec(workspaceId, {
      title: String(form.get("title") ?? ""),
      engineering_question: String(form.get("engineering_question") ?? ""),
      scope: String(form.get("scope") ?? "")
    })
      .then(() => {
        event.currentTarget.reset();
        return refreshWorkspaceRecords(workspaceId);
      })
      .catch((error: Error) => setMessage(error.message));
  };

  const onAssumptionSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const statement = String(new FormData(event.currentTarget).get("statement") ?? "");
    createAssumption(workspaceId, { statement })
      .then(() => {
        event.currentTarget.reset();
        return refreshWorkspaceRecords(workspaceId);
      })
      .catch((error: Error) => setMessage(error.message));
  };

  const onParameterSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    createParameter(workspaceId, {
      name: String(form.get("name") ?? ""),
      symbol: String(form.get("symbol") ?? ""),
      value: String(form.get("value") ?? ""),
      unit: String(form.get("unit") ?? "")
    })
      .then(() => {
        event.currentTarget.reset();
        return refreshWorkspaceRecords(workspaceId);
      })
      .catch((error: Error) => setMessage(error.message));
  };

  const onRunSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const runLabelValue = String(new FormData(event.currentTarget).get("run_label") ?? "");
    createSimulationRun(workspaceId, { run_label: runLabelValue, status: "planned" })
      .then(() => {
        event.currentTarget.reset();
        return refreshWorkspaceRecords(workspaceId);
      })
      .catch((error: Error) => setMessage(error.message));
  };

  const onDecisionSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    createDecision(workspaceId, {
      title: String(form.get("title") ?? ""),
      decision_text: String(form.get("decision_text") ?? "")
    })
      .then(() => {
        event.currentTarget.reset();
        return refreshWorkspaceRecords(workspaceId);
      })
      .catch((error: Error) => setMessage(error.message));
  };

  const updateScenarioBinding = (name: string, next: ScenarioBinding) => {
    setScenarioBindings((current) => ({ ...current, [name]: next }));
    setPreview(null);
    setScenarioResult(null);
  };

  const onParameterBindingChange = (variable: ModelInputVariable, parameterId: string) => {
    const parameter = parameters.find((item) => item.id === parameterId);
    updateScenarioBinding(variable.name, {
      parameterId,
      value: parameter?.value ?? scenarioBindings[variable.name]?.value ?? ""
    });
  };

  const buildBindingPayload = () => {
    const variables = selectedImplementation?.input_contract?.variables ?? [];
    return Object.fromEntries(
      variables.flatMap((variable) => {
        const binding = scenarioBindings[variable.name];
        if (!binding || binding.value.trim() === "") {
          return [];
        }
        const item: Record<string, unknown> = {
          value: Number(binding.value),
          unit: variable.unit
        };
        if (binding.parameterId) {
          item.source_parameter_id = binding.parameterId;
        }
        return [[variable.name, item]];
      })
    );
  };

  const onPreviewScenario = () => {
    if (!selectedImplementation) {
      return;
    }
    setScenarioBusy(true);
    setMessage(null);
    previewModelBindings(workspaceId, selectedImplementation.id, buildBindingPayload())
      .then(setPreview)
      .catch((error: Error) => setMessage(error.message))
      .finally(() => setScenarioBusy(false));
  };

  const onRunScenario = () => {
    if (!selectedImplementation || preview?.state !== "ready" || !preview.normalized_input_set || !runLabel.trim()) {
      return;
    }
    setScenarioBusy(true);
    setMessage(null);
    createRunnerJob(workspaceId, {
      model_version_id: selectedImplementation.id,
      run_label: runLabel.trim(),
      input_set: preview.normalized_input_set
    })
      .then((created) => runRunnerJob(created.runner_job.id))
      .then((result) => {
        setScenarioResult(result);
        return refreshWorkspaceRecords(workspaceId);
      })
      .catch((error: Error) => setMessage(error.message))
      .finally(() => setScenarioBusy(false));
  };

  return (
    <section className="page">
      <div className="page-header">
        <p className="eyebrow">Persistent Core</p>
        <h2>Domain Foundation</h2>
      </div>

      {message && <div className="error-banner">{message}</div>}

      <section className="panel">
        <h3>Workspace</h3>
        <div className="foundation-toolbar">
          <button type="button" onClick={onInitializeClick}>
            Initialize Storage
          </button>
          <select value={workspaceId} onChange={(event) => setWorkspaceId(event.target.value)}>
            {workspaces.map((workspace) => (
              <option key={workspace.id} value={workspace.id}>
                {workspace.name}
              </option>
            ))}
          </select>
        </div>
        <form className="compact-form" onSubmit={onWorkspaceSubmit}>
          <input name="name" placeholder="Workspace name" required />
          <input name="slug" placeholder="slug" required />
          <input name="description" placeholder="description" />
          <button type="submit">Create</button>
        </form>
      </section>

      <ScenarioPanel
        implementations={eligibleImplementations}
        selected={selectedImplementation}
        implementationId={implementationId}
        onImplementationChange={setImplementationId}
        parameters={parameters}
        bindings={scenarioBindings}
        onBindingChange={updateScenarioBinding}
        onParameterChange={onParameterBindingChange}
        preview={preview}
        onPreview={onPreviewScenario}
        runLabel={runLabel}
        onRunLabelChange={setRunLabel}
        onRun={onRunScenario}
        onRegisterBundled={onRegisterBundledModels}
        canRegisterBundled={canRegisterBundled}
        result={scenarioResult}
        busy={scenarioBusy}
      />

      <section className="foundation-grid">
        <RecordPanel title="Model Specs" items={modelSpecs.map((item) => item.title)}>
          <form className="compact-form" onSubmit={onModelSpecSubmit}>
            <input name="title" placeholder="Title" required />
            <input name="engineering_question" placeholder="Engineering question" required />
            <input name="scope" placeholder="Scope" />
            <button type="submit">Create</button>
          </form>
        </RecordPanel>

        <RecordPanel title="Assumptions" items={assumptions.map((item) => item.statement)}>
          <form className="compact-form" onSubmit={onAssumptionSubmit}>
            <input name="statement" placeholder="Assumption statement" required />
            <button type="submit">Create</button>
          </form>
        </RecordPanel>

        <RecordPanel
          title="Parameters"
          items={parameters.map((item) => `${item.symbol ?? item.name}: ${item.value ?? ""} ${item.unit ?? ""}`)}
        >
          <form className="compact-form" onSubmit={onParameterSubmit}>
            <input name="name" placeholder="Name" required />
            <input name="symbol" placeholder="Symbol" />
            <input name="value" placeholder="Value" />
            <input name="unit" placeholder="Unit" />
            <button type="submit">Create</button>
          </form>
        </RecordPanel>

        <RecordPanel title="Simulation Runs" items={runs.map((item) => item.run_label ?? item.id)}>
          <form className="compact-form" onSubmit={onRunSubmit}>
            <input name="run_label" placeholder="Run label" />
            <button type="submit">Create</button>
          </form>
        </RecordPanel>

        <RecordPanel title="Decisions" items={decisions.map((item) => item.title)}>
          <form className="compact-form" onSubmit={onDecisionSubmit}>
            <input name="title" placeholder="Title" required />
            <input name="decision_text" placeholder="Decision" required />
            <button type="submit">Create</button>
          </form>
        </RecordPanel>
      </section>
    </section>
  );
}

function ScenarioPanel({
  implementations,
  selected,
  implementationId,
  onImplementationChange,
  parameters,
  bindings,
  onBindingChange,
  onParameterChange,
  preview,
  onPreview,
  runLabel,
  onRunLabelChange,
  onRun,
  onRegisterBundled,
  canRegisterBundled,
  result,
  busy
}: {
  implementations: ModelImplementation[];
  selected: ModelImplementation | null;
  implementationId: string;
  onImplementationChange: (value: string) => void;
  parameters: Parameter[];
  bindings: Record<string, ScenarioBinding>;
  onBindingChange: (name: string, value: ScenarioBinding) => void;
  onParameterChange: (variable: ModelInputVariable, parameterId: string) => void;
  preview: BindingPreviewResponse | null;
  onPreview: () => void;
  runLabel: string;
  onRunLabelChange: (value: string) => void;
  onRun: () => void;
  onRegisterBundled: () => void;
  canRegisterBundled: boolean;
  result: RunnerJobRunResponse | null;
  busy: boolean;
}) {
  const variables = selected?.input_contract?.variables ?? [];
  const outputs = result?.output?.outputs ?? {};
  return (
    <section className="panel scenario-panel">
      <h3>Model scenario</h3>
      <p className="panel-subtitle">
        Bind editable project values, inspect forward degrees of freedom, then create an immutable simulation run.
      </p>
      {implementations.length === 0 ? (
        <div className="scenario-empty">
          <p>No reviewed model implementation exposes an input contract yet.</p>
          <button type="button" className="secondary-button" disabled={busy} onClick={onRegisterBundled}>
            Register missing bundled BlueRev models
          </button>
        </div>
      ) : (
        <>
          {canRegisterBundled && (
            <div className="scenario-empty">
              <button type="button" className="secondary-button" disabled={busy} onClick={onRegisterBundled}>
                Register missing bundled BlueRev models
              </button>
            </div>
          )}
          <label className="scenario-model-select">
            Model implementation
            <select value={implementationId} onChange={(event) => onImplementationChange(event.target.value)}>
              {implementations.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.version_label}
                </option>
              ))}
            </select>
          </label>
          <div className="scenario-variable-list">
            {variables.map((variable) => {
              const binding = bindings[variable.name] ?? { value: "", parameterId: "" };
              const compatible = parameters.filter(
                (parameter) =>
                  parameter.unit === variable.unit &&
                  parameter.value != null &&
                  Number.isFinite(Number(parameter.value))
              );
              const variablePreview = preview?.variables.find((item) => item.name === variable.name);
              return (
                <div className="scenario-variable" key={variable.name}>
                  <div>
                    <strong>{variable.label}</strong>
                    <span>{variable.category}</span>
                    <small>{variable.description}</small>
                  </div>
                  <label>
                    Value [{variable.unit}]
                    <input
                      type="number"
                      step="any"
                      value={binding.value}
                      onChange={(event) =>
                        onBindingChange(variable.name, { ...binding, value: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    Source
                    <select
                      value={binding.parameterId}
                      onChange={(event) => onParameterChange(variable, event.target.value)}
                    >
                      <option value="">Manual scenario override</option>
                      {compatible.map((parameter) => (
                        <option key={parameter.id} value={parameter.id}>
                          {parameter.name}: {parameter.value} {parameter.unit}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className={`binding-state ${variablePreview?.binding_state ?? "missing"}`}>
                    {variablePreview?.binding_state ?? "not previewed"}
                    {variablePreview?.errors.map((error) => <span key={error}>{error}</span>)}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="scenario-actions">
            <button type="button" className="secondary-button" disabled={busy} onClick={onPreview}>
              Preview bindings
            </button>
            <label>
              Run label
              <input value={runLabel} onChange={(event) => onRunLabelChange(event.target.value)} />
            </label>
            <button
              type="button"
              disabled={busy || preview?.state !== "ready" || !runLabel.trim()}
              onClick={onRun}
            >
              Run scenario
            </button>
          </div>
          <div className="dof-strip" aria-label="Degree of freedom summary">
            <span>Structural: {preview?.structural_input_dof ?? variables.filter((item) => item.required).length}</span>
            <span>Bound: {preview?.bound_input_dof ?? 0}</span>
            <span>Unresolved: {preview?.unresolved_input_dof ?? variables.filter((item) => item.required).length}</span>
            <span>Invalid: {preview?.invalid_binding_count ?? 0}</span>
            <strong>State: {preview?.state ?? "not previewed"}</strong>
          </div>
          {result && (
            <div className="scenario-result">
              <h4>Run {result.simulation_run.run_label ?? result.simulation_run.id}</h4>
              <p>Status: {result.runner_job.status}</p>
              {result.error && (
                <div className="error-banner">
                  {result.error.code}: {result.error.message}
                </div>
              )}
              <dl className="scenario-output-list">
                {Object.entries(outputs).map(([name, output]) => (
                  <div key={name}>
                    <dt>{name}</dt>
                    <dd>
                      {String(output.value)} {output.unit}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </>
      )}
    </section>
  );
}

function RecordPanel({ title, items, children }: { title: string; items: string[]; children: ReactNode }) {
  return (
    <section className="panel record-panel">
      <h3>{title}</h3>
      {children}
      <ul className="record-list">
        {items.length === 0 && <li>No records yet.</li>}
        {items.map((item, index) => (
          <li key={`${item}-${index}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export default DomainFoundation;
