import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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
import { pullRequestEvidenceSummary, runtimeDeltaSummary } from "../operatorSemantics";
import "./CodingWorkbench.css";

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

type RepositoryErrors = Readonly<{
  repository: string | null;
  tree: string | null;
  file: string | null;
  search: string | null;
  pr: string | null;
  checks: string | null;
  reviews: string | null;
  inspect: string | null;
  context: string | null;
  proposal: string | null;
}>;

const EMPTY_PARTIAL: PartialEvidence = {
  tree: false,
  file: false,
  search: false,
  pr: false,
  checks: false,
  reviews: false
};

const EMPTY_REPOSITORY_ERRORS: RepositoryErrors = {
  repository: null,
  tree: null,
  file: null,
  search: null,
  pr: null,
  checks: null,
  reviews: null,
  inspect: null,
  context: null,
  proposal: null
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

function canonicalPrNumber(value: string): number | null {
  if (!/^[1-9][0-9]*$/.test(value)) return null;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

function canonicalSpecId(value: string): string | null {
  if (!/^[0-9]{3}[a-z]?$/.test(value)) return null;
  return Number(value.slice(0, 3)) > 0 ? value : null;
}

function partialLabel(partial: PartialEvidence): string | null {
  const labels = Object.entries(partial).filter(([, value]) => value).map(([key]) => key);
  return labels.length ? `Partial evidence · ${labels.join(", ")}` : null;
}

function humanize(value: unknown, fallback = "Unknown"): string {
  if (typeof value !== "string" || !value.trim()) return fallback;
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function TechnicalDetails({ children }: Readonly<{ children: ReactNode }>) {
  return <details><summary>Technical details</summary>{children}</details>;
}

function RawJson({ value }: Readonly<{ value: unknown }>) {
  return <TechnicalDetails><pre className="final-fusion__searchbox">{JSON.stringify(value, null, 2)}</pre></TechnicalDetails>;
}

function readableReason(code: string): string {
  const reasons: Record<string, string> = {
    provider_unavailable: "The backend provider is unavailable. Retry when the repository connection or local coding model is available.",
    missing_evidence: "Complete file evidence is unavailable. Refresh the repository and reopen the file before retrying.",
    stale_target: "The branch changed since this file was opened. Refresh the repository and review the new file before retrying.",
    identity_conflict: "The selected context is no longer current. Remove it, refresh the repository, and add the file again.",
    unauthorized_repository: "This repository is not enabled in the backend configuration.",
    missing_exact_sha: "The repository commit could not be verified. Refresh the repository before opening files.",
    proposal_invalid: "The model did not return a valid bounded proposal. No change was applied; you can retry.",
    proposal_too_large: "The proposed change exceeds the allowed size. Describe a smaller change and retry.",
    invalid_pr_number: "Enter a positive pull request number, such as 655.",
    invalid_pipeline_selection: "Enter a positive pull request number and a three-digit spec ID, such as 144."
  };
  return reasons[code] ?? humanize(code, "The request could not be completed. Please retry.");
}

function ActionResult({ value, kind }: Readonly<{ value: CodingActionResult; kind: "inspect" | "proposal" }>) {
  if (value.state === "refused") return <div className="coding-action-result" role="status"><strong>{kind === "inspect" ? "Inspection" : "Proposal"} unavailable</strong><p>{readableReason(value.reason ?? "unknown")}</p><RawJson value={value} /></div>;
  const changes = Array.isArray(value.changes) ? value.changes as Record<string, unknown>[] : [];
  const evidence = Array.isArray(value.evidence) ? value.evidence as Record<string, unknown>[] : [];
  return <section className="coding-action-result" aria-label={kind === "inspect" ? "File inspection result" : "Modification proposal result"}>
    <strong>{kind === "inspect" ? "File evidence verified" : "Proposal ready for review"}</strong>
    <p>{kind === "inspect" ? "The backend verified these files at the selected commit. This is a deterministic inspection, not an AI analysis." : typeof value.summary === "string" ? value.summary : humanize(value.state)}</p>
    {evidence.map((item, index) => { const payload = item.payload as Record<string, unknown> | undefined; return <p key={index}><strong>{String(item.path ?? "File")}</strong>{typeof payload?.size === "number" ? ` · ${payload.size.toLocaleString()} bytes` : ""}{typeof payload?.text === "string" ? ` · ${payload.text.split("\n").length.toLocaleString()} lines` : ""}</p>; })}
    {changes.map((change, index) => <div key={index}><h3>{String(change.path ?? "Selected file")}</h3>{typeof change.diff === "string" ? <pre aria-label="Proposed diff">{change.diff}</pre> : <p className="coding-plan">{String(change.plan ?? "No change details returned.")}</p>}</div>)}
    {([ ["assumptions", "Assumptions"], ["warnings", "Warnings"], ["expected_checks", "Checks to run"] ] as const).map(([key, label]) => Array.isArray(value[key]) && value[key].length ? <div key={key}><h3>{label}</h3><ul>{(value[key] as unknown[]).map((item, index) => <li key={index}>{String(item)}</li>)}</ul></div> : null)}
    {kind === "proposal" ? <p>No files were changed. Review this proposal through the normal development workflow.</p> : null}
    <RawJson value={value} />
  </section>;
}

function EvidenceSummary({ value, label }: Readonly<{ value: Record<string, unknown>; label: string }>) {
  if ("pr" in value) {
    const summary = pullRequestEvidenceSummary(value);
    return <div className="final-fusion__source-empty"><strong>{summary.title || label}</strong><span>{humanize(summary.state)} · Checks: {summary.checks.passing} passing, {summary.checks.failing} failing, {summary.checks.pending} pending, {summary.checks.stale} stale · Reviews: {summary.reviews.approved} approved, {summary.reviews.changesRequested} changes requested, {summary.reviews.stale} stale</span><RawJson value={value} /></div>;
  }
  const payload = typeof value.payload === "object" && value.payload !== null ? value.payload as Record<string, unknown> : value;
  const state = payload.state ?? payload.status ?? value.state ?? "available";
  const title = payload.title ?? payload.name ?? payload.summary ?? label;
  const checks = Array.isArray(payload.checks) ? payload.checks.length : null;
  const reviews = Array.isArray(payload.reviews) ? payload.reviews.length : null;
  return <div className="final-fusion__source-empty"><strong>{String(title)}</strong><span>{humanize(state)}{checks !== null ? ` · ${checks} checks` : ""}{reviews !== null ? ` · ${reviews} reviews` : ""}</span><RawJson value={value} /></div>;
}

function PipelineSummary({ value }: Readonly<{ value: Record<string, unknown> }>) {
  const stages = Array.isArray(value.stages) ? value.stages as Record<string, unknown>[] : [];
  const partial = value.partial === true;
  const warnings = Array.isArray(value.warnings) ? value.warnings : [];
  const projectionLabel = partial ? "Partial" : "Server projection";
  const evidenceLabel = `${stages.length} reported stages${warnings.length ? ` · ${warnings.length} warnings` : ""}`;
  return <div><div className="final-fusion__source-empty"><strong>Pipeline {projectionLabel}</strong><span>{evidenceLabel}</span></div>{stages.map((stage, index) => <div className="final-fusion__source-empty" key={String(stage.id ?? stage.name ?? index)}><strong>{humanize(stage.title ?? stage.name, `Stage ${index + 1}`)}</strong><span>{humanize(stage.state ?? stage.status)}{stage.reason ? ` · ${humanize(stage.reason)}` : ""}</span></div>)}{warnings.length ? <div className="coding-action-result"><strong>Evidence gaps</strong><ul>{warnings.map((warning, index) => <li key={index}>{humanize(warning)}</li>)}</ul></div> : null}<RawJson value={value} /></div>;
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
  const [rendered, setRendered] = useState(true);
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
  const [fileLoading, setFileLoading] = useState(false);
  const [fileLoaded, setFileLoaded] = useState(false);
  const [searchState, setSearchState] = useState<"idle" | "loading" | "done">("idle");
  const [pendingAction, setPendingAction] = useState<"inspect" | "context" | "proposal" | null>(null);
  const [repositoryErrors, setRepositoryErrors] = useState<RepositoryErrors>(EMPTY_REPOSITORY_ERRORS);
  const fileReadGeneration = useRef(0);
  const prEvidenceGeneration = useRef(0);
  const proposalGeneration = useRef(0);
  const contextPreviewGeneration = useRef(0);
  const inspectGeneration = useRef(0);
  const refreshGeneration = useRef(0);
  const treeReadGeneration = useRef(0);
  const searchGeneration = useRef(0);

  const resolvedSha = truth?.resolved_sha ?? null;
  const anyPartial = truth?.partial || Object.values(partial).some(Boolean);
  const repositoryReadError = repositoryErrors.repository ?? repositoryErrors.tree;
  const evidenceError = repositoryErrors.file ?? repositoryErrors.search ?? repositoryErrors.pr ?? repositoryErrors.checks ?? repositoryErrors.reviews;
  const jarvisError = repositoryErrors.inspect ?? repositoryErrors.context ?? repositoryErrors.proposal;
  const setRepositoryError = (key: keyof RepositoryErrors, value: string | null) => {
    setRepositoryErrors((current) => ({ ...current, [key]: value }));
  };

  const clearSelectedEvidence = () => {
    fileReadGeneration.current += 1;
    prEvidenceGeneration.current += 1;
    proposalGeneration.current += 1;
    contextPreviewGeneration.current += 1;
    inspectGeneration.current += 1;
    setSelectedPath("");
    setSafeUrl(null);
    setPreview("");
    setFileLoading(false); setFileLoaded(false); setSearchState("idle"); setPendingAction(null);
    setMatches([]);
    setPrEvidence(null);
    setPartial(EMPTY_PARTIAL);
    setInspectResult(null);
    setContextBinding(null);
    setProposal(null);
    setRepositoryErrors(EMPTY_REPOSITORY_ERRORS);
  };

  const refresh = async () => {
    const requestGeneration = ++refreshGeneration.current;
    const requestTreeGeneration = ++treeReadGeneration.current;
    searchGeneration.current += 1;
    setBusy(true); setTruth(null); setTree([]); clearSelectedEvidence();
    setTreePath("");
    try {
      const nextTruth = await readRepositoryRef(repository, ref);
      if (refreshGeneration.current !== requestGeneration) return;
      setTruth(nextTruth);
      const exactRef = nextTruth.resolved_sha;
      if (!exactRef || !/^[0-9a-f]{40}$/.test(exactRef)) throw new Error("missing_exact_sha");
      const nextTree = await readRepositoryTree(repository, exactRef);
      if (refreshGeneration.current !== requestGeneration || treeReadGeneration.current !== requestTreeGeneration) return;
      const entries = nextTree.payload.entries;
      setTree(Array.isArray(entries) ? entries as TreeEntry[] : []);
      setPartial((current) => ({ ...current, tree: nextTree.partial }));
    } catch (cause) {
      if (refreshGeneration.current === requestGeneration) setRepositoryError("repository", errorText(cause));
    } finally {
      if (refreshGeneration.current === requestGeneration) setBusy(false);
    }
  };

  useEffect(() => { void refresh(); }, []);
  useEffect(() => {
    contextPreviewGeneration.current += 1;
    inspectGeneration.current += 1;
    proposalGeneration.current += 1;
    setInspectResult(null);
    setContextBinding(null);
    setProposal(null); setPendingAction(null);
    setRepositoryErrors((current) => ({ ...current, inspect: null, context: null, proposal: null }));
  }, [workspaceId]);

  const openFile = async (path: string) => {
    const requestGeneration = ++fileReadGeneration.current;
    proposalGeneration.current += 1;
    contextPreviewGeneration.current += 1;
    inspectGeneration.current += 1;
    setSelectedPath(path); setSafeUrl(null); setPreview(""); setContextBinding(null); setInspectResult(null); setProposal(null); setPendingAction(null); setFileLoaded(false); setFileLoading(true);
    setRepositoryErrors((current) => ({ ...current, file: null, inspect: null, context: null, proposal: null }));
    setPartial((current) => ({ ...current, file: false }));
    const requestSha = resolvedSha;
    if (!requestSha) { setRepositoryError("file", "missing_exact_sha"); setFileLoading(false); return; }
    try {
      const [result, navigation] = await Promise.all([
        readRepositoryFile(repository, requestSha, path),
        readSafeGithubUrl(repository, requestSha, path).catch(() => null)
      ]);
      if (fileReadGeneration.current !== requestGeneration) return;
      setPreview(typeof result.payload.text === "string" ? result.payload.text : "");
      setFileLoaded(true);
      setSafeUrl(typeof navigation?.payload.url === "string" ? navigation.payload.url : null);
      setPartial((current) => ({ ...current, file: result.partial }));
    } catch (cause) {
      if (fileReadGeneration.current === requestGeneration) setRepositoryError("file", errorText(cause));
    } finally {
      if (fileReadGeneration.current === requestGeneration) setFileLoading(false);
    }
  };

  const openDirectory = async (path: string) => {
    const requestSha = resolvedSha;
    if (!requestSha) { setRepositoryError("tree", "missing_exact_sha"); return; }
    const requestGeneration = ++treeReadGeneration.current;
    setTree([]); setRepositoryError("tree", null);
    setPartial((current) => ({ ...current, tree: false }));
    try {
      const result = await readRepositoryTree(repository, requestSha, path);
      if (treeReadGeneration.current !== requestGeneration) return;
      const entries = result.payload.entries;
      setTree(Array.isArray(entries) ? entries as TreeEntry[] : []);
      setTreePath(path);
      setPartial((current) => ({ ...current, tree: result.partial }));
    } catch (cause) {
      if (treeReadGeneration.current === requestGeneration) setRepositoryError("tree", errorText(cause));
    }
  };

  const runSearch = async () => {
    const requestLiteral = literal.trim();
    const requestSha = resolvedSha;
    if (!requestLiteral || !requestSha) return;
    const requestGeneration = ++searchGeneration.current;
    setSearchState("loading");
    setMatches([]); setRepositoryError("search", null); setPartial((current) => ({ ...current, search: false }));
    try {
      const result = await searchRepository(repository, requestSha, requestLiteral);
      if (searchGeneration.current !== requestGeneration) return;
      setMatches(Array.isArray(result.payload.matches) ? result.payload.matches as SearchMatch[] : []);
      setSearchState("done");
      setPartial((current) => ({ ...current, search: result.partial }));
    } catch (cause) {
      if (searchGeneration.current === requestGeneration) { setRepositoryError("search", errorText(cause)); setSearchState("idle"); }
    }
  };

  const loadPr = async () => {
    const prNumber = canonicalPrNumber(prInput);
    if (prNumber === null) { setRepositoryError("pr", "invalid_pr_number"); return; }
    const requestGeneration = ++prEvidenceGeneration.current;
    setPrEvidence(null);
    setRepositoryErrors((current) => ({ ...current, pr: null, checks: null, reviews: null }));
    setPartial((current) => ({ ...current, pr: false, checks: false, reviews: false }));
    try {
      const pr = await readPullRequest(repository, prNumber);
      if (prEvidenceGeneration.current !== requestGeneration) return;
      const headSha = exactSha(pr.payload.head_sha);
      if (headSha === "Unknown") throw new Error("missing_pr_head_sha");
      setPrEvidence({ pr: pr.payload });
      setPartial((current) => ({ ...current, pr: pr.partial }));
      const [checks, reviews] = await Promise.allSettled([
        readChecks(repository, prNumber, headSha),
        readReviews(repository, prNumber, headSha)
      ]);
      if (prEvidenceGeneration.current !== requestGeneration) return;
      if (checks.status === "fulfilled") {
        setPrEvidence((current) => ({ ...(current ?? {}), checks: checks.value.payload }));
        setPartial((current) => ({ ...current, checks: checks.value.partial }));
      } else {
        setRepositoryError("checks", errorText(checks.reason));
      }
      if (reviews.status === "fulfilled") {
        setPrEvidence((current) => ({ ...(current ?? {}), reviews: reviews.value.payload }));
        setPartial((current) => ({ ...current, reviews: reviews.value.partial }));
      } else {
        setRepositoryError("reviews", errorText(reviews.reason));
      }
    } catch (cause) {
      if (prEvidenceGeneration.current === requestGeneration) setRepositoryError("pr", errorText(cause));
    }
  };

  const inspect = async () => {
    const requestWorkspaceId = workspaceId;
    const requestSha = resolvedSha;
    const requestPath = selectedPath;
    if (!requestWorkspaceId || !requestSha || !requestPath) return;
    const requestGeneration = ++inspectGeneration.current;
    setInspectResult(null); setRepositoryError("inspect", null); setPendingAction("inspect");
    try {
      const result = await inspectCodingTarget({ workspace_id: requestWorkspaceId, repository, base_ref: ref, base_sha: requestSha, target_paths: [requestPath] });
      if (inspectGeneration.current !== requestGeneration) return;
      setInspectResult(result);
    } catch (cause) {
      if (inspectGeneration.current === requestGeneration) setRepositoryError("inspect", errorText(cause));
    } finally {
      if (inspectGeneration.current === requestGeneration) setPendingAction(null);
    }
  };

  const addContext = async () => {
    const requestWorkspaceId = workspaceId;
    const requestSha = resolvedSha;
    const requestPath = selectedPath;
    if (!requestWorkspaceId || !requestSha || !requestPath || partial.file) return;
    const requestGeneration = ++contextPreviewGeneration.current;
    proposalGeneration.current += 1;
    setContextBinding(null); setProposal(null);
    setRepositoryErrors((current) => ({ ...current, context: null, proposal: null }));
    setPendingAction("context");
    try {
      const next = await previewCodingContext({ workspace_id: requestWorkspaceId, repository, base_ref: ref, base_sha: requestSha, target_paths: [requestPath] });
      if (contextPreviewGeneration.current !== requestGeneration) return;
      if (next.state !== "current" || !next.context_digest || !next.added_context_refs?.length) {
        setRepositoryError("context", next.reason ?? "context_preview_refused");
        return;
      }
      proposalGeneration.current += 1;
      setProposal(null);
      setContextBinding(next);
    } catch (cause) {
      if (contextPreviewGeneration.current === requestGeneration) setRepositoryError("context", errorText(cause));
    } finally {
      if (contextPreviewGeneration.current === requestGeneration) setPendingAction(null);
    }
  };

  const removeContext = () => {
    contextPreviewGeneration.current += 1;
    proposalGeneration.current += 1;
    setContextBinding(null); setProposal(null); setPendingAction(null);
    setRepositoryErrors((current) => ({ ...current, context: null, proposal: null }));
  };

  const suggest = async () => {
    const requestSha = resolvedSha;
    const requestPath = selectedPath;
    const requestIntent = intent.trim();
    const requestContextDigest = contextBinding?.context_digest ?? null;
    if (!workspaceId || !requestSha || !requestPath || !requestIntent) return;
    const requestGeneration = ++proposalGeneration.current;
    setProposal(null); setRepositoryError("proposal", null); setPendingAction("proposal");
    try {
      const result = await suggestCodingModification({
        workspace_id: workspaceId,
        repository,
        base_ref: ref,
        base_sha: requestSha,
        target_paths: [requestPath],
        intent: requestIntent,
        added_context_refs: contextBinding?.added_context_refs,
        expected_context_digest: requestContextDigest,
        expected_checks: []
      });
      if (proposalGeneration.current !== requestGeneration) return;
      setProposal(result);
    } catch (cause) {
      if (proposalGeneration.current === requestGeneration) setRepositoryError("proposal", errorText(cause));
    } finally {
      if (proposalGeneration.current === requestGeneration) setPendingAction(null);
    }
  };

  return <div className="final-fusion__workbench final-fusion__workbench--coding" data-testid="coding-repository-surface">
    <Panel title="Repository" status={busy ? "Loading" : repositoryReadError ? "Read error" : anyPartial ? "Partial" : truth ? "Exact READ" : "Unknown"}>
      <div className="final-fusion__repo-status"><div><strong>{repository}</strong><span>Target branch · {ref}</span></div><span className={resolvedSha ? "" : "final-fusion__unknown"}>{truth ? "Exact repository state available" : "Repository state unknown"}</span></div>
      {truth ? <TechnicalDetails><p>Requested ref · {ref}</p><p>Resolved commit · {resolvedSha ?? "Unknown"}</p><RawJson value={truth} /></TechnicalDetails> : null}
      <div className="final-fusion__toolbar-line"><span>Repository files</span><button type="button" onClick={() => void refresh()} disabled={busy}>Refresh repository</button></div>
      {partialLabel(partial) ? <div className="final-fusion__source-empty" role="status"><strong>{partialLabel(partial)}</strong><span>Truncated evidence is not presented as complete.</span></div> : null}
      {repositoryReadError ? <div className="final-fusion__source-empty" role="status"><strong>Repository read refused / unavailable</strong><span>{readableReason(repositoryReadError)}</span></div> : null}
      <div className="final-fusion__toolbar-line"><input aria-label="Literal repository search" value={literal} onChange={(event) => { searchGeneration.current += 1; setLiteral(event.target.value); setSearchState("idle"); setMatches([]); setRepositoryError("search", null); setPartial((current) => ({ ...current, search: false })); }} onKeyDown={(event) => { if (event.key === "Enter") void runSearch(); }} placeholder="Search file contents" maxLength={512}/><button type="button" onClick={() => void runSearch()} disabled={!literal.trim() || !resolvedSha || searchState === "loading"}>Search</button></div>
      {repositoryErrors.search ? <div className="final-fusion__source-empty" role="status"><strong>Repository search refused / unavailable</strong><span>{readableReason(repositoryErrors.search)}</span></div> : null}
      {searchState !== "idle" ? <p className="coding-search-status" role="status">{searchState === "loading" ? "Searching repository…" : matches.length ? `${matches.length} matches${partial.search ? " · partial results" : ""}` : partial.search ? "No matches in the searched portion. Results are incomplete." : "No matching file contents found."}</p> : null}
      <div className="final-fusion__source-list">{matches.map((match, index) => <div className="final-fusion__disclosure-row final-fusion__disclosure-row--plain" key={`${match.path}:${match.offset}:${index}`}><button type="button" disabled={!match.path} onClick={() => match.path && void openFile(match.path)}>{match.path ?? "Unknown"} · line {match.line ?? "?"}</button></div>)}</div>
      <div className="final-fusion__toolbar-line">
        <span>Tree path · {treePath || "Root"}</span>
        <div><button type="button" onClick={() => void openDirectory("")} disabled={!resolvedSha || !treePath}>Root</button><button type="button" onClick={() => void openDirectory(treePath.split("/").slice(0, -1).join("/"))} disabled={!resolvedSha || !treePath}>Up</button></div>
      </div>
      <div className="final-fusion__source-list">{tree.length ? tree.map((entry) => entry.path ? <button type="button" className="final-fusion__disclosure-row final-fusion__disclosure-row--plain" key={entry.path} aria-current={selectedPath === entry.path ? "true" : undefined} onClick={() => entry.type === "file" ? void openFile(entry.path!) : entry.type === "dir" ? void openDirectory(entry.path!) : undefined} disabled={entry.type !== "file" && entry.type !== "dir"}><strong title={entry.path}>{entry.path.split("/").slice(-1)[0]}</strong><em>{entry.type ?? "unknown"}{typeof entry.size === "number" ? ` · ${entry.size} B` : ""}</em></button> : null) : <div className="final-fusion__source-empty"><strong>No current tree evidence</strong></div>}</div>
    </Panel>
    <Panel title="Repository Inspector" status={evidenceError ? "Read error" : anyPartial ? "PARTIAL · READ only" : "READ only"}>
      <div className="final-fusion__toolbar-line"><span>Selected path · {selectedPath || "None"}</span>{safeUrl ? <a href={safeUrl} target="_blank" rel="noreferrer">Open on GitHub</a> : null}</div>
      {selectedPath.endsWith(".md") && preview && <div className="file-view-tabs" role="group" aria-label="Markdown view"><button aria-pressed={rendered} onClick={() => setRendered(true)}>Rendered</button><button aria-pressed={!rendered} onClick={() => setRendered(false)}>Raw</button></div>}
      <div className="repository-file-viewport" tabIndex={0} aria-label="File content">{!selectedPath ? <div className="repository-empty"><h3>Open a file to begin</h3><p>Choose a file in the repository tree, or search for text inside files.</p></div> : fileLoading ? <p className="repository-empty" role="status">Loading file…</p> : repositoryErrors.file ? <p className="repository-empty">File content is unavailable. Reopen the file to retry.</p> : !preview ? <p className="repository-empty">This file contains no readable text.</p> : selectedPath.endsWith(".md") && rendered ? <article className="markdown-preview"><ReactMarkdown remarkPlugins={[remarkGfm]} components={{img: ({alt}) => <span>[Image: {alt || "image"} · open on GitHub]</span>}}>{preview}</ReactMarkdown></article> : <pre>{preview || "No readable text returned for this file."}</pre>}</div>
      {repositoryErrors.file ? <div className="final-fusion__source-empty" role="status"><strong>File preview refused / unavailable</strong><span>{readableReason(repositoryErrors.file)}</span></div> : null}
      <details className="repository-pr-evidence"><summary>Pull request evidence</summary><div className="final-fusion__toolbar-line"><input aria-label="Pull request number" inputMode="numeric" value={prInput} onChange={(event) => { prEvidenceGeneration.current += 1; setPrInput(event.target.value); setPrEvidence(null); setRepositoryErrors((current) => ({ ...current, pr: null, checks: null, reviews: null })); setPartial((current) => ({ ...current, pr: false, checks: false, reviews: false })); }} placeholder="PR number"/><button type="button" onClick={() => void loadPr()} disabled={!prInput}>Load PR evidence</button></div>
      {repositoryErrors.pr ? <div className="final-fusion__source-empty" role="status"><strong>PR evidence refused / unavailable</strong><span>{readableReason(repositoryErrors.pr)}</span></div> : null}
      {repositoryErrors.checks ? <div className="final-fusion__source-empty" role="status"><strong>Checks evidence refused / unavailable</strong><span>{readableReason(repositoryErrors.checks)}</span></div> : null}
      {repositoryErrors.reviews ? <div className="final-fusion__source-empty" role="status"><strong>Reviews evidence refused / unavailable</strong><span>{readableReason(repositoryErrors.reviews)}</span></div> : null}
      {prEvidence ? <EvidenceSummary value={prEvidence} label={`Pull request ${prInput}`} /> : null}</details>
    </Panel>
    <Panel title="Jarvis Coding" status={jarvisError || inspectResult?.state === "refused" || proposal?.state === "refused" ? "Action unavailable" : "Proposals for review"}>
      <div className="final-fusion__context-note">Select a file and describe the change you want. Suggestions remain proposals for review. The selected file is always supplied as target evidence; adding context binds it explicitly to this proposal.</div>
      {!workspaceId ? <p role="status">Select a workspace to inspect files or request proposals.</p> : !resolvedSha ? <p role="status">Repository evidence is unavailable. Refresh the repository before using Coding actions.</p> : null}
      <div className="final-fusion__toolbar-line"><button type="button" onClick={() => void inspect()} disabled={!workspaceId || !resolvedSha || !fileLoaded || partial.file || pendingAction !== null}>Inspect file</button><span>{pendingAction === "inspect" ? "Verifying file evidence…" : "Verify exact file evidence"}</span></div>
      {repositoryErrors.inspect ? <div className="final-fusion__source-empty" role="status"><strong>Inspect refused / unavailable</strong><span>{readableReason(repositoryErrors.inspect)}</span></div> : null}
      {inspectResult ? <ActionResult value={inspectResult} kind="inspect" /> : null}
      <div className="final-fusion__toolbar-line"><button type="button" onClick={() => void addContext()} disabled={!workspaceId || !resolvedSha || !fileLoaded || partial.file || pendingAction !== null || !!contextBinding}>Add to Jarvis context</button><span>{pendingAction === "context" ? "Verifying context…" : contextBinding?.context_digest ? `In context: ${selectedPath}` : "Browsing has not entered Jarvis context"}</span></div>
      {contextBinding ? <div className="coding-context-binding"><span>{contextBinding.target_paths?.join(", ") ?? selectedPath}<small>Commit {contextBinding.base_sha?.slice(0, 8)} · for this proposal</small></span><button type="button" onClick={removeContext} disabled={pendingAction === "inspect"}>Remove context</button></div> : null}
      {repositoryErrors.context ? <div className="final-fusion__source-empty" role="status"><strong>Context insertion refused / unavailable</strong><span>{readableReason(repositoryErrors.context)}</span></div> : null}
      <textarea aria-label="Suggest modification intent" rows={4} maxLength={4000} disabled={pendingAction !== null} value={intent} onChange={(event) => { proposalGeneration.current += 1; setProposal(null); setRepositoryError("proposal", null); setIntent(event.target.value); }} placeholder="Describe a bounded proposal for the selected path" />
      <button type="button" onClick={() => void suggest()} disabled={!workspaceId || !resolvedSha || !fileLoaded || partial.file || !intent.trim() || pendingAction !== null}>Suggest modification</button>
      {pendingAction === "proposal" ? <p role="status">Preparing a proposal for review…</p> : null}
      {repositoryErrors.proposal ? <div className="final-fusion__source-empty" role="status"><strong>Proposal refused / unavailable</strong><span>{readableReason(repositoryErrors.proposal)}</span></div> : null}
      {proposal ? <ActionResult value={proposal} kind="proposal" /> : null}
    </Panel>
  </div>;
}

function RuntimeSurface() {
  const [runtime, setRuntime] = useState<RuntimeTruth | null>(null);
  const [prInput, setPrInput] = useState("");
  const [specId, setSpecId] = useState("");
  const [pipeline, setPipeline] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const pipelineRequestGeneration = useRef(0);

  const refresh = async () => {
    setLoading(true); setRuntimeError(null); setRuntime(null);
    try { setRuntime(await readRuntimeTruth()); } catch (cause) { setRuntimeError(errorText(cause)); } finally { setLoading(false); }
  };
  useEffect(() => { void refresh(); }, []);

  const loadPipeline = async () => {
    const prNumber = canonicalPrNumber(prInput);
    const requestSpecId = canonicalSpecId(specId);
    if (prNumber === null || requestSpecId === null) { setPipelineError("invalid_pipeline_selection"); return; }
    const requestGeneration = ++pipelineRequestGeneration.current;
    setPipeline(null); setPipelineError(null);
    try {
      const result = await readPipelineState(CODING_REPOSITORY, prNumber, requestSpecId);
      if (pipelineRequestGeneration.current === requestGeneration) setPipeline(result);
    } catch (cause) {
      if (pipelineRequestGeneration.current === requestGeneration) setPipelineError(errorText(cause));
    }
  };

  const invalidatePipelineSelection = () => {
    pipelineRequestGeneration.current += 1;
    setPipeline(null);
    setPipelineError(null);
  };

  const startup: Record<string, unknown> = runtime?.startup ?? {};
  const live: Record<string, unknown> = runtime?.live ?? {};
  const remote: Record<string, unknown> = runtime?.remote ?? {};
  const localSha = exactSha(live.git_sha);
  const remoteSha = exactSha(remote.resolved_sha);
  const delta: Record<string, unknown> = runtime?.semantic_delta ?? {};
  const relation = runtime?.alignment ?? "unknown";
  const semanticDelta = runtimeDeltaSummary(delta, relation, typeof runtime?.reason === "string" ? runtime.reason : null);

  return <div className="final-fusion__workbench final-fusion__workbench--coding" data-testid="coding-runtime-surface">
    <Panel title="Runtime" status={loading ? "Loading" : runtimeError ? "Read error" : runtime?.observer_status ?? "Unknown"}>
      <div className="final-fusion__repo-status"><div><strong>JarvisOS runtime identity</strong><span>{CODING_REPOSITORY} · target {CODING_TARGET_REF}</span></div><span className={semanticDelta.relation === "unknown" ? "final-fusion__unknown" : ""}>{semanticDelta.relationship}</span></div>
      <section className="final-fusion__compare"><div className="final-fusion__version-card"><small>Running workspace</small><strong>{typeof live.branch === "string" ? live.branch : humanize(live.head_state, "Local runtime")}</strong><p>Process started at <code>{exactSha(startup.git_sha) === "Unknown" ? "unknown commit" : exactSha(startup.git_sha).slice(0, 12)}</code></p><p>Workspace now at <code>{localSha === "Unknown" ? "unknown commit" : localSha.slice(0, 12)}</code></p>{runtime?.worktree_changed_since_start ? <p className="coding-runtime-warning">Workspace changed since startup. The current files do not prove what the running process loaded.</p> : null}<p>Working tree · {humanize(live.dirty_state)}</p></div><div className="final-fusion__delta" aria-hidden="true">→</div><div className="final-fusion__version-card is-remote"><small>Tracked target</small><strong>{humanize(remote.requested_ref ?? CODING_TARGET_REF)}</strong><p>Remote commit · <code>{remoteSha === "Unknown" ? "Unknown" : remoteSha.slice(0, 12)}</code></p><p>{humanize(runtime?.remote_status, "Remote status unknown")}</p></div></section>
      <div className="final-fusion__summary-strip"><span>Remote ahead · {semanticDelta.aheadBy ?? "Unknown"}</span><span>Remote behind · {semanticDelta.behindBy ?? "Unknown"}</span><span>{semanticDelta.partial ? "Changed files shown" : "Changed files"} · {semanticDelta.status === "unavailable" || semanticDelta.status === "unknown" ? "Unknown" : semanticDelta.files.length}</span><span>Evidence · {semanticDelta.partial ? "Partial — file list is truncated" : humanize(semanticDelta.status)}</span></div>
      {semanticDelta.explanation ? <div className="final-fusion__context-note" role="status">{semanticDelta.explanation}</div> : null}
      {semanticDelta.files.length ? <div className="final-fusion__source-list">{semanticDelta.files.map((file) => <div className="final-fusion__source-empty" key={file.name}><strong>{file.name}</strong><span>{humanize(file.status, "Changed")}</span></div>)}</div> : null}
      <details className="coding-runtime-method"><summary>How this comparison is determined</summary><div className="final-fusion__context-note">Primary relationship comes from the canonical server-owned runtime alignment. Remote-ahead/remote-behind counts and changed files come from the server-owned semantic delta. The browser performs no SHA ancestry or cleanliness inference.</div></details>
      {runtime ? <TechnicalDetails><p>Runtime alignment code · {relation}</p><p>Local commit · {localSha}</p><p>Remote commit · {remoteSha}</p><p>Process startup identity · {exactSha(startup.git_sha)}</p><p>Root identity · {String(live.root_identity ?? startup.root_identity ?? "unknown")}</p><p>Observed at · {String(live.observed_at ?? "unknown")}</p><p>Remote observed at · {String(remote.observed_at ?? "unknown")}</p><p>Startup observed at · {String(startup.observed_at ?? "unknown")}</p><p>Provenance · {String(live.provenance ?? startup.provenance ?? "unknown")}</p><p>Dirty state · {String(live.dirty_state ?? "unknown")}</p><p>Reason · {String(runtime.reason ?? "none")}</p><p>Failure identity · {String(live.failure_code ?? startup.failure_code ?? "none")}</p><RawJson value={delta} /></TechnicalDetails> : null}
      {runtimeError ? <div className="final-fusion__source-empty" role="status"><strong>Runtime truth unavailable</strong><span>{readableReason(runtimeError)}</span></div> : null}
      <button type="button" onClick={() => void refresh()} disabled={loading}>Refresh runtime truth</button>
    </Panel>
    <Panel title="Development pipeline" status={pipelineError ? "Projection error" : pipeline ? "Reported evidence" : "Unselected"}>
      <div className="final-fusion__toolbar-line"><input aria-label="Pipeline PR number" inputMode="numeric" value={prInput} onChange={(event) => { setPrInput(event.target.value); invalidatePipelineSelection(); }} placeholder="PR number"/><input aria-label="Pipeline spec id" value={specId} onChange={(event) => { setSpecId(event.target.value); invalidatePipelineSelection(); }} placeholder="Spec id"/><button type="button" onClick={() => void loadPipeline()} disabled={!prInput || !specId}>Load pipeline state</button></div>
      {pipelineError ? <div className="final-fusion__source-empty" role="status"><strong>Pipeline projection refused / unavailable</strong><span>{readableReason(pipelineError)}</span></div> : null}
      {pipeline ? <PipelineSummary value={pipeline} /> : <div className="final-fusion__source-empty"><strong>No pipeline selection</strong><span>No synthetic stages are shown.</span></div>}
    </Panel>
  </div>;
}

export default function CodingWorkbench({ mode, workspaceId }: Props) {
  return mode === "repository" ? <RepositorySurface workspaceId={workspaceId} /> : <RuntimeSurface />;
}
