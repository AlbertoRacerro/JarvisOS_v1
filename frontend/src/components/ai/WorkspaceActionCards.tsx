import { useState } from "react";
import type { ActionOutcome } from "../../api/workspaceActions";
import { actionOriginLabel, actionStatePresentation } from "./workspaceActionPresentation";

type Props = { actions: ActionOutcome[]; onApply(actionId: string): Promise<void>; onDismiss(actionId: string): Promise<void>; onUndo(actionId: string): Promise<void>; technicalDetails?: string | null; technicalInfo?: unknown };

export default function WorkspaceActionCards({ actions, onApply, onDismiss, onUndo, technicalDetails, technicalInfo }: Props) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const run = async (id: string, fn: (actionId: string) => Promise<void>) => {
    setBusyId(id);
    try { await fn(id); } finally { setBusyId(null); }
  };
  if (!actions.length && !technicalDetails && !technicalInfo) return null;
  const details = [
    technicalDetails,
    actions.length ? JSON.stringify(actions.map(({ request, request_digest, origin }) => ({ request, request_digest, origin })), null, 2) : null,
    technicalInfo ? JSON.stringify(technicalInfo, null, 2) : null
  ].filter(Boolean).join("\n\n");
  return <div className="jarvis-action-list">
    {actions.map((action) => {
      const presentation = actionStatePresentation(action.state);
      return <section className={`jarvis-action-card jarvis-action-card--${presentation.tone}`} key={action.action_id} aria-label={`${presentation.label} workspace action`}>
        <header><strong>{presentation.label}</strong><span>{actionOriginLabel(action.origin)}</span></header>
        <p>{action.summary}</p>
        {action.changes.length > 0 && <ul>{action.changes.map((change, index) => <li key={`${change.label}-${index}`}><strong>{change.label}</strong>: {change.before ?? "—"} → {change.after ?? "—"}</li>)}</ul>}
        {(action.state === "refused" || action.state === "stale") && action.reason && <p className="jarvis-action-card__reason">{action.reason}</p>}
        {action.state === "proposed" && <div className="jarvis-action-card__buttons"><button type="button" className="jarvis-primary-button" disabled={busyId === action.action_id} aria-label={`Apply ${action.summary}`} onClick={() => void run(action.action_id, onApply)}>Apply</button><button type="button" className="jarvis-link-button" disabled={busyId === action.action_id} aria-label={`Dismiss ${action.summary}`} onClick={() => void run(action.action_id, onDismiss)}>Dismiss</button></div>}
        {action.state === "applied" && action.undo_available && <button type="button" className="jarvis-link-button" disabled={busyId === action.action_id} aria-label={`Undo ${action.summary}`} onClick={() => void run(action.action_id, onUndo)}>Undo</button>}
        {action.state === "applied" && action.result_revision && <small>Revision {action.result_revision}</small>}
      </section>;
    })}
    {Boolean(details) && <details className="jarvis-action-technical"><summary>Technical details</summary><pre>{details}</pre></details>}
  </div>;
}
