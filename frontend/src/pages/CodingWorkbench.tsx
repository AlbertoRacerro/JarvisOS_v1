import { useEffect, useRef, useState, type ReactNode } from "react";

import {
  CODING_REPOSITORY,
  CODING_TARGET_REF,
  CodingRequestError,
  inspectCodingTarget,
  previewCodingContext,
  readChecks,
  readPipelineState,
  readPullRequest,
  readRepositoryFile,
  readRepositoryRef,
  readRepositoryTree,
  readReviews,
  readRuntimeTruth,
  readSafeGithubUrl,
  searchRepository,
  suggestCodingModification,
  type CodingActionResult,
  type CodingContextPreview,
  type RepositoryTruthResult,
  type RuntimeTruth
} from "../api/coding";

type Props = Readonly<{
  mode: "repository" | "runtime";
  workspaceId: string | null;
}>;

type TreeEntry = Readonly<{ path?: string; type?: string; sha?: string | null; size?: number | null }>;
type SearchMatch = Readonly<{ path?: string; line?: number; offset?: number }>;

type PartialEvidence = Readonly<{
  tree: boolean;
  file: boolean;
  search: boolean;
  pr: boolean;
  checks: boolean;
  reviews: boolean;
}>;

const EMPTY_PARTIAL: PartialEvidence = {
  tree: false,
  file: false,
  search: false,
  pr: false,
  checks: false,
  reviews: false
};

function Panel({ title, status, children }: Readonly<{ title: string; status?: string; children: ReactNode }>) {
  return <section className="final-fusion__panel" aria-label={title}><header className="final-fusion__panel-head"><h2>{title}</h2>{status ? <span>{status}</span> : null}</header>{children}</section>;
}

function errorText(cause: unknown): string {
  if (cause instanceof CodingRequestError) return cause.code;
  return cause instanceof Error ? cause.message : "coding_read_failed";
}

function exactSha(value: unknown): string {
  return typeof value === "string" && /^[0-9a-f]{40}$/.test(value) ? value : "Unknown";
}

function partialLabel(partial: PartialEvidence): string | null {
  const labels = Object.entries(partial).filter(([, value]) => value).map(([key]) => key);
  return labels.length ? `Partial evidence · ${labels.join(", ")}` : null;
}

function RepositorySurface({ workspaceId }: Readonly<{ workspaceId: string | null }>) {
  const [repository] = useState(CODING_REPOSITORY);
  const [ref] = useState(CODING_TARGET_REF);
  const [truth, setTruth] = useState<RepositoryTruthResult | null>(null);
  const [tree, setTree] = useState<TreeEntry[]>([]);
  const [treePath, setTreePath] = useState("");
  const [selectedPath, setSelectedPath] = useState("");
  const [safeUrl, setSafeUrl] = useState<string | null>(null);
  const [preview, setPreview] = useState("");
  const [literal, setLiteral] = useState("");
  const [matches, setMatches] = useState<SearchMatch[]>([]);
  const [prInput, setPrInput] = useState("");
  const [prEvidence, setPrEvidence] = useState<Record<string, unknown> | null>(null);
  const [partial, setPartial] = useState<PartialEvidence>(EMPTY_PARTIAL);
  const [inspectResult, setInspectResult] = useState<CodingActionResult | null>(null);
  const [contextBinding, setContextBinding] = useState<CodingContextPreview | null>(null);
  const [intent, setIntent] = useState("");
  const [proposal, setProposal] = useState<CodingActionResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileReadGeneration = useRef(0);

  const resolvedSha = truth?.resolved_sha ?? null;
  const anyPartial = truth?.partial || Object.values(partial).some(Boolean);

  const clearSelectedEvidence = () => {
    fileReadGeneration.current += 1;
    setSelectedPath("");
    setSafeUrl(null);
    setPreview("");
    setMatches([]);
    setPrEvidence(null);
    setPartial(EMPTY_PARTIAL);
    setInspectResult(null);
    setContextBinding(null);
    setProposal(null);
  };

  const refresh = async () => {
    setBusy(true); setError(null); setTruth(null); setTree([]); clearSelectedEvidence();
    setTreePath("");
    try {
      const nextTruth = await readRepositoryRef(repository, ref);
      setTruth(nextTruth);
      const exactRef = nextTruth.resolved_sha;
      if (!exactRef || !/^[0-9a-f]{40}$/.test(exactRef)) throw new Error("missing_exact_sha");
      const nextTree = await readRepositoryTree(repository, exactRef);
      const entries = nextTree.payload.entries;
      setTree(Array.isArray(entries) ? entries as TreeEntry[] : []);
      setPartial((current) => ({ ...current, tree: nextTree.partial }));
    } catch (cause) {
      setError(errorText(cause));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => { void refresh(); }, []);

  const openFile = async (path: string) => {
    const requestGeneration = ++fileReadGeneration.current;
    setSelectedPath(path); setSafeUrl(null); setPreview(""); setContextBinding(null); setProposal(null); setError(null);
    setPartial((current) => ({ ...current, file: false }));
    const requestSha = resolvedSha;
    if (!requestSha) { setError("missing_exact_sha"); return; }
    try {
      const [result, navigation] = await Promise.all([
        readRepositoryFile(repository, requestSha, path),
        readSafeGithubUrl(repository, requestSha, path)
      ]);
      if (fileReadGeneration.current !== requestGeneration) return;
      setPreview(typeof result.payload.text === "string" ? result.payload.text : "");
      setSafeUrl(typeof navigation.payload.url === "string" ? navigation.payload.url : null);
      setPartial((current) => ({ ...current, file: result.partial }));
    } catch (cause) {
      if (fileReadGeneration.current === requestGeneration) setError(errorText(cause));
    }
  };

  const openDirectory = async (path: string) => {
    if (!resolvedSha) { setError("missing_exact_sha"); return; }
    setTree([]); setError(null);
    setPartial((current) => ({ ...current, tree: false }));
    try {
      const result = await readRepositoryTree(repository, resolvedSha, path);
      const entries = result.payload.entries;
      setTree(Array.isArray(entries) ? entries as TreeEntry[] : []);
      setTreePath(path);
      setPartial((current) => ({ ...current, tree: result.partial }));
    } catch (cause) {
      setError(errorText(cause));
    }
  };

  const runSearch = async () => {
    if (!literal.trim() || !resolvedSha) return;
    setMatches([]); setError(null); setPartial((current) => ({ ...current, search: false }));
    try {
      const result = await searchRepository(repository, resolvedSha, literal.trim());
      setMatches(Array.isArray(result.payload.matches) ? result.payload.matches as SearchMatch[] : []);
      setPartial((current) => ({ ...current, search: result.partial }));
    } catch (cause) { setError(errorText(cause)); }
  };

  const loadPr = async () => {
    const prNumber = Number(prInput);
    if (!Number.isInteger(prNumber) || prNumber <= 0) { setError("invalid_pr_number"); return; }
    setPrEvidence(null); setError(null);
    setPartial((current) => ({ ...current, pr: false, checks: false, reviews: false }));
    try {
      const pr = await readPullRequest(repository, prNumber);
      const headSha = exactSha(pr.payload.head_sha);
      if (headSha === "Unknown") throw new Error("missing_pr_head_sha");
      const [checks, reviews] = await Promise.all([
        readChecks(repository, prNumber, headSha),
        readReviews(repository, prNumber, headSha)
      ]);
      setPrEvidence({ pr: pr.payload, checks: checks.payload, reviews: reviews.payload });
      setPartial((current) => ({ ...current, pr: pr.partial, checks: checks.partial, reviews: reviews.partial }));
    } catch (cause) { setError(errorText(cause)); }
  };

  const inspect = async () => {
    if (!workspaceId || !resolvedSha || !selectedPath) return;
    setInspectResult(null); setError(null);
    try {
      setInspectResult(await inspectCodingTarget({ workspace_id: workspaceId, repository, base_ref: ref, base_sha: resolvedSha, target_paths: [selectedPath] }));
    } catch (cause) { setError(errorText(cause)); }
  };

  const addContext = async () => {
    if (!workspaceId || !resolvedSha || !selectedPath || partial.file) return;
    setContextBinding(null); setProposal(null); setError(null);
    try {
      const next = await previewCodingContext({ workspace_id: workspaceId, repository, base_ref: ref, base_sha: resolvedSha, target_paths: [selectedPath] });
      if (next.state !== "current" || !next.context_digest || !next.added_context_refs?.length) {
        setError(next.reason ?? "context_preview_refused");
        return;
      }
      setContextBinding(next);
    } catch (cause) { setError(errorText(cause)); }
  };

  const suggest = async () => {
    if (!workspaceId || !resolvedSha || !selectedPath || !intent.trim()) return;
    setProposal(null); setError(null);
    try {
      setProposal(await suggestCodingModification({
        workspace_id: workspaceId,
        repository,
        base_ref: ref,
        base_sha: resolvedSha,
        target_paths: [selectedPath],
        intent: intent.trim(),
        added_context_refs: contextBinding?.added_context_refs,
        expected_context_digest: contextBinding?.context_digest ?? null,
        expected_checks: []
      }));
    } catch (cause) { setError(errorText(cause)); }
  };

  return <div className="final-fusion__workbench final-fusion__workbench--coding" data-testid="coding-repository-surface">
    <Panel title="Repository" status={busy ? "Loading" : error ? "Read error" : anyPartial ? "Partial" : truth ? "Exact READ" : "Unknown"}>
      <div className="final-fusion__repo-status"><div><strong>{repository}</strong><span>requested ref · {ref}</span></div><span className={resolvedSha ? "" : "final-fusion__unknown"}>{resolvedSha ?? "Unknown"}</span></div>
      <div className="final-fusion__toolbar-line"><span>Server-owned 118 repository truth</span><button type="button" onClick={() => void refresh()} disabled={busy}>Refresh exact truth</button></div>
      {partialLabel(partial) ? <div className="final-fusion__source-empty" role="status"><strong>{partialLabel(partial)}</strong><span>Truncated evidence is not presented as complete.</span></div> : null}
      {error ? <div className="final-fusion__source-empty" role="status"><strong>Repository read refused / unavailable</strong><span>{error}</span></div> : null}
      <div className="final-fusion__toolbar-line">
        <span>Tree path · {treePath || "Root"}</span>
        <div><button type="button" onClick={() => void openDirectory("")} disabled={!resolvedSha || !treePath}>Root</button><button type="button" onClick={() => void openDirectory(treePath.split("/").slice(0, -1).join("/"))} disabled={!resolvedSha || !treePath}>Up</button></div>
      </div>
      <div className="final-fusion__source-list">{tree.length ? tree.map((entry) => entry.path ? <button type="button" className="final-fusion__disclosure-row" key={entry.path} onClick={() => entry.type === "file" ? void openFile(entry.path!) : entry.type === "dir" ? void openDirectory(entry.path!) : undefined} disabled={entry.type !== "file" && entry.type !== "dir"}><span>›</span><strong>{entry.path}</strong><em>{entry.type ?? "unknown"}{typeof entry.size === "number" ? ` · ${entry.size} B` : ""}</em></button> : null) : <div className="final-fusion__source-empty"><strong>No current tree evidence</strong></div>}</div>
    </Panel>
    <Panel title="File / search / PR evidence" status={anyPartial ? "PARTIAL · READ only" : "READ only"}>
      <div className="final-fusion__toolbar-line"><span>Selected path · {selectedPath || "None"}</span>{safeUrl ? <a href={safeUrl} target="_blank" rel="noreferrer">Open server-validated GitHub path</a> : null}</div>
      <pre className="final-fusion__searchbox">{preview || "Select a file for bounded UTF-8 preview."}</pre>
      <div className="final-fusion__toolbar-line"><input aria-label="Literal repository search" value={literal} onChange={(event) => setLiteral(event.target.value)} placeholder="Literal search" maxLength={512}/><button type="button" onClick={() => void runSearch()} disabled={!literal.trim() || !resolvedSha}>Search</button></div>
      <div className="final-fusion__source-list">{matches.map((match, index) => <div className="final-fusion__disclosure-row" key={`${match.path}:${match.offset}:${index}`}><span>›</span><strong>{match.path ?? "Unknown"}</strong><em>line {match.line ?? "?"}</em></div>)}</div>
      <div className="final-fusion__toolbar-line"><input aria-label="Pull request number" inputMode="numeric" value={prInput} onChange={(event) => setPrInput(event.target.value)} placeholder="PR number"/><button type="button" onClick={() => void loadPr()} disabled={!prInput}>Load PR evidence</button></div>
      {prEvidence ? <pre className="final-fusion__searchbox">{JSON.stringify(prEvidence, null, 2)}</pre> : null}
    </Panel>
    <Panel title="Jarvis Coding" status="READ / CONTEXT / PROPOSE only">
      <div className="final-fusion__context-note">Repository browsing is context-neutral. These explicit actions are exact-base 111/123 operations; they do not commit, apply, execute, push, create a PR, merge, or mutate STATUS.</div>
      <div className="final-fusion__toolbar-line"><button type="button" onClick={() => void inspect()} disabled={!workspaceId || !resolvedSha || !selectedPath}>Inspect selected exact file</button><span>{inspectResult ? `${inspectResult.state}${inspectResult.reason ? ` · ${inspectResult.reason}` : ""}` : "No explicit Coding inspection yet"}</span></div>
      <div className="final-fusion__toolbar-line"><button type="button" onClick={() => void addContext()} disabled={!workspaceId || !resolvedSha || !selectedPath || partial.file}>Add selected exact file to proposal context</button><span>{contextBinding?.context_digest ? `Context bound · ${contextBinding.context_digest}` : "Browsing has not entered Jarvis context"}</span></div>
      <textarea aria-label="Suggest modification intent" rows={4} maxLength={4000} value={intent} onChange={(event) => setIntent(event.target.value)} placeholder="Describe a bounded proposal for the selected path" />
      <button type="button" onClick={() => void suggest()} disabled={!workspaceId || !resolvedSha || !selectedPath || !intent.trim()}>Suggest modification</button>
      {proposal ? <pre className="final-fusion__searchbox">{JSON.stringify(proposal, null, 2)}</pre> : null}
    </Panel>
  </div>;
}

function RuntimeSurface() {
  const [runtime, setRuntime] = useState<RuntimeTruth | null>(null);
  const [prInput, setPrInput] = useState("");
  const [specId, setSpecId] = useState("140");
  const [pipeline, setPipeline] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pipelineRequestGeneration = useRef(0);

  const refresh = async () => {
    setLoading(true); setError(null); setRuntime(null);
    try { setRuntime(await readRuntimeTruth()); } catch (cause) { setError(errorText(cause)); } finally { setLoading(false); }
  };
  useEffect(() => { void refresh(); }, []);

  const loadPipeline = async () => {
    const prNumber = Number(prInput);
    if (!Number.isInteger(prNumber) || prNumber <= 0 || !specId.trim()) { setError("invalid_pipeline_selection"); return; }
    const requestGeneration = ++pipelineRequestGeneration.current;
    setPipeline(null); setError(null);
    try {
      const result = await readPipelineState(CODING_REPOSITORY, prNumber, specId.trim());
      if (pipelineRequestGeneration.current === requestGeneration) setPipeline(result);
    } catch (cause) {
      if (pipelineRequestGeneration.current === requestGeneration) setError(errorText(cause));
    }
  };

  const invalidatePipelineSelection = () => {
    pipelineRequestGeneration.current += 1;
    setPipeline(null);
  };

  const startup: Record<string, unknown> = runtime?.startup ?? {};
  const live: Record<string, unknown> = runtime?.live ?? {};
  const remote: Record<string, unknown> = runtime?.remote ?? {};
  const localSha = exactSha(live.git_sha);
  const remoteSha = exactSha(remote.resolved_sha);
  const relation = runtime?.alignment ?? "unknown";

  return <div className="final-fusion__workbench final-fusion__workbench--coding" data-testid="coding-runtime-surface">
    <Panel title="Runtime" status={loading ? "Loading" : error ? "Read error" : runtime?.observer_status ?? "Unknown"}>
      <div className="final-fusion__repo-status"><div><strong>JarvisOS runtime identity</strong><span>{CODING_REPOSITORY} · target {CODING_TARGET_REF}</span></div><span className={relation === "unknown" ? "final-fusion__unknown" : ""}>{relation}</span></div>
      <section className="final-fusion__compare"><div className="final-fusion__version-card"><small>Local current · actually executed</small><strong>LOCAL · {localSha}</strong><code>{String(live.branch ?? live.head_state ?? "Unknown")}</code><p>Root identity · {String(live.root_identity ?? "unknown")}</p><p>Observed at · {String(live.observed_at ?? "unknown")}</p><p>Provenance · {String(live.provenance ?? "unknown")}</p><p>Failure identity · {String(live.failure_code ?? "none")}</p><p>Dirty state · {String(live.dirty_state ?? "unknown")}</p></div><div className="final-fusion__delta">→<span>{relation}</span></div><div className="final-fusion__version-card is-remote"><small>Remote target · server observed</small><strong>REMOTE · {remoteSha}</strong><code>{String(remote.requested_ref ?? CODING_TARGET_REF)}</code><p>Observed at · {String(remote.observed_at ?? "unknown")}</p><p>Remote status · {runtime?.remote_status ?? "unknown"}</p></div></section>
      <div className="final-fusion__source-empty">
        <strong>Process startup identity · {exactSha(startup.git_sha)}</strong>
        <span>Root identity · {String(startup.root_identity ?? "unknown")}</span>
        <span>Observed at · {String(startup.observed_at ?? "unknown")}</span>
        <span>Ref · {String(startup.branch ?? startup.head_state ?? "Unknown")}</span>
        <span>Provenance · {String(startup.provenance ?? "unknown")}</span>
        <span>Failure identity · {String(startup.failure_code ?? "none")}</span>
      </div>
      <div className="final-fusion__context-note">Alignment is rendered exactly from 119. The browser performs no SHA ancestry or cleanliness inference.</div>
      {runtime?.reason ? <div className="final-fusion__source-empty" role="status"><strong>Runtime relation reason · {runtime.reason}</strong><span>Worktree changed since start · {runtime.worktree_changed_since_start ? "yes" : "no"}</span></div> : null}
      {error ? <div className="final-fusion__source-empty" role="status"><strong>Runtime truth unavailable</strong><span>{error}</span></div> : null}
      <button type="button" onClick={() => void refresh()} disabled={loading}>Refresh runtime truth</button>
    </Panel>
    <Panel title="Development pipeline" status={pipeline ? "120 server projection" : "Unselected"}>
      <div className="final-fusion__toolbar-line"><input aria-label="Pipeline PR number" inputMode="numeric" value={prInput} onChange={(event) => { setPrInput(event.target.value); invalidatePipelineSelection(); }} placeholder="PR number"/><input aria-label="Pipeline spec id" value={specId} onChange={(event) => { setSpecId(event.target.value); invalidatePipelineSelection(); }} placeholder="Spec id"/><button type="button" onClick={() => void loadPipeline()} disabled={!prInput || !specId.trim()}>Load pipeline state</button></div>
      {pipeline ? <pre className="final-fusion__searchbox">{JSON.stringify(pipeline, null, 2)}</pre> : <div className="final-fusion__source-empty"><strong>No pipeline selection</strong><span>No synthetic stages are shown.</span></div>}
    </Panel>
  </div>;
}

export default function CodingWorkbench({ mode, workspaceId }: Props) {
  return mode === "repository" ? <RepositorySurface workspaceId={workspaceId} /> : <RuntimeSurface />;
}
