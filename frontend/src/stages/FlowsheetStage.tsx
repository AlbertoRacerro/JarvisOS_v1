import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { listWorkspaces, type Workspace } from "../api/client";
import InlineNotice from "../components/ui/InlineNotice";
import Surface from "../components/ui/Surface";
import {
  getLineageFreshness,
  getLineageGraph,
  getLineageNode,
  LineageRequestError,
  type LineageEdge,
  type LineageFreshness,
  type LineageGraph,
  type LineageNode,
  type LineageNodeKind
} from "../components/lineage/api";
import {
  acceptsLineageResponse,
  nodeMatchesFilter,
  orderedLineageNodes,
  stageSelectionForLineageNode,
  type LineageRequestContext
} from "../components/lineage/state";
import type { PrimaryStageProps, ShellRegionContributions } from "./registry";

type LoadState = "idle" | "loading" | "ready" | "error";

type DetailState = Readonly<{
  status: LoadState;
  node: LineageNode | null;
  freshness: LineageFreshness | null;
  freshnessStatus: LoadState;
  drifted: boolean;
  message: string | null;
}>;

const EMPTY_DETAIL: DetailState = {
  status: "idle",
  node: null,
  freshness: null,
  freshnessStatus: "idle",
  drifted: false,
  message: null
};

function FlowsheetStage({ workspaceId, onWorkspaceChange, onSelectionChange, onShellRegionsChange }: PrimaryStageProps) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceState, setWorkspaceState] = useState<LoadState>("loading");
  const [workspaceMessage, setWorkspaceMessage] = useState<string | null>(null);
  const [graph, setGraph] = useState<LineageGraph | null>(null);
  const [graphState, setGraphState] = useState<LoadState>(workspaceId ? "loading" : "idle");
  const [graphMessage, setGraphMessage] = useState<string | null>(null);
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const [detail, setDetail] = useState<DetailState>(EMPTY_DETAIL);
  const [query, setQuery] = useState("");
  const [kindFilter, setKindFilter] = useState<LineageNodeKind | "all">("all");
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);

  const workspaceDiscoveryGeneration = useRef(0);
  const graphGeneration = useRef(0);
  const detailGeneration = useRef(0);
  const freshnessGeneration = useRef(0);
  const currentGraphRequest = useRef<LineageRequestContext | null>(null);
  const currentDetailRequest = useRef<LineageRequestContext | null>(null);
  const currentFreshnessRequest = useRef<LineageRequestContext | null>(null);
  const workspaceRef = useRef(workspaceId);
  const selectedRefRef = useRef(selectedRef);
  workspaceRef.current = workspaceId;
  selectedRefRef.current = selectedRef;

  const clearNodeState = useCallback(() => {
    currentDetailRequest.current = null;
    currentFreshnessRequest.current = null;
    setDetail(EMPTY_DETAIL);
  }, []);

  const publishSelection = useCallback((node: LineageNode | null) => {
    if (!workspaceRef.current || !node) {
      onSelectionChange(null);
      return;
    }
    onSelectionChange(stageSelectionForLineageNode(workspaceRef.current, node));
  }, [onSelectionChange]);

  const selectNode = useCallback((node: LineageNode | null) => {
    currentDetailRequest.current = null;
    currentFreshnessRequest.current = null;
    selectedRefRef.current = node?.ref ?? null;
    setSelectedRef(node?.ref ?? null);
    setDetail(node ? { ...EMPTY_DETAIL, status: "loading", freshnessStatus: "loading" } : EMPTY_DETAIL);
    publishSelection(node);
  }, [publishSelection]);

  const clearGraphDerivedState = useCallback((nextGraphState: LoadState) => {
    currentGraphRequest.current = null;
    graphGeneration.current += 1;
    detailGeneration.current += 1;
    freshnessGeneration.current += 1;
    setGraph(null);
    setGraphState(nextGraphState);
    setGraphMessage(null);
    setSelectedRef(null);
    selectedRefRef.current = null;
    clearNodeState();
    onSelectionChange(null);
    setQuery("");
    setKindFilter("all");
    setDiagnosticsOpen(false);
  }, [clearNodeState, onSelectionChange]);

  const requestWorkspaceChange = useCallback((nextWorkspaceId: string | null) => {
    if (nextWorkspaceId === workspaceRef.current) return;
    clearGraphDerivedState(nextWorkspaceId ? "loading" : "idle");
    workspaceRef.current = nextWorkspaceId;
    onWorkspaceChange(nextWorkspaceId);
  }, [clearGraphDerivedState, onWorkspaceChange]);

  const loadGraph = useCallback(async (targetWorkspaceId: string) => {
    const request: LineageRequestContext = {
      generation: ++graphGeneration.current,
      workspaceId: targetWorkspaceId,
      nodeRef: null
    };
    currentGraphRequest.current = request;
    setGraphState("loading");
    setGraphMessage(null);
    try {
      const nextGraph = await getLineageGraph(targetWorkspaceId);
      if (!acceptsLineageResponse(currentGraphRequest.current, request) || workspaceRef.current !== targetWorkspaceId) return;
      setGraph(nextGraph);
      setGraphState("ready");
      const currentRef = selectedRefRef.current;
      const retained = currentRef ? nextGraph.nodes.find((node) => node.ref === currentRef) ?? null : null;
      const first = orderedLineageNodes(nextGraph)[0] ?? null;
      selectNode(retained ?? first);
    } catch (error) {
      if (!acceptsLineageResponse(currentGraphRequest.current, request) || workspaceRef.current !== targetWorkspaceId) return;
      setGraph(null);
      setGraphState("error");
      setGraphMessage(error instanceof Error ? error.message : "Lineage graph unavailable.");
      selectNode(null);
    }
  }, [selectNode]);

  useEffect(() => {
    const generation = ++workspaceDiscoveryGeneration.current;
    setWorkspaceState("loading");
    setWorkspaceMessage(null);
    void listWorkspaces().then((items) => {
      if (workspaceDiscoveryGeneration.current !== generation) return;
      setWorkspaces(items);
      setWorkspaceState("ready");
      if (!workspaceRef.current && items.length > 0) {
        requestWorkspaceChange(items[0].id);
      }
    }).catch((error: unknown) => {
      if (workspaceDiscoveryGeneration.current !== generation) return;
      setWorkspaces([]);
      setWorkspaceState("error");
      setWorkspaceMessage(error instanceof Error ? error.message : "Workspace discovery failed.");
    });
    return () => {
      workspaceDiscoveryGeneration.current += 1;
    };
  }, [requestWorkspaceChange]);

  useEffect(() => {
    clearGraphDerivedState(workspaceId ? "loading" : "idle");
    if (workspaceId) void loadGraph(workspaceId);
  }, [clearGraphDerivedState, loadGraph, workspaceId]);

  useEffect(() => {
    if (!workspaceId || !selectedRef) {
      clearNodeState();
      return;
    }
    const nodeRef = selectedRef;
    const detailRequest: LineageRequestContext = {
      generation: ++detailGeneration.current,
      workspaceId,
      nodeRef
    };
    const freshnessRequest: LineageRequestContext = {
      generation: ++freshnessGeneration.current,
      workspaceId,
      nodeRef
    };
    currentDetailRequest.current = detailRequest;
    currentFreshnessRequest.current = freshnessRequest;
    setDetail({ ...EMPTY_DETAIL, status: "loading", freshnessStatus: "loading" });

    void getLineageNode(workspaceId, nodeRef).then((node) => {
      if (!acceptsLineageResponse(currentDetailRequest.current, detailRequest)) return;
      if (workspaceRef.current !== workspaceId || selectedRefRef.current !== nodeRef) return;
      setDetail((current) => ({ ...current, status: "ready", node, drifted: false, message: null }));
    }).catch((error: unknown) => {
      if (!acceptsLineageResponse(currentDetailRequest.current, detailRequest)) return;
      if (workspaceRef.current !== workspaceId || selectedRefRef.current !== nodeRef) return;
      const drifted = error instanceof LineageRequestError && error.status === 404;
      setDetail((current) => ({
        ...current,
        status: "error",
        node: null,
        drifted,
        message: drifted ? "This graph node is no longer resolvable. Refresh lineage to reconcile the read." : error instanceof Error ? error.message : "Node detail unavailable."
      }));
    });

    void getLineageFreshness(workspaceId, nodeRef).then((freshness) => {
      if (!acceptsLineageResponse(currentFreshnessRequest.current, freshnessRequest)) return;
      if (workspaceRef.current !== workspaceId || selectedRefRef.current !== nodeRef) return;
      setDetail((current) => ({ ...current, freshnessStatus: "ready", freshness }));
    }).catch((error: unknown) => {
      if (!acceptsLineageResponse(currentFreshnessRequest.current, freshnessRequest)) return;
      if (workspaceRef.current !== workspaceId || selectedRefRef.current !== nodeRef) return;
      setDetail((current) => ({
        ...current,
        freshnessStatus: "error",
        freshness: null,
        message: current.message ?? (error instanceof LineageRequestError && error.status === 404
          ? "Freshness is unavailable because the selected graph node changed between reads."
          : "Freshness is unavailable for this node.")
      }));
    });
  }, [clearNodeState, selectedRef, workspaceId]);

  const orderedNodes = useMemo(() => graph ? orderedLineageNodes(graph) : [], [graph]);
  const visibleNodes = useMemo(
    () => orderedNodes.filter((node) => nodeMatchesFilter(node, query, kindFilter)),
    [kindFilter, orderedNodes, query]
  );
  const selectedGraphNode = useMemo(
    () => graph?.nodes.find((node) => node.ref === selectedRef) ?? null,
    [graph, selectedRef]
  );
  const selectedHidden = Boolean(selectedGraphNode && !visibleNodes.some((node) => node.ref === selectedGraphNode.ref));
  const kinds = useMemo(
    () => Array.from(new Set((graph?.nodes ?? []).map((node) => node.kind))).sort(),
    [graph]
  );
  const relationships = useMemo(
    () => selectedRef && graph ? graph.edges.filter((edge) => edge.upstream_ref === selectedRef || edge.downstream_ref === selectedRef) : [],
    [graph, selectedRef]
  );

  const navigator = useMemo<ReactNode>(() => (
    <div className="lineage-navigator">
      <label>
        Workspace
        <select
          value={workspaceId ?? ""}
          onChange={(event) => requestWorkspaceChange(event.target.value || null)}
          disabled={workspaceState === "loading" || workspaces.length === 0}
        >
          <option value="">Select workspace</option>
          {workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
        </select>
      </label>
      {workspaceState === "loading" && <p>Loading workspaces…</p>}
      {workspaceState === "error" && <p className="error-banner">Workspace discovery failed: {workspaceMessage ?? "Request failed."}</p>}
      {workspaceState === "ready" && workspaces.length === 0 && <p>No workspaces are available.</p>}
      <label>
        Search lineage
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Label or canonical ref" disabled={!workspaceId} />
      </label>
      <label>
        Record kind
        <select value={kindFilter} onChange={(event) => setKindFilter(event.target.value as LineageNodeKind | "all")} disabled={!workspaceId}>
          <option value="all">All kinds</option>
          {kinds.map((kind) => <option key={kind} value={kind}>{humanize(kind)}</option>)}
        </select>
      </label>
      {selectedHidden && <p className="panel-subtitle">Selected node is hidden by the current filter.</p>}
      <div aria-label="Lineage nodes">
        {visibleNodes.map((node) => (
          <button
            key={node.ref}
            type="button"
            className={node.ref === selectedRef ? "bluecad-candidate active" : "bluecad-candidate"}
            aria-pressed={node.ref === selectedRef}
            onClick={() => selectNode(node)}
          >
            <strong>{node.label}</strong>
            <small>{node.ref}</small>
          </button>
        ))}
      </div>
      {graphState === "ready" && orderedNodes.length > 0 && visibleNodes.length === 0 && <p>No nodes match the current filter.</p>}
    </div>
  ), [graphState, kindFilter, kinds, orderedNodes.length, query, requestWorkspaceChange, selectNode, selectedHidden, selectedRef, visibleNodes, workspaceId, workspaceMessage, workspaceState, workspaces]);

  const sidecar = useMemo<ReactNode>(() => (
    <LineageInspector
      node={detail.node ?? selectedGraphNode}
      detail={detail}
      relationships={relationships}
    />
  ), [detail, relationships, selectedGraphNode]);

  useEffect(() => {
    const contributions: ShellRegionContributions = { navigator, sidecar };
    onShellRegionsChange(contributions);
  }, [navigator, onShellRegionsChange, sidecar]);

  useEffect(() => () => {
    workspaceDiscoveryGeneration.current += 1;
    currentGraphRequest.current = null;
    currentDetailRequest.current = null;
    currentFreshnessRequest.current = null;
    onShellRegionsChange({});
  }, [onShellRegionsChange]);

  if (!workspaceId) {
    const emptyNotice = workspaceState === "loading"
      ? <InlineNotice tone="neutral">Loading workspaces…</InlineNotice>
      : workspaceState === "error"
        ? <InlineNotice tone="danger">Workspace discovery failed: {workspaceMessage ?? "Request failed."}</InlineNotice>
        : workspaces.length === 0
          ? <InlineNotice tone="neutral">No workspaces are available.</InlineNotice>
          : <InlineNotice tone="neutral">Select a workspace to inspect lineage.</InlineNotice>;
    return (
      <section className="shell-placeholder" aria-labelledby="flowsheet-stage-title">
        <div className="page-header"><p className="eyebrow">Lineage</p><h1 id="flowsheet-stage-title">Dependency & provenance</h1></div>
        {emptyNotice}
      </section>
    );
  }

  return (
    <section className="shell-placeholder" aria-labelledby="flowsheet-stage-title">
      <div className="page-header">
        <div>
          <p className="eyebrow">Lineage</p>
          <h1 id="flowsheet-stage-title">Dependency & provenance</h1>
          <p className="panel-subtitle">Read-only engineering lineage. Upstream → downstream; provenance does not imply recomputation.</p>
        </div>
        <button type="button" className="secondary-button" onClick={() => void loadGraph(workspaceId)} disabled={graphState === "loading"}>Refresh</button>
      </div>

      {graphState === "loading" && <Surface as="div" className="shell-placeholder__surface"><p>Loading lineage graph…</p></Surface>}
      {graphState === "error" && (
        <Surface as="div" className="shell-placeholder__surface">
          <InlineNotice tone="danger">{graphMessage ?? "Lineage graph unavailable."}</InlineNotice>
          <button type="button" onClick={() => void loadGraph(workspaceId)}>Retry</button>
        </Surface>
      )}
      {graphState === "ready" && graph && graph.nodes.length === 0 && (
        <Surface as="div" className="shell-placeholder__surface"><InlineNotice tone="neutral">This workspace has no lineage records yet.</InlineNotice></Surface>
      )}
      {graphState === "ready" && graph && graph.nodes.length > 0 && (
        <>
          <LineageDiagnostics graph={graph} open={diagnosticsOpen} onToggle={() => setDiagnosticsOpen((value) => !value)} />
          <Surface as="div" className="shell-placeholder__surface">
            <div role="list" aria-label="Dependency and provenance overview">
              {orderedNodes.map((node) => (
                <LineageRow
                  key={node.ref}
                  node={node}
                  selected={node.ref === selectedRef}
                  incoming={graph.edges.filter((edge) => edge.downstream_ref === node.ref)}
                  outgoing={graph.edges.filter((edge) => edge.upstream_ref === node.ref)}
                  onSelect={() => selectNode(node)}
                />
              ))}
            </div>
          </Surface>
        </>
      )}
    </section>
  );
}

function LineageRow({ node, selected, incoming, outgoing, onSelect }: {
  node: LineageNode;
  selected: boolean;
  incoming: LineageEdge[];
  outgoing: LineageEdge[];
  onSelect(): void;
}) {
  return (
    <article role="listitem" className="panel-card">
      <div className="button-row">
        <button type="button" className="secondary-button" aria-pressed={selected} onClick={onSelect}>{node.label}</button>
        <span className="status-pill">{humanize(node.kind)}</span>
        {node.status && <span>{node.status}</span>}
      </div>
      <p className="panel-subtitle">{node.ref}</p>
      <RelationshipSummary label="Upstream" edges={incoming} direction="incoming" />
      <RelationshipSummary label="Downstream" edges={outgoing} direction="outgoing" />
    </article>
  );
}

function RelationshipSummary({ label, edges, direction }: { label: string; edges: LineageEdge[]; direction: "incoming" | "outgoing" }) {
  if (edges.length === 0) return <p><strong>{label}:</strong> none</p>;
  return (
    <div>
      <strong>{label}:</strong>
      <ul>
        {edges.map((edge) => (
          <li key={edge.id}>
            <span>{direction === "incoming" ? edge.upstream_ref : edge.downstream_ref}</span>
            {" · "}<strong>{edge.edge_class}</strong>{" · "}{edge.relation}
          </li>
        ))}
      </ul>
    </div>
  );
}

function LineageDiagnostics({ graph, open, onToggle }: { graph: LineageGraph; open: boolean; onToggle(): void }) {
  const diagnostics = graph.diagnostics;
  const issueCount = diagnostics.unsupported_reference_count
    + diagnostics.malformed_reference_count
    + diagnostics.dangling_reference_count
    + diagnostics.cycle_count;
  return (
    <Surface as="div" className="shell-placeholder__surface">
      <div className="button-row">
        <strong>{graph.is_acyclic ? "Acyclic dependency graph" : "Cycles present"}</strong>
        <button type="button" className="secondary-button" aria-expanded={open} onClick={onToggle}>
          Diagnostics ({issueCount})
        </button>
      </div>
      {open && (
        <div>
          <p>Unsupported {diagnostics.unsupported_reference_count} · malformed {diagnostics.malformed_reference_count} · dangling {diagnostics.dangling_reference_count} · cycles {diagnostics.cycle_count} · manual bindings {diagnostics.manual_binding_count}</p>
          {diagnostics.unresolved_references.length > 0 && <ul>{diagnostics.unresolved_references.map((item, index) => <li key={`${item.owner_ref}-${item.source_field}-${index}`}>{item.code}: {item.owner_ref} / {item.source_field}{item.raw_ref ? ` → ${item.raw_ref}` : ""}</li>)}</ul>}
          {diagnostics.cycles.length > 0 && <ul>{diagnostics.cycles.map((cycle, index) => <li key={index}>Cycle: {cycle.join(" → ")}</li>)}</ul>}
        </div>
      )}
    </Surface>
  );
}

function LineageInspector({ node, detail, relationships }: { node: LineageNode | null; detail: DetailState; relationships: LineageEdge[] }) {
  if (!node) return <p>{detail.status === "loading" ? "Loading selected node…" : "Select a lineage node to inspect it."}</p>;
  const freshness = detail.freshness;
  const incoming = relationships.filter((edge) => edge.downstream_ref === node.ref);
  const outgoing = relationships.filter((edge) => edge.upstream_ref === node.ref);
  return (
    <div>
      <h3>{node.label}</h3>
      <p className="panel-subtitle">{node.ref}</p>
      <dl className="details">
        <div><dt>Kind</dt><dd>{humanize(node.kind)}</dd></div>
        <div><dt>Status</dt><dd>{node.status ?? "Unavailable"}</dd></div>
        <div><dt>Origin</dt><dd>{node.origin ?? "Unavailable"}</dd></div>
        <div><dt>Created</dt><dd>{node.created_at ?? "Unavailable"}</dd></div>
        <div><dt>Freshness</dt><dd>{detail.freshnessStatus === "loading" ? "Loading…" : detail.freshnessStatus === "error" ? "Unavailable" : freshness?.state ?? "Unavailable"}</dd></div>
      </dl>
      {detail.drifted && <InlineNotice tone="warning">{detail.message ?? "Node changed between reads."}</InlineNotice>}
      {!detail.drifted && detail.message && <InlineNotice tone="warning">{detail.message}</InlineNotice>}
      {freshness?.state === "stale" && (
        <InlineNotice tone="warning">
          This record is stale because accepted upstream authority was superseded. Historical status remains {node.status ?? "unavailable"}.
        </InlineNotice>
      )}
      {freshness && <p>Invalidations: {freshness.invalidation_count}</p>}
      {freshness?.latest_invalidation && (
        <div>
          <p><strong>Latest invalidation:</strong> {freshness.latest_invalidation.source_ref} → {freshness.latest_invalidation.replacement_ref}</p>
          {freshness.latest_invalidation.reason_code && <p>Reason: {freshness.latest_invalidation.reason_code}</p>}
          {freshness.latest_invalidation.path && <p>Path: {freshness.latest_invalidation.path.join(" → ")}</p>}
        </div>
      )}
      {Object.keys(node.metadata).length > 0 && (
        <div><h4>Metadata</h4><dl className="details">{Object.entries(node.metadata).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value === null ? "—" : String(value)}</dd></div>)}</dl></div>
      )}
      <h4>Direct relationships</h4>
      <p>{incoming.length} incoming · {outgoing.length} outgoing</p>
      {relationships.length > 0 && <ul>{relationships.map((edge) => <li key={edge.id}>{edge.upstream_ref} → {edge.downstream_ref} · <strong>{edge.edge_class}</strong> · {edge.relation}</li>)}</ul>}
    </div>
  );
}

function humanize(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default FlowsheetStage;
