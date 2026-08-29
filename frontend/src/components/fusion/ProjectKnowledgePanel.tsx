import { useEffect, useMemo, useState } from "react";

import {
  approveProjectKnowledgeDraft,
  changeProjectKnowledgeRevisionState,
  createProjectKnowledgeDraft,
  getProjectKnowledgeRevalidation,
  listProjectKnowledgeRevisions,
  previewProjectKnowledgeImpact,
  reconcileProjectKnowledge,
  type ProjectKnowledgeDraft,
  type ProjectKnowledgeImpact,
  type ProjectKnowledgeRevalidation,
  type ProjectKnowledgeRevision
} from "../../api/projectKnowledge";

type Props = Readonly<{ workspaceId: string | null }>;

function shortId(value: string | null | undefined): string {
  return value ? `${value.slice(0, 8)}…` : "None";
}

function requestKey(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}

export default function ProjectKnowledgePanel({ workspaceId }: Props) {
  const [revisions, setRevisions] = useState<ProjectKnowledgeRevision[]>([]);
  const [selectedWorkingId, setSelectedWorkingId] = useState<string | null>(null);
  const [statement, setStatement] = useState("");
  const [draft, setDraft] = useState<ProjectKnowledgeDraft | null>(null);
  const [impact, setImpact] = useState<ProjectKnowledgeImpact | null>(null);
  const [revalidation, setRevalidation] = useState<ProjectKnowledgeRevalidation | null>(null);
  const [knownFailAck, setKnownFailAck] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentReconciled = useMemo(
    () => revisions.find((revision) => revision.state === "reconciled" && revision.reconciled_snapshot_id) ?? null,
    [revisions]
  );
  const working = useMemo(() => revisions.filter((revision) => revision.state === "working"), [revisions]);
  const selectedWorking = useMemo(
    () => working.find((revision) => revision.id === selectedWorkingId) ?? working[0] ?? null,
    [selectedWorkingId, working]
  );

  const reload = async () => {
    if (!workspaceId) {
      setRevisions([]);
      setSelectedWorkingId(null);
      return;
    }
    const next = await listProjectKnowledgeRevisions(workspaceId);
    setRevisions(next);
    const nextWorking = next.filter((revision) => revision.state === "working");
    setSelectedWorkingId((current) => nextWorking.some((revision) => revision.id === current) ? current : nextWorking[0]?.id ?? null);
  };

  useEffect(() => {
    setDraft(null);
    setImpact(null);
    setRevalidation(null);
    setKnownFailAck("");
    setError(null);
    void reload().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Project Knowledge read failed"));
  }, [workspaceId]);

  useEffect(() => {
    if (!workspaceId || !selectedWorking) {
      setRevalidation(null);
      return;
    }
    void getProjectKnowledgeRevalidation(workspaceId, selectedWorking.id)
      .then(setRevalidation)
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Revalidation read failed"));
  }, [selectedWorking?.id, workspaceId]);

  const act = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await operation();
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Project Knowledge transition failed");
    } finally {
      setBusy(false);
    }
  };

  const stageRequirement = () => act(async () => {
    if (!workspaceId || !statement.trim()) return;
    const parent = selectedWorking;
    const nextDraft = await createProjectKnowledgeDraft({
      workspace_id: workspaceId,
      parent_kind: parent ? "working" : "reconciled",
      parent_revision_id: parent?.id ?? currentReconciled?.id ?? null,
      operations: [{
        owner_kind: "requirement",
        operation_kind: "create",
        fields: {
          statement: statement.trim(),
          status: "active",
          basis_kind: "requirement",
          reconciliation_gate: "advisory"
        }
      }]
    });
    const nextImpact = await previewProjectKnowledgeImpact(workspaceId, nextDraft.id);
    setDraft(nextDraft);
    setImpact(nextImpact);
  });

  const approve = () => act(async () => {
    if (!workspaceId || !draft || !impact || !impact.complete) return;
    const result = await approveProjectKnowledgeDraft({
      workspace_id: workspaceId,
      approval_request_key: requestKey("project-basis-approve"),
      draft_id: draft.id,
      expected_draft_revision_token: draft.revision_token,
      expected_preview_digest: impact.digest,
      origin: "operator"
    });
    if (result.state !== "success" || !result.working_revision_id) throw new Error(result.failure_code ?? "Approval did not produce a working revision");
    setStatement("");
    setDraft(null);
    setImpact(null);
    await reload();
    setSelectedWorkingId(result.working_revision_id);
  });

  const discard = () => act(async () => {
    if (!workspaceId || !selectedWorking) return;
    await changeProjectKnowledgeRevisionState(selectedWorking.id, { workspace_id: workspaceId, action: "discard" });
    setRevalidation(null);
    await reload();
  });

  const reconcile = () => act(async () => {
    if (!workspaceId || !selectedWorking || !revalidation?.complete) return;
    if (revalidation.known_fail_requirement_ids.length && !knownFailAck.trim()) return;
    const result = await reconcileProjectKnowledge({
      workspace_id: workspaceId,
      idempotency_key: requestKey("project-basis-reconcile"),
      working_revision_id: selectedWorking.id,
      expected_target_snapshot_id: currentReconciled?.reconciled_snapshot_id ?? null,
      expected_target_digest: selectedWorking.projected_state_digest,
      expected_selected_validation_set_digest: revalidation.selected_validation_set_digest,
      known_fail_acknowledgement: knownFailAck.trim() || null,
      policy_identity: knownFailAck.trim() ? "operator-explicit-known-fail-v0" : null
    });
    if (result.state !== "success") throw new Error(result.failure_code ?? "Reconciliation did not commit");
    setKnownFailAck("");
    setRevalidation(null);
    await reload();
  });

  if (!workspaceId) {
    return <section className="final-fusion__panel final-fusion__basis" aria-label="Project Knowledge"><header className="final-fusion__panel-head"><h2>Project Knowledge</h2><span>Unavailable</span></header><div className="final-fusion__empty">Select a workspace to inspect server-owned working revisions.</div></section>;
  }

  return <section className="final-fusion__panel final-fusion__basis" aria-label="Project Knowledge">
    <header className="final-fusion__panel-head"><h2>Project Knowledge</h2><span>112 · server-owned</span></header>
    <div className="final-fusion__dossier-top"><strong>Reconciled snapshot · {shortId(currentReconciled?.reconciled_snapshot_id)}</strong><span>Working revisions · {working.length}</span></div>
    {error && <div className="final-fusion__source-empty"><strong>Transition rejected</strong><span>{error}</span></div>}
    <div className="final-fusion__toolbar-line">
      <span>Selected working parent / chain</span>
      <select aria-label="Working revision" value={selectedWorking?.id ?? ""} onChange={(event) => setSelectedWorkingId(event.target.value || null)} disabled={busy || !working.length}>
        <option value="">Current reconciled basis</option>
        {working.map((revision) => <option key={revision.id} value={revision.id}>{shortId(revision.id)} · {revision.origin}</option>)}
      </select>
    </div>
    {selectedWorking && <div className="final-fusion__facts"><div>Revision · {selectedWorking.id}</div><div>Parent · {selectedWorking.parent_kind}:{shortId(selectedWorking.parent_revision_id)}</div><div>Change-set digest · {selectedWorking.change_set_digest}</div><div>Projected state digest · {selectedWorking.projected_state_digest}</div></div>}
    <div className="final-fusion__toolbar-line"><span>Stage one server-supported Requirement on the selected exact parent.</span><input aria-label="Requirement statement" value={statement} onChange={(event) => setStatement(event.target.value)} disabled={busy} placeholder="Requirement statement" /><button type="button" disabled={busy || !statement.trim()} onClick={stageRequirement}>Preview impact</button></div>
    {draft && impact && <div className="final-fusion__source-list"><div className="final-fusion__disclosure-row"><span>›</span><strong>Draft {shortId(draft.id)} · token {shortId(draft.revision_token)}</strong><em>{impact.complete ? "Impact complete" : "Impact incomplete"}</em></div><div className="final-fusion__facts"><div>Affected refs · {impact.affected_refs.length ? impact.affected_refs.join(", ") : "None"}</div><div>Owner tokens · {Object.entries(impact.owner_tokens).map(([ref, token]) => `${ref}=${token}`).join(" · ") || "None"}</div><div>Diagnostics · {impact.diagnostics.join(", ") || "None"}</div><div>Impact digest · {impact.digest}</div></div><div className="final-fusion__toolbar-line"><span>Approve all creates an immutable working revision; it does not reconcile canonical truth.</span><button type="button" disabled={busy || !impact.complete} onClick={approve}>Approve all</button></div></div>}
    {selectedWorking && revalidation && <div className="final-fusion__source-list"><div className="final-fusion__disclosure-row"><span>›</span><strong>Deterministic revalidation</strong><em>{revalidation.complete ? "Terminal" : "Blocked"}</em></div><div className="final-fusion__facts"><div>PASS/current evidence · {revalidation.current_validation_ids.length}</div><div>Blocking criteria · {revalidation.blocking_requirement_ids.join(", ") || "None"}</div><div>Known FAIL · {revalidation.known_fail_requirement_ids.join(", ") || "None"}</div><div>Recomputation required · {revalidation.recomputation_required.join(", ") || "None"}</div><div>Validation-set digest · {revalidation.selected_validation_set_digest}</div></div>{revalidation.recomputation_required.length > 0 && <div className="final-fusion__toolbar-line"><span>Recomputation remains owned by the canonical Process domain.</span><a href="/design/process">Open Process</a></div>}{revalidation.known_fail_requirement_ids.length > 0 && <div className="final-fusion__toolbar-line"><span>Known mandatory FAIL requires explicit acknowledgement.</span><input aria-label="Known fail acknowledgement" value={knownFailAck} onChange={(event) => setKnownFailAck(event.target.value)} disabled={busy} placeholder="Acknowledge known FAIL evidence" /></div>}<div className="final-fusion__toolbar-line"><button type="button" disabled={busy} onClick={discard}>Discard working revision</button><button type="button" disabled={busy || !revalidation.complete || (revalidation.known_fail_requirement_ids.length > 0 && !knownFailAck.trim())} onClick={reconcile}>Final reconcile</button></div></div>}
    <div className="final-fusion__context-strip">Frontend state is non-canonical. Every protected transition reloads exact server truth; branching is explicit by selecting a historical working parent before staging.</div>
  </section>;
}
