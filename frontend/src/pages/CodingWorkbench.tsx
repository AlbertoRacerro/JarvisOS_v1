import { useEffect, useState, type ReactNode } from "react";

import {
  CODING_REPOSITORY,
  CODING_TARGET_REF,
  CodingRequestError,
  inspectCodingTarget,
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
  type RepositoryTruthResult,
  type RuntimeTruth
} from "../api/coding";

type Props = Readonly<{
  mode: "repository" | "runtime";
  workspaceId: string | null;
}>;

type TreeEntry = Readonly<{ path?: string; type?: string; sha?: string | null; size?: number | null }>;
type SearchMatch = Readonly<{ path?: string; line?: number; offset?: number }>;

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

function RepositorySurface({ workspaceId }: Readonly<{ workspaceId: string | null }>) {
  const [repository] = useState(CODING_REPOSITORY);
  const [ref] = useState(CODING_TARGET_REF);
  const [truth, setTruth] = useState<RepositoryTruthResult | null>(null);
  const [tree, setTree] = useState<TreeEntry[]>([]);
  const [selectedPath, setSelectedPath] = useState("");
  const [safeUrl, setSafeUrl] = useState<string | null>(null);
  const [preview, setPreview] = useState("");
  const [literal, setLiteral] = useState("");
  const [matches, setMatches] = useState<SearchMatch[]>([]);
  const [prInput, setPrInput] = useState("");
  const [prEvidence, setPrEvidence] = useState<Record<string, unknown> | null>(null);
  const [inspectResult, setInspectResult] = useState<CodingActionResult | null>(null);
  const [intent, setIntent] = useState("");
  const [proposal, setProposal] = useState<CodingActionResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resolvedSha = truth?.resolved_sha ?? null;

  const refresh = async () => {
    setBusy(true); setError(null); setTruth(null); setTree([]); setSelectedPath(""); setSafeUrl(null); setPreview(""); setMatches([]); setPrEvidence(null); setInspectResult(null); setProposal(null);
    try {
      const nextTruth = await readRepositoryRef(repository, ref);
      setTruth(nextTruth);
      const nextTree = await readRepositoryTree(repository, ref);
      const entries = nextTree.payload.entries;
      setTree(Array.isArray(entries) ? entries as TreeEntry[] : []);
    } catch (cause) {
      setError(errorText(cause));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => { void refresh(); }, []);

  const openFile = async (path: string) => {
    setSelectedPath(path); setSafeUrl(null); setPreview(""); setError(null);
    if (!resolvedSha) { setError("missing_exact_sha"); return; }
    try {
      const [result, navigation] = await Promise.all([
        readRepositoryFile(repository, ref, path),
        readSafeGithubUrl(repository, resolvedSha, path)
      ]);
      setPreview(typeof result.payload.text === "string" ? result.payload.text : "");
      setSafeUrl(typeof navigation.payload.url === "string" ? navigation.payload.url : null);
    } catch (cause) { setError(errorText(cause)); }
  };

  const runSearch = async () => {
    if (!literal.trim()) return;
    setMatches([]); setError(null);
    try {
      const result = await searchRepository(repository, ref, literal.trim());
      setMatches(Array.isArray(result.payload.matches) ? result.payload.matches as SearchMatch[] : []);
    } catch (cause) { setError(errorText(cause)); }
  };

  const loadPr = async () => {
    const prNumber = Number(prInput);
    if (!Number.isInteger(prNumber) || prNumber <= 0) { setError("invalid_pr_number"); return; }
    setPrEvidence(null); setError(null);
    try {
      const pr = await readPullRequest(repository, prNumber);
      const headSha = exactSha(pr.payload.head_sha);
      if (headSha === "Unknown") throw new Error("missing_pr_head_sha");
      const [checks, reviews] = await Promise.all([
        readChecks(repository, prNumber, headSha),
        readReviews(repository, prNumber, headSha)
      ]);
      setPrEvidence({ pr: pr.payload, checks: checks.payload, reviews: reviews.payload });
    } catch (cause) { setError(errorText(cause)); }
  };

  const inspect = async () => {
    if (!workspaceId || !resolvedSha || !selectedPath) return;
    setInspectResult(null); setError(null);
    try {
      setInspectResult(await inspectCodingTarget({ workspace_id: workspaceId, repository, base_ref: ref, base_sha: resolvedSha, target_paths: [selectedPath] }));
    } catch (cause) { setError(errorText(cause)); }
  };

  const suggest = async () => {
    if (!workspaceId || !resolvedSha || !selectedPath || !intent.trim()) return;
    setProposal(null); setError(null);
    try {
      setProposal(await suggestCodingModification({ workspace_id: workspaceId, repository, base_ref: ref, base_sha: resolvedSha, target_paths: [selectedPath], intent: intent.trim(), expected_checks: [] }));
    } catch (cause) { setError(errorText(cause)); }
  };

  return <div className="final-fusion__workbench final-fusion__workbench--coding" data-testid="coding-repository-surface">
    <Panel title="Repository" status={busy ? "Loading" : error ? "Read error" : truth?.partial ? "Partial" : truth ? "Exact READ" : "Unknown"}>
      <div className="final-fusion__repo-status"><div><strong>{repository}</strong><span>requested ref · {ref}</span></div><span className={resolvedSha ? "" : "final-fusion__unknown"}>{resolvedSha ?? "Unknown"}</span></div>
      <div className="final-fusion__toolbar-line"><span>Server-owned 118 repository truth</span><button type="button" onClick={() => void refresh()} disabled={busy}>Refresh exact truth</button></div>
      {error ? <div className="final-fusion__source-empty" role="status"><strong>Repository read refused / unavailable</strong><span>{error}</span></div> : null}
      <div className="final-fusion__source-list">{tree.length ? tree.map((entry) => entry.path ? <button type="button" className="final-fusion__disclosure-row" key={entry.path} onClick={() => entry.type === "file" ? void openFile(entry.path!) : undefined} disabled={entry.type !== "file"}><span>›</span><strong>{entry.path}</strong><em>{entry.type ?? "unknown"}{typeof entry.size === "number" ? ` · ${entry.size} B` : ""}</em></button> : null) : <div className="final-fusion__source-empty"><strong>No current tree evidence</strong></div>}</div>
    </Panel>
    <Panel title="File / search / PR evidence" status="READ only">
      <div className="final-fusion__toolbar-line"><span>Selected path · {selectedPath || "None"}</span>{safeUrl ? <a href={safeUrl} target="_blank" rel="noreferrer">Open server-validated GitHub path</a> : null}</div>
      <pre className="final-fusion__searchbox">{preview || "Select a file for bounded UTF-8 preview."}</pre>
      <div className="final-fusion__toolbar-line"><input aria-label="Literal repository search" value={literal} onChange={(event) => setLiteral(event.target.value)} placeholder="Literal search" maxLength={512}/><button type="button" onClick={() => void runSearch()} disabled={!literal.trim()}>Search</button></div>
      <div className="final-fusion__source-list">{matches.map((match, index) => <div className="final-fusion__disclosure-row" key={`${match.path}:${match.offset}:${index}`}><span>›</span><strong>{match.path ?? "Unknown"}</strong><em>line {match.line ?? "?"}</em></div>)}</div>
      <div className="final-fusion__toolbar-line"><input aria-label="Pull request number" inputMode="numeric" value={prInput} onChange={(event) => setPrInput(event.target.value)} placeholder="PR number"/><button type="button" onClick={() => void loadPr()} disabled={!prInput}>Load PR evidence</button></div>
      {prEvidence ? <pre className="final-fusion__searchbox">{JSON.stringify(prEvidence, null, 2)}</pre> : null}
    </Panel>
    <Panel title="Jarvis Coding" status="READ / PROPOSE only">
      <div className="final-fusion__context-note">Repository browsing is context-neutral. These explicit actions are exact-base 123 operations; they do not commit, apply, execute, push, create a PR, merge, or mutate STATUS.</div>
      <div className="final-fusion__toolbar-line"><button type="button" onClick={() => void inspect()} disabled={!workspaceId || !resolvedSha || !selectedPath}>Inspect selected exact file</button><span>{inspectResult ? `${inspectResult.state}${inspectResult.reason ? ` · ${inspectResult.reason}` : ""}` : "No explicit Coding inspection yet"}</span></div>
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

  const refresh = async () => {
    setLoading(true); setError(null); setRuntime(null);
    try { setRuntime(await readRuntimeTruth()); } catch (cause) { setError(errorText(cause)); } finally { setLoading(false); }
  };
  useEffect(() => { void refresh(); }, []);

  const loadPipeline = async () => {
    const prNumber = Number(prInput);
    if (!Number.isInteger(prNumber) || prNumber <= 0 || !specId.trim()) { setError("invalid_pipeline_selection"); return; }
    setPipeline(null); setError(null);
    try { setPipeline(await readPipelineState(CODING_REPOSITORY, prNumber, specId.trim())); } catch (cause) { setError(errorText(cause)); }
  };

  const live: Record<string, unknown> = runtime?.live ?? {};
  const remote: Record<string, unknown> = runtime?.remote ?? {};
  const localSha = exactSha(live.git_sha);
  const remoteSha = exactSha(remote.resolved_sha);
  const relation = runtime?.alignment ?? "unknown";

  return <div className="final-fusion__workbench final-fusion__workbench--coding" data-testid="coding-runtime-surface">
    <Panel title="Runtime" status={loading ? "Loading" : error ? "Read error" : runtime?.observer_status ?? "Unknown"}>
      <div className="final-fusion__repo-status"><div><strong>JarvisOS runtime identity</strong><span>{CODING_REPOSITORY} · target {CODING_TARGET_REF}</span></div><span className={relation === "unknown" ? "final-fusion__unknown" : ""}>{relation}</span></div>
      <section className="final-fusion__compare"><div className="final-fusion__version-card"><small>Local current · actually executed</small><strong>LOCAL · {localSha}</strong><code>{String(live.branch ?? live.head_state ?? "Unknown")}</code><p>Dirty state · {String(live.dirty_state ?? "unknown")}</p></div><div className="final-fusion__delta">→<span>{relation}</span></div><div className="final-fusion__version-card is-remote"><small>Remote target · server observed</small><strong>REMOTE · {remoteSha}</strong><code>{String(remote.requested_ref ?? CODING_TARGET_REF)}</code><p>Remote status · {runtime?.remote_status ?? "unknown"}</p></div></section>
      <div className="final-fusion__context-note">Alignment is rendered exactly from 119. The browser performs no SHA ancestry or cleanliness inference.</div>
      {error ? <div className="final-fusion__source-empty" role="status"><strong>Runtime truth unavailable</strong><span>{error}</span></div> : null}
      <button type="button" onClick={() => void refresh()} disabled={loading}>Refresh runtime truth</button>
    </Panel>
    <Panel title="Development pipeline" status={pipeline ? "120 server projection" : "Unselected"}>
      <div className="final-fusion__toolbar-line"><input aria-label="Pipeline PR number" inputMode="numeric" value={prInput} onChange={(event) => { setPrInput(event.target.value); setPipeline(null); }} placeholder="PR number"/><input aria-label="Pipeline spec id" value={specId} onChange={(event) => { setSpecId(event.target.value); setPipeline(null); }} placeholder="Spec id"/><button type="button" onClick={() => void loadPipeline()} disabled={!prInput || !specId.trim()}>Load pipeline state</button></div>
      {pipeline ? <pre className="final-fusion__searchbox">{JSON.stringify(pipeline, null, 2)}</pre> : <div className="final-fusion__source-empty"><strong>No pipeline selection</strong><span>No synthetic stages are shown.</span></div>}
    </Panel>
  </div>;
}

export default function CodingWorkbench({ mode, workspaceId }: Props) {
  return mode === "repository" ? <RepositorySurface workspaceId={workspaceId} /> : <RuntimeSurface />;
}
