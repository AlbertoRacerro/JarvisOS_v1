import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import {
  createAssumption,
  createDecision,
  createModelSpec,
  createParameter,
  createSimulationRun,
  createWorkspace,
  initializeSystem,
  listAssumptions,
  listDecisions,
  listModelSpecs,
  listParameters,
  listSimulationRuns,
  listWorkspaces,
  type Assumption,
  type Decision,
  type ModelSpec,
  type Parameter,
  type SimulationRun,
  type Workspace
} from "../api/client";

function DomainFoundation() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState("bluerev");
  const [modelSpecs, setModelSpecs] = useState<ModelSpec[]>([]);
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [runs, setRuns] = useState<SimulationRun[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [message, setMessage] = useState<string | null>(null);

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

  const onModelSpecSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    createModelSpec(workspaceId, {
      title: String(form.get("title") ?? ""),
      engineering_question: String(form.get("engineering_question") ?? ""),
      scope: String(form.get("scope") ?? "")
    }).then(() => {
      event.currentTarget.reset();
      return refreshWorkspaceRecords(workspaceId);
    }).catch((error: Error) => setMessage(error.message));
  };

  const onAssumptionSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const statement = String(new FormData(event.currentTarget).get("statement") ?? "");
    createAssumption(workspaceId, { statement }).then(() => {
      event.currentTarget.reset();
      return refreshWorkspaceRecords(workspaceId);
    }).catch((error: Error) => setMessage(error.message));
  };

  const onParameterSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    createParameter(workspaceId, {
      name: String(form.get("name") ?? ""),
      symbol: String(form.get("symbol") ?? ""),
      value: String(form.get("value") ?? ""),
      unit: String(form.get("unit") ?? "")
    }).then(() => {
      event.currentTarget.reset();
      return refreshWorkspaceRecords(workspaceId);
    }).catch((error: Error) => setMessage(error.message));
  };

  const onRunSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const runLabel = String(new FormData(event.currentTarget).get("run_label") ?? "");
    createSimulationRun(workspaceId, { run_label: runLabel, status: "planned" }).then(() => {
      event.currentTarget.reset();
      return refreshWorkspaceRecords(workspaceId);
    }).catch((error: Error) => setMessage(error.message));
  };

  const onDecisionSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    createDecision(workspaceId, {
      title: String(form.get("title") ?? ""),
      decision_text: String(form.get("decision_text") ?? "")
    }).then(() => {
      event.currentTarget.reset();
      return refreshWorkspaceRecords(workspaceId);
    }).catch((error: Error) => setMessage(error.message));
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

        <RecordPanel title="Parameters" items={parameters.map((item) => `${item.symbol ?? item.name}: ${item.value ?? ""} ${item.unit ?? ""}`)}>
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
