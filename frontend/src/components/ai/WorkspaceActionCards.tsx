import { useState } from "react";
import type { ActionOutcome } from "../../api/workspaceActions";
import { actionOriginLabel, actionStatePresentation, actionSummaryText } from "./workspaceActionPresentation";

type Props = { actions: ActionOutcome[]; onApply(actionId: string): Promise<void>; onDismiss(actionId: string): Promise<void>; onUndo(actionId: string): Promise<void>; technicalDetails?: string | null; technicalInfo?: unknown };

function studioProposal(action: ActionOutcome) {
  if (action.surface !== "studio") return null;
  const item = Array.isArray(action.request.actions) ? action.request.actions[0] : null;
  if (!item || typeof item !== "object") return null;
  const proposal = item as Record<string, unknown>;
  if (proposal.op !== "studio_draft") return null;
  const contract = proposal.contract && typeof proposal.contract === "object" ? proposal.contract as Record<string, unknown> : {};
  const fields = Object.entries(contract).filter(([, value]) => Array.isArray(value));
  const source = typeof proposal.source === "string" ? proposal.source : "";
  const assumptions = typeof proposal.assumptions === "string" ? proposal.assumptions : "";
  const sourceChange = action.changes.find((change) => change.label.toLowerCase().includes("source"));
  const diff = sourceChange?.before ? `--- Current Python\n+++ Proposed Python\n${sourceChange.before.split("\n").map((line) => `- ${line}`).join("\n")}\n${source.split("\n").map((line) => `+ ${line}`).join("\n")}` : `+++ Proposed Python\n${source.split("\n").map((line) => `+ ${line}`).join("\n")}`;
  return <div className="jarvis-studio-proposal">
    <p><strong>{String(proposal.name ?? "Studio draft")}</strong> · {String(proposal.category ?? "unknown")} · {proposal.mode === "update" ? "update selected draft" : "new draft"}</p>
    {typeof proposal.engineering_question === "string" ? <p>{proposal.engineering_question}</p> : null}
    <div><strong>Engineering contract</strong>{fields.length ? fields.map(([title, rows]) => <section key={title}><h4>{title.replace(/_/g, " ")}</h4><ul>{(rows as unknown[]).map((row, index) => {
      const record = row && typeof row === "object" ? row as Record<string, unknown> : {};
      return <li key={index}><strong>{String(record.label ?? record.name ?? `Item ${index + 1}`)}</strong>{record.name && record.label ? ` (${String(record.name)})` : ""}{record.unit ? ` [${String(record.unit)}]` : ""}{record.description ? ` — ${String(record.description)}` : ""}{record.min != null || record.max != null ? ` · bounds ${String(record.min ?? "−∞")}…${String(record.max ?? "+∞")}` : ""}</li>;
    })}</ul></section>) : <p>Review the proposed contract in technical details.</p>}</div>
    <div><strong>Assumptions and limits</strong><p>{assumptions || "No assumptions supplied. Review the model before testing."}</p><p>Apply creates a draft only. Test and Publish remain separate actions; scientific status is unqualified.</p></div>
    <details><summary>Python source diff</summary><pre>{diff}</pre></details>
  </div>;
}

export default function WorkspaceActionCards({ actions, onApply, onDismiss, onUndo, technicalDetails, technicalInfo }: Props) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const run = async (id: string, fn: (actionId: string) => Promise<void>) => {
    setBusyId(id);
    try { await fn(id); } finally { setBusyId(null); }
  };
  if (!actions.length && !technicalDetails && !technicalInfo) return null;
  const details = [
    technicalDetails,
    actions.length ? JSON.stringify(actions.map(({ request, request_digest, origin, result_revision }) => ({ request, request_digest, origin, result_revision })), null, 2) : null,
    technicalInfo ? JSON.stringify(technicalInfo, null, 2) : null
  ].filter(Boolean).join("\n\n");
  return <div className="jarvis-action-list">
    {actions.map((action) => {
      const presentation = actionStatePresentation(action.state);
      return <section className={`jarvis-action-card jarvis-action-card--${presentation.tone}`} key={action.action_id} aria-label={`${presentation.label} workspace action`}>
        <header><strong>{presentation.label}</strong><span>{actionOriginLabel(action.origin)}</span></header>
        <p>{actionSummaryText(action)}</p>
        {studioProposal(action)}
        {action.surface !== "studio" && action.changes.length > 0 && <ul>{action.changes.map((change, index) => <li key={`${change.label}-${index}`}><strong>{change.label}</strong>: {change.before ? `${change.before} → ` : ""}{change.after ?? "—"}</li>)}</ul>}
        {(action.state === "refused" || action.state === "stale") && action.reason && <p className="jarvis-action-card__reason">{action.reason}</p>}
        {action.state === "proposed" && <div className="jarvis-action-card__buttons"><button type="button" className="jarvis-primary-button" disabled={busyId === action.action_id} aria-label={`Apply ${actionSummaryText(action)}`} onClick={() => void run(action.action_id, onApply)}>Apply</button><button type="button" className="jarvis-link-button" disabled={busyId === action.action_id} aria-label={`Dismiss ${actionSummaryText(action)}`} onClick={() => void run(action.action_id, onDismiss)}>Dismiss</button></div>}
        {action.state === "applied" && action.undo_available && <button type="button" className="jarvis-link-button" disabled={busyId === action.action_id} aria-label={`Undo ${actionSummaryText(action)}`} onClick={() => void run(action.action_id, onUndo)}>Undo</button>}
        {action.state === "applied" && action.result_revision && <small>Revision {action.result_revision.split(":", 1)[0]}</small>}
      </section>;
    })}
    {Boolean(details) && <details className="jarvis-action-technical"><summary>Technical details</summary><pre>{details}</pre></details>}
  </div>;
}
