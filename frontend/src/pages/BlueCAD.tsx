import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";

import {
  archiveBluecadCandidate,
  bluecadArtifactContentUrl,
  createBluecadCandidate,
  getBluecadArtifactJson,
  listBluecadCandidates,
  listWorkspaces,
  promoteBluecadCandidate,
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
  const [showArchived, setShowArchived] = useState(false);
  const [actionCandidateId, setActionCandidateId] = useState<string | null>(null);
  const [expandedAttempts, setExpandedAttempts] = useState<Record<string, boolean>>({});
  const briefRef = useRef<HTMLTextAreaElement | null>(null);

  const visibleCandidates = useMemo(
    () => candidates.filter((candidate) => showArchived || candidate.status !== "archived"),
    [candidates, showArchived]
  );

  const selected = useMemo(
    () => visibleCandidates.find((candidate) => candidate.id === selectedId) ?? visibleCandidates[0] ?? null,
    [visibleCandidates, selectedId]
  );

  const refreshCandidates = (id: string) => {
    setLoading(true);
    return listBluecadCandidates(id)
      .then((items) => {
        setCandidates(items);
        setSelectedId((current) => {
          const visibleItems = items.filter((item) => showArchived || item.status !== "archived");
          return current && visibleItems.some((item) => item.id === current) ? current : (visibleItems[0]?.id ?? null);
        });
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

  const onArchive = (candidate: BluecadCandidate) => {
    setActionCandidateId(candidate.id);
    archiveBluecadCandidate(candidate.workspace_id, candidate.id)
      .then(() => {
        setMessage("Candidate archived.");
        return refreshCandidates(workspaceId);
      })
      .catch((error: Error) => setMessage(error.message))
      .finally(() => setActionCandidateId(null));
  };

  const onPromote = (candidate: BluecadCandidate) => {
    setActionCandidateId(candidate.id);
    promoteBluecadCandidate(candidate.workspace_id, candidate.id)
      .then((updated) => {
        setMessage(`Promoted to Decision ${updated.promoted_decision_id ?? "(pending id)"}.`);
        return refreshCandidates(workspaceId);
      })
      .catch((error: Error) => setMessage(error.message))
      .finally(() => setActionCandidateId(null));
  };

  const onRetryBrief = (candidate: BluecadCandidate) => {
    if (briefRef.current) {
      briefRef.current.value = candidate.brief_text;
      briefRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
      briefRef.current.focus();
    }
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
          <div className="bluecad-toolbar-actions">
            <label className="checkbox-line bluecad-archive-toggle">
              <input type="checkbox" checked={showArchived} onChange={(event) => setShowArchived(event.target.checked)} />
              Show archived
            </label>
            <button type="button" className="secondary-button" onClick={() => refreshCandidates(workspaceId)} disabled={loading}>
              {loading ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        </div>
        <form className="bluecad-new-form" onSubmit={onCandidateSubmit}>
          <label>
            New candidate brief
            <textarea ref={briefRef} name="brief_text" placeholder="Describe the BLUECAD part or assembly to generate." required />
          </label>
          <button type="submit" disabled={submitting}>{submitting ? "Submitting…" : "New candidate"}</button>
        </form>
      </section>

      <section className="bluecad-grid">
        <div className="panel">
          <h3>Candidates</h3>
          <div className="bluecad-candidate-list">
            {visibleCandidates.map((candidate) => (
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
            {visibleCandidates.length === 0 && <p className="panel-subtitle">No BLUECAD candidates to show.</p>}
          </div>
        </div>

        <div className="bluecad-detail">
          {selected ? (
            <>
              <section className="panel">
                <div className="bluecad-section-heading">
                  <h3>Candidate detail</h3>
                  <div className="button-row">
                    <button type="button" className="secondary-button" onClick={() => onRetryBrief(selected)}>Retry / duplicate brief</button>
                    {selected.status !== "archived" && (
                      <button type="button" className="secondary-button" onClick={() => onArchive(selected)} disabled={actionCandidateId === selected.id}>
                        {actionCandidateId === selected.id ? "Archiving…" : "Archive"}
                      </button>
                    )}
                    {selected.status === "valid" && !selected.promoted_decision_id && (
                      <button type="button" onClick={() => onPromote(selected)} disabled={actionCandidateId === selected.id}>
                        {actionCandidateId === selected.id ? "Promoting…" : "Promote to Decision"}
                      </button>
                    )}
                    {selected.promoted_decision_id && <span className="bluecad-promoted">Promoted: {selected.promoted_decision_id}</span>}
                  </div>
                </div>
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
                    <thead><tr><th>#</th><th>Route</th><th>Proposal</th><th>Build</th><th>Validation</th><th>Error detail</th><th>Started</th><th>Finished</th></tr></thead>
                    <tbody>
                      {selected.attempts.map((attempt) => {
                        const detail = parseDetailJson(attempt.error_detail_json);
                        const isExpanded = Boolean(expandedAttempts[attempt.id]);
                        return (
                          <tr key={attempt.id}>
                            <td>{attempt.attempt_no}</td>
                            <td>{attempt.route_class}</td>
                            <td>{attempt.proposal_outcome}</td>
                            <td>{attempt.build_outcome ?? "—"}</td>
                            <td>{attempt.validation_verdict ?? "—"}</td>
                            <td>
                              {detail ? (
                                <details open={isExpanded} onToggle={(event) => setExpandedAttempts((current) => ({ ...current, [attempt.id]: event.currentTarget.open }))}>
                                  <summary>Detail</summary>
                                  <pre className="bluecad-detail-json">{formatCell(detail)}</pre>
                                </details>
                              ) : "—"}
                            </td>
                            <td>{attempt.started_at}</td>
                            <td>{attempt.finished_at ?? "—"}</td>
                          </tr>
                        );
                      })}
                      {selected.attempts.length === 0 && <tr><td colSpan={8}>No attempts recorded yet.</td></tr>}
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

function parseDetailJson(value?: string | null): unknown | null {
  if (!value) return null;
  try {
    return JSON.parse(value) as unknown;
  } catch {
    return value;
  }
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatPercent(value: unknown): string | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return `${(value * 100).toPrecision(3)}%`;
}

function formatValidationDetail(value: unknown): string {
  if (!isRecord(value)) return formatCell(value);

  if ("actual" in value && "declared" in value) {
    const relErr = formatPercent(value.rel_err);
    const relTol = formatPercent(value.rel_tol);
    const tolerance = relTol ? ` / tol ${relTol}` : "";
    const error = relErr ? ` (rel err ${relErr}${tolerance})` : "";
    return `actual ${formatCell(value.actual)} vs declared ${formatCell(value.declared)}${error}`;
  }

  return formatCell(value);
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
              <td>{formatCell(check.tier) || "—"}</td>
              <td>{check.status ?? check.verdict ?? "—"}</td>
              <td>{formatValidationDetail(check.detail ?? check.message) || "—"}</td>
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
