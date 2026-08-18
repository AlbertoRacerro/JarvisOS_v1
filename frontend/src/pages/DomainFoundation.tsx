import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import {
  API_BASE_URL,
  createAssumption,
  createDecision,
  createModelSpec,
  createParameter,
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
  type Assumption,
  type Decision,
  type ModelImplementation,
  type ModelSpec,
  type Parameter,
  type SimulationRun,
  type Workspace
} from "../api/client";

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
  const [registrationBusy, setRegistrationBusy] = useState(false);

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
    setRegistrationBusy(true);
    setMessage(null);
    try {
      if (!bundledProcess0Registered) {
        await registerBundledBlueRevProcess0(workspaceId);
      }
      if (!bundledProcess1Registered) {
        await registerBundledBlueRevProcess1(workspaceId);
      }
      if (!bundledProcess2Registered) {
        await registerBundledBlueRevProcess2(workspaceId);
      }
      await refreshWorkspaceRecords(workspaceId);
      setMessage("Missing bundled BlueRev models registered.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setRegistrationBusy(false);
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

      <section className="panel scenario-panel">
        <h3>Model implementations</h3>
        <p className="panel-subtitle">
          Scenario editing, deterministic preflight, and execution now live in the shared Properties sidecar so there is only one editable working configuration.
        </p>
        {canRegisterBundled ? (
          <button type="button" className="secondary-button" disabled={registrationBusy} onClick={onRegisterBundledModels}>
            Register missing bundled BlueRev models
          </button>
        ) : (
          <p>Bundled BlueRev model implementations are registered.</p>
        )}
        <ul className="record-list">
          {implementations.length === 0 && <li>No model implementations yet.</li>}
          {implementations.map((item) => <li key={item.id}>{item.version_label}</li>)}
        </ul>
      </section>

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