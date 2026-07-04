import { type FormEvent, useEffect, useMemo, useState } from "react";

import {
  bluecadArtifactContentUrl,
  createBluecadCandidate,
  getBluecadArtifactJson,
  listBluecadCandidates,
  listWorkspaces,
  type BluecadCandidate,
  type BluecadValidationCheck,
  type Workspace
} from "../api/client";
import BluecadGlbViewer from "../components/BluecadGlbViewer";

type ValidationReport = {
  checks?: BluecadValidationCheck[];
  validation?: { checks?: BluecadValidationCheck[] };
};

function BlueCAD() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState("bluerev");
  const [candidates, setCandidates] = useState<BluecadCandidate[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [checks, setChecks] = useState<BluecadValidationCheck[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const selected = useMemo(
    () => candidates.find((candidate) => candidate.id === selectedId) ?? candidates[0] ?? null,
    [candidates, selectedId]
  );

  const refreshCandidates = (id: string) => {
    setLoading(true);
    return listBluecadCandidates(id)
      .then((items) => {
        setCandidates(items);
        setSelectedId((current) => (current && items.some((item) => item.id === current) ? current : (items[0]?.id ?? null)));
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    listWorkspaces()
      .then((items) => {
        setWorkspaces(items);
        if (items.length > 0 && !items.some((item) => item.id === workspaceId)) {
          setWorkspaceId(items[0].id);
        }
      })
      .catch((error: Error) => setMessage(`Storage may need initialization: ${error.message}`));
  }, []);

  useEffect(() => {
    if (workspaceId) {
      refreshCandidates(workspaceId).catch((error: Error) => setMessage(error.message));
    }
  }, [workspaceId]);

  useEffect(() => {
    setChecks([]);
    if (!selected?.report_artifact_id) return;
    getBluecadArtifactJson<ValidationReport>(selected.workspace_id, selected.report_artifact_id)
      .then((report) => setChecks(report.checks ?? report.validation?.checks ?? []))
      .catch((error: Error) => setMessage(`Validation report unavailable: ${error.message}`));
  }, [selected?.id, selected?.report_artifact_id, selected?.workspace_id]);

  const onCandidateSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const briefText = String(new FormData(form).get("brief_text") ?? "").trim();
    if (!briefText) return;
    setSubmitting(true);
    createBluecadCandidate(workspaceId, briefText)
      .then((candidate) => {
        form.reset();
        setSelectedId(candidate.id);
        setMessage("BLUECAD candidate requested.");
        return refreshCandidates(workspaceId);
      })
      .catch((error: Error) => setMessage(error.message))
      .finally(() => setSubmitting(false));
  };

  return (
    <section className="page bluecad-page">
      <div className="page-header">
        <p className="eyebrow">BLUECAD</p>
        <h2>Workbench</h2>
      </div>

      {message && <div className="error-banner">{message}</div>}

      <section className="panel">
        <div className="bluecad-toolbar">
          <label>
            Workspace
            <select value={workspaceId} onChange={(event) => setWorkspaceId(event.target.value)}>
              {workspaces.map((workspace) => (
                <option key={workspace.id} value={workspace.id}>
                  {workspace.name}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="secondary-button" onClick={() => refreshCandidates(workspaceId)} disabled={loading}>
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>
        <form className="bluecad-new-form" onSubmit={onCandidateSubmit}>
          <label>
            New candidate brief
            <textarea name="brief_text" placeholder="Describe the BLUECAD part or assembly to generate." required />
          </label>
          <button type="submit" disabled={submitting}>{submitting ? "Submitting…" : "New candidate"}</button>
        </form>
      </section>

      <section className="bluecad-grid">
        <div className="panel">
          <h3>Candidates</h3>
          <div className="bluecad-candidate-list">
            {candidates.map((candidate) => (
              <button
                key={candidate.id}
                type="button"
                className={candidate.id === selected?.id ? "bluecad-candidate active" : "bluecad-candidate"}
                onClick={() => setSelectedId(candidate.id)}
              >
                <span className={`status-pill status-${candidate.status}`}>{candidate.status}</span>
                {candidate.parked_reason && <span className="parked-reason">Parked: {candidate.parked_reason}</span>}
                <strong>{candidate.brief_text.slice(0, 120)}{candidate.brief_text.length > 120 ? "…" : ""}</strong>
                <small>{candidate.created_at}</small>
              </button>
            ))}
            {candidates.length === 0 && <p className="panel-subtitle">No BLUECAD candidates yet.</p>}
          </div>
        </div>

        <div className="bluecad-detail">
          {selected ? (
            <>
              <section className="panel">
                <h3>Candidate detail</h3>
                {selected.parked_reason && <div className="warning-banner">Parked reason: {selected.parked_reason}</div>}
                <dl className="details">
                  <div><dt>ID</dt><dd>{selected.id}</dd></div>
                  <div><dt>Status</dt><dd>{selected.status}</dd></div>
                  <div><dt>Brief</dt><dd>{selected.brief_text}</dd></div>
                  <div><dt>Updated</dt><dd>{selected.updated_at}</dd></div>
                </dl>
              </section>

              <section className="panel">
                <h3>3D GLB viewer</h3>
                {selected.glb_artifact_id ? (
                  <BluecadGlbViewer artifactUrl={bluecadArtifactContentUrl(selected.workspace_id, selected.glb_artifact_id)} />
                ) : (
                  <p className="panel-subtitle">No GLB artifact is available for this candidate yet.</p>
                )}
              </section>

              <section className="panel">
                <h3>Validation report</h3>
                <ReportTable checks={checks} />
              </section>

              <section className="panel">
                <h3>Attempt history</h3>
                <div className="table-wrap">
                  <table className="smoke-table bluecad-table">
                    <thead><tr><th>#</th><th>Route</th><th>Proposal</th><th>Build</th><th>Validation</th><th>Started</th><th>Finished</th></tr></thead>
                    <tbody>
                      {selected.attempts.map((attempt) => (
                        <tr key={attempt.id}>
                          <td>{attempt.attempt_no}</td>
                          <td>{attempt.route_class}</td>
                          <td>{attempt.proposal_outcome}</td>
                          <td>{attempt.build_outcome ?? "—"}</td>
                          <td>{attempt.validation_verdict ?? "—"}</td>
                          <td>{attempt.started_at}</td>
                          <td>{attempt.finished_at ?? "—"}</td>
                        </tr>
                      ))}
                      {selected.attempts.length === 0 && <tr><td colSpan={7}>No attempts recorded yet.</td></tr>}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          ) : (
            <section className="panel"><p className="panel-subtitle">Select a candidate to inspect validation and attempt history.</p></section>
          )}
        </div>
      </section>
    </section>
  );
}

function ReportTable({ checks }: { checks: BluecadValidationCheck[] }) {
  return (
    <div className="table-wrap">
      <table className="smoke-table bluecad-table">
        <thead><tr><th>Check ID</th><th>Tier</th><th>Status</th><th>Detail</th><th>Hint</th></tr></thead>
        <tbody>
          {checks.map((check, index) => (
            <tr key={`${check.id ?? check.check_id ?? "check"}-${index}`}>
              <td>{check.id ?? check.check_id ?? `check-${index + 1}`}</td>
              <td>{check.tier ?? "—"}</td>
              <td>{check.status ?? check.verdict ?? "—"}</td>
              <td>{check.detail ?? check.message ?? "—"}</td>
              <td>{check.hint ?? "—"}</td>
            </tr>
          ))}
          {checks.length === 0 && <tr><td colSpan={5}>No validation checks available.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

export default BlueCAD;
