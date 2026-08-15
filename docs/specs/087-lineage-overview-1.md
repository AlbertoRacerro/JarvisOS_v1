# 087 — LINEAGE-OVERVIEW-1

Status: definition-complete; `docs/specs/STATUS.md` is authoritative.

Depends on: 050, 051, 083

Related merged foundations: 040, 042, 044, 070, 084, 085, 086

## Goal

Expose the already-authoritative 050 dependency/provenance graph and 051 freshness overlay as one early, read-only operator surface inside the 083 application shell.

087 answers, without creating new engineering truth:

- what supported records exist in the selected workspace;
- which records depend on which upstream authorities;
- which relationships are dependency versus provenance;
- whether a record is fresh or stale when 051 has an answer;
- the latest persisted invalidation path explaining stale state;
- which graph diagnostics make lineage incomplete, cyclic, malformed, dangling, or unsupported;
- enough bounded node metadata to inspect a selected graph record without opening the later full Engineering Data area.

087 does not recompute, promote, mutate, repair, bind, rerun, clear stale state, infer semantic equivalence, or implement an editable process flowsheet.

## Product boundary

This slice replaces the current `FlowsheetStage` placeholder with a lineage overview. The stage remains named **Flowsheet** in primary navigation because the shell contract is already stable, but the rendered surface must label itself clearly as **Lineage** / **Dependency & provenance** and must not imply an Aspen-like editable canvas.

The overview is a workstation surface, not a graph-authoring tool:

- primary stage: compact dependency/provenance overview;
- navigator contribution: workspace-local graph navigation and bounded filters;
- sidecar contribution: selected-node inspector and freshness explanation;
- dock: optional compact diagnostics summary only when useful; no permanent telemetry strip is required.

The visual direction follows the maintainer-approved technical workstation hierarchy already used by 083/085: dense, legible, desktop-first, light/off-white surfaces, natural leaf-green accent used selectively, thin separators, minimal shadows. This slice does not own global typography, palette, radius, iconography, motion, or visual-identity tokens.

## Existing backend authority

087 consumes existing 050/051 read APIs only.

### Graph

```http
GET /workspaces/{workspace_id}/flowsheet/graph
```

The response authority is 050, including:

- canonical `<kind>:<id>` node identity;
- deterministic nodes and edges;
- edge classes `dependency` and `provenance`;
- topological order and acyclic flag;
- diagnostics for unsupported, malformed and dangling references, cycles, manual bindings and bounded unresolved-reference detail.

Frontend code must not reconstruct lineage by joining unrelated endpoints or parsing arbitrary payloads.

### Node detail

```http
GET /workspaces/{workspace_id}/flowsheet/nodes/{node_ref}
```

The response authority is the shared 050 resolver. The frontend renders only fields supplied by that bounded response and never fetches raw record bodies to enrich the inspector in this slice.

### Freshness

```http
GET /workspaces/{workspace_id}/flowsheet/nodes/{node_ref}/freshness
```

The response authority is 051. Freshness is distinct from execution/lifecycle status. A successful historical run may be stale; the UI must never turn `stale` into `failed` or overwrite the node's stored status.

087 does not require the invalidation-detail endpoint for normal operation. The node-freshness response already carries the latest canonical invalidation path. A later surface may expose full invalidation history.

## Frontend contracts

Add strict TypeScript read models and client functions for the exact 050/051 responses. Do not weaken them to `Record<string, unknown>` where stable fields are already specified.

Minimum models:

```ts
type LineageNode = {
  ref: string;
  kind: string;
  id: string;
  label: string;
  status: string | null;
  origin: string | null;
  created_at: string | null;
  metadata: Record<string, string | number | boolean | null>;
};

type LineageEdge = {
  id: string;
  upstream_ref: string;
  downstream_ref: string;
  relation: string;
  edge_class: "dependency" | "provenance";
  authorities: string[];
  source_fields: string[];
};

type LineageGraph = {
  workspace_id: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
  topological_order: string[];
  is_acyclic: boolean;
  diagnostics: LineageDiagnostics;
};

type NodeFreshness = {
  record_ref: string;
  state: "fresh" | "stale";
  invalidation_count: number;
  latest_invalidation: null | {
    id: string;
    source_ref: string;
    replacement_ref: string;
    reason_code: string;
    path: string[];
    path_digest: string;
    created_at: string;
  };
};
```

If the exact merged backend model is narrower or names nullable fields differently, the implementation must derive its TypeScript contract from runtime/backend response models rather than forcing this illustrative shape.

## State ownership and request races

`FlowsheetStage` owns one workspace-local lineage state. The shell remains owner of `workspaceId` and `StageSelection`.

Required state:

- graph load state;
- selected canonical node ref or null;
- bounded view/filter state;
- selected node-detail load state;
- selected freshness load state;
- diagnostic visibility state only if a disclosure is used.

Selection uses the existing semantic record branch:

```ts
{
  kind: "record",
  ref: {
    resource: <mapped canonical resource>,
    workspaceId,
    recordId
  }
}
```

087 must not manufacture a `RecordRef` for canonical kinds that the existing selection resource taxonomy cannot represent. Such nodes remain locally selectable inside the lineage stage and inspectable through 050, but shell `StageSelection` stays null or preserves only an already-valid semantic selection. Do not expand the global selection taxonomy merely to make every graph kind fit unless a separately accepted contract requires it.

Every graph, node-detail and freshness request must be guarded against stale completion. At minimum, acceptance of a response requires the same workspace and selected node that initiated it. A workspace A → B → A race or node X → Y → X race must not let an older request overwrite the current state.

Changing workspace clears graph-derived local selection, detail and freshness before loading the new graph.

## Overview representation

The first 087 implementation must use the simplest representation that makes direction, class and selection unambiguous with current dependencies. It must not add a graph-layout library merely for visual polish.

Preferred minimum: an accessible, deterministic lineage list/adjacency workbench derived directly from ordered 050 nodes and edges, with enough visual connectors/grouping to read upstream → downstream relationships. A small native SVG layer is allowed only if it remains bounded, keyboard-accessible through equivalent controls/list semantics, and requires no new dependency.

Do not implement force-directed physics, freeform dragging, saved coordinates, minimaps, zoom engines, canvas hit testing, automatic clustering or a second layout state store in 087.

### Ordering

Use backend deterministic order as authority:

1. when acyclic, `topological_order` drives the main dependency sequence;
2. nodes not represented there remain visible in deterministic response order;
3. provenance-only edges do not alter dependency topological meaning;
4. cyclic graphs remain inspectable and are never reordered to pretend acyclicity.

Frontend sorting may group exact kinds or edge classes only when it preserves a stable deterministic tie-break by canonical ref.

### Edge semantics

Direction must be communicated as **upstream → downstream** and not by colour alone.

`dependency` and `provenance` must have distinct text labels or accessible semantics. The UI must not imply that every provenance edge means engineering invalidation. 051 traverses only its defined dependency relations plus the exact `executed_by` bridge; 087 must not invent freshness consequences from other provenance links.

## Navigator contribution

The navigator may provide only bounded read controls:

- search by visible node label or canonical ref;
- optional exact kind filter;
- optional edge-class visibility filter if both classes would otherwise be unreadable;
- node list using canonical identity as stable key.

Filters are presentation-only. They never change backend graph authority, freshness state or persisted data.

Search is case-insensitive over already-returned label/ref only. Do not search raw backend records or introduce a backend search endpoint for 087.

If filtering hides the currently selected node, local selection may remain and the inspector must make that state understandable, or selection may deterministically move to the first visible node. Pick one rule during implementation and cover it with a focused test; do not allow focus loss or stale sidecar content.

## Compact inspector

For the selected node, the sidecar renders:

- label;
- canonical ref and kind;
- bounded status/origin/created-at when present;
- allowlisted 050 metadata;
- freshness state;
- invalidation count;
- latest invalidation source → replacement relationship when stale;
- latest canonical invalidation path when stale;
- direct incoming/outgoing edge counts and a compact relationship list derived from the already-loaded graph.

The inspector must not render:

- engineering values or raw parameter payloads;
- prompts or model outputs;
- logs;
- filesystem paths;
- arbitrary JSON;
- hidden backend fields;
- fake confidence, severity, health, impact or recomputation estimates.

A stale node must say in plain language that it is stale because an accepted upstream Parameter was superseded, while preserving historical status separately.

## Diagnostics

Graph diagnostics are part of normal authority, not decorative telemetry.

The stage must visibly distinguish at least:

- complete acyclic graph;
- cyclic graph;
- unresolved/malformed/dangling/unsupported references present;
- graph request failed;
- empty graph.

Do not convert non-zero diagnostic counts into an invented overall health score.

Raw unresolved references may be rendered only to the extent already bounded and returned by 050. No client-side payload inspection is allowed to recover additional detail.

A cycle does not make the graph unusable. Show the cycle diagnostic and preserve deterministic inspection.

## Loading, error and partial-state behavior

Graph loading:

- retain no graph from a previous workspace;
- use an explicit loading state;
- failure gives a bounded retry action;
- empty success is distinct from failure.

Node detail/freshness loading:

- selection changes immediately identify the newly selected ref;
- detail/freshness from the old node must not remain presented as belonging to the new node;
- a detail failure does not erase the already-loaded graph;
- a freshness failure does not invent `fresh`; it renders freshness unavailable;
- `404` after graph load is treated as drift between reads: retain the graph context, explain that the node is no longer resolvable, and offer refresh rather than silently remapping it.

No automatic polling is required.

## Accessibility and layout

The slice inherits 070/083 contracts and must prove them on its own changed surface.

Required:

- all interactive nodes/filters/disclosures reachable by keyboard;
- visible focus;
- selected node indicated by semantics (`aria-current`, `aria-selected`, pressed state, or equivalent), not colour only;
- dependency/provenance distinction exposed in text/accessibility semantics;
- stale/fresh state not colour-only;
- reduced-motion compliance; no required motion is expected;
- at effective 200% zoom, the page has no global horizontal overflow;
- dense lineage content may scroll inside an explicitly bounded stage region instead of widening the page;
- long canonical refs, labels and metadata wrap or truncate with an accessible full-value affordance where needed;
- sidecar/dock closures from 083 remain usable and do not destroy stage state unexpectedly.

## Failure modes to test first

1. workspace A graph resolves after the operator has switched to B;
2. node X detail/freshness resolves after selection moved to Y;
3. A → B → A or X → Y → X lets the first request overwrite the later request;
4. graph contains a cycle;
5. graph contains diagnostics but remains otherwise usable;
6. graph contains a node kind that cannot map to `StageSelection`;
7. selected node disappears between graph and detail/freshness read;
8. freshness request fails or returns stale while stored execution status is succeeded;
9. long labels/refs cause page-level overflow at 200% zoom;
10. provenance edge is visually mistaken for a dependency/recalculation edge;
11. filters hide the selected/focused node;
12. empty workspace is mistaken for request failure.

## Likely implementation boundary

A bounded implementation should normally touch only:

- `frontend/src/api/client.ts` for strict 050/051 read models/functions;
- `frontend/src/stages/FlowsheetStage.tsx`;
- one or more small lineage-specific frontend components/helpers under `frontend/src/components/lineage/` when separation materially improves testability/readability;
- existing frontend stylesheet(s) for local lineage layout;
- one dependency-free conformance checker under `scripts/` if current frontend queue practice requires it;
- focused frontend/harness proof files already permitted by readiness;
- `docs/specs/STATUS.md` lifecycle updates.

Backend, schema, migrations, providers, workflows, package manifests, lockfiles and new npm dependencies are outside the default boundary.

If implementation proves an existing 050/051 read contract insufficient for a required acceptance criterion, stop runtime expansion and document the exact insufficiency before considering a separate minimum-necessary backend read-model amendment. Do not silently absorb backend scope into 087.

## Acceptance criteria

087 is complete only when all are true on one exact implementation head:

1. the Flowsheet primary stage renders a real workspace-scoped lineage overview from `GET .../flowsheet/graph` rather than the placeholder;
2. no frontend join or arbitrary payload parsing duplicates 050 graph authority;
3. dependency direction and dependency/provenance class are unambiguous without colour;
4. deterministic backend ordering is preserved and cyclic graphs remain inspectable;
5. selecting a node exposes only bounded 050 node detail plus 051 freshness and graph-derived relationship summary;
6. stale state remains distinct from historical execution/lifecycle status;
7. freshness failure is shown as unavailable, never coerced to fresh;
8. graph/node/freshness stale-response races are rejected for workspace and selection changes, including A → B → A and X → Y → X;
9. cross-workspace or disappeared-node reads do not leak or silently remap identity;
10. diagnostics, loading, error, empty and partial states are distinct and usable;
11. no mutation/recompute/promote/retry-run/stale-clear control exists in this slice;
12. no fake metrics, health scores, confidence or unsupported engineering state is rendered;
13. keyboard navigation, focus visibility, selected semantics, reduced motion and 200%-zoom/no-global-overflow requirements pass;
14. existing Model, Results, Review, BLUECAD and legacy-route behavior is preserved;
15. no backend/schema/dependency/workflow/provider/credential/global-visual-identity change is introduced;
16. exact-head CI, existing frontend preservation checkers, production build and any frozen browser proof from readiness are green;
17. rollback is deletion/reversion of the 087 frontend contribution and typed client additions, restoring the previous Flowsheet placeholder without data migration.

## Readiness questions

A separate readiness decision must freeze before runtime implementation:

- exact merged 050/051 response models as implemented, not merely historical spec prose;
- exact frontend file allow-list;
- whether native list/adjacency presentation is sufficient or a bounded native SVG is necessary;
- exact selected-node/filter/focus behavior;
- mapping policy from canonical graph kinds to existing `StageSelection` resources;
- exact checker/build/browser evidence;
- whether sidecar alone is sufficient for diagnostics or a closed-by-default dock contribution is justified;
- rollback and preservation gates.

Readiness must apply the minimum-necessary test to every proposed helper/component or visualization mechanism.

## Non-goals

087 does not implement:

- editable flowsheets, process streams, equipment placement or solver state;
- graph mutation, edge creation/deletion or saved layouts;
- automatic recomputation, reruns, scheduling or stale clearing;
- replacement promotion or proposal review;
- full Engineering Data search/navigation from spec 035;
- Runs workbench behavior from 088;
- analytics/comparison behavior from 089;
- AI threads or Jarvis sidecar behavior from 090/091;
- scene-component semantics or binding from 092/058c;
- global visual identity;
- graph-layout dependencies or a general graph framework.

## Acceptance outcome

After 087, an operator can open the existing Flowsheet stage and inspect the real persisted dependency/provenance structure of the current workspace, select a supported node, understand its bounded provenance and freshness explanation, and see incomplete/cyclic lineage explicitly.

The product still cannot edit a flowsheet or automatically recompute stale work.