import { useEffect, useState } from "react";

import { getHealth, type HealthResponse } from "../api/client";

function Dashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((caught: Error) => setError(caught.message));
  }, []);

  return (
    <section className="page">
      <div className="page-header">
        <p className="eyebrow">Milestone 0B</p>
        <h2>Core Domain Foundation</h2>
      </div>

      <div className="status-grid">
        <article className="metric-card">
          <span className="metric-label">Backend</span>
          <strong>{health?.status ?? (error ? "offline" : "checking")}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">Environment</span>
          <strong>{health?.environment ?? "local"}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">Version</span>
          <strong>{health?.version ?? "0.1.0"}</strong>
        </article>
      </div>

      <section className="panel">
        <h3>Foundation Scope</h3>
        <div className="scope-list">
          <span>FastAPI backend</span>
          <span>React TypeScript frontend</span>
          <span>SQLite-ready data layer</span>
          <span>Budget-guarded AI gateway</span>
          <span>Workspace records</span>
          <span>Modeling records</span>
          <span>Creation event log</span>
          <span>Fake AI draft provider</span>
        </div>
      </section>
    </section>
  );
}

export default Dashboard;
