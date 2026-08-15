# Spec 089 — ANALYTICS-DOCK-1

**Definition status:** complete definition; registry remains `planned` until a separate readiness decision.

**Depends on:** 035 ENGINEERING-DATA-1, 083 APP-SHELL-1, 087 LINEAGE-OVERVIEW-1, 088 RUNS-WORKBENCH-1.

**Target path:** `docs/specs/089-analytics-dock-1.md`

**Implementation PR:** none until readiness promotes 089 to `ready`.

---

## 1. Purpose

Phase 3 already exposes real persisted runs, their bindings/results/logs/artifacts, lineage/freshness, and searchable engineering records. The shell also already owns one transient, closed-by-default `AnalysisDock` region.

089 turns that existing dock into a bounded operator comparison surface over **real persisted data**. Its purpose is to answer a narrow question safely:

> For selected persisted run observations that have a trustworthy metric identity and declared unit, how do their recorded values compare?

The slice is intentionally smaller than a general analytics subsystem. It must make invalid comparison harder than valid comparison. In particular, it must visibly refuse incompatible or insufficiently specified observations rather than silently normalizing, guessing units, coercing values, or inventing telemetry.

The minimum useful result is a compact comparison table inside the existing analysis dock. Charts are optional presentation, not a requirement or authority.

## 2. Exact product authority

This definition derives from current merged frontend authority and runtime behavior:

- 081 requires Phase 3 to contain one real analytics widget and one visibly rejected unit incompatibility;
- 083 owns the single `AnalysisDock`, closed by default, transient, keyboard reachable, Escape-closeable, and non-persistent;
- 087 owns read-only dependency/provenance/freshness semantics;
- 088 exposes persisted run list/detail and treats persisted payloads as historical evidence, not live recomputation;
- 035 exposes searchable engineering records and cross-navigation without creating a second engineering-truth store.

Current 088 runtime exposes persisted run detail fields including `output_payload` as stored JSON text. Current frontend code deliberately renders those payloads as bounded inert evidence. Nothing in the current runtime authorizes arbitrary JSON leaves to be treated automatically as engineering metrics.

Therefore 089 must not infer more semantic authority than the persisted data actually contains.

## 3. Scope

089 may add only the minimum frontend behavior needed to:

1. expose analytics content through the existing shell `AnalysisDock`;
2. let the operator choose a bounded set of persisted runs within the current workspace;
3. discover only observations whose metric identity, numeric value, and unit are trustworthy under the frozen comparability rules;
4. show why observations are comparable, excluded, or incompatible;
5. render a deterministic comparison of compatible observations;
6. preserve direct navigation to the underlying run evidence;
7. handle stale responses, disappearing runs, malformed payloads, empty data, and partial read failures without retaining misleading prior analytics.

Expected implementation is frontend-only unless readiness proves that current persisted contracts cannot expose any trustworthy unit-bearing observation without backend interpretation. If that happens, readiness must stop and record the exact insufficiency; it must not invent an aggregation endpoint merely for convenience.

## 4. Non-goals

089 does **not** authorize:

- a generic BI/dashboard framework;
- analytics persistence, saved dashboards, saved chart layouts, or browser-storage state;
- run creation, rerun, cancellation, polling, live progress, or streaming telemetry;
- provider/model cost analytics, route scoring, latency scoring, AI evaluation, or automatic route promotion;
- proposal review or promotion/rejection behavior from 054;
- any 062 grading control or use of missing grades as evidence;
- Jarvis threads, AI summaries, generated insight text, anomaly detection, recommendations, forecasts, or synthetic explanations;
- statistical significance claims, confidence intervals, regressions, optimization, surrogate models, or design-of-experiments logic;
- unit guessing from field names, labels, magnitudes, model names, comments, display text, or neighboring values;
- silent unit conversion through ad-hoc constants;
- semantic identity derived from array position or arbitrary JSON traversal order;
- new global state libraries, charting libraries, table libraries, schema libraries, or unit libraries without a readiness-proven need;
- backend/schema/migration/provider/credential/budget/egress changes by default;
- global visual-identity changes.

## 5. Data authority and observation contract

### 5.1 Persisted evidence only

Every displayed observation must trace to persisted repository-backed data already returned by an authorized read contract. The UI must never manufacture a value because a run status, label, artifact, log line, missing payload, or visual reference suggests that value should exist.

A current page selection may choose *which* persisted subject to inspect, but it does not become engineering authority.

### 5.2 Trustworthy observation

Readiness must inventory the exact result shapes produced by the currently reachable bundled/run paths. It may authorize extraction only where the runtime contract provides all of:

```text
metric identity
finite numeric value
declared unit
source run identity
```

A metric identity must be stable within the persisted contract, such as a versioned output key/path whose meaning is defined by the producing model contract. Display labels alone are insufficient if they can map to multiple meanings.

The implementation must reject, rather than coerce, observations whose value is:

- `null`;
- boolean;
- string-form numeric text unless the producing contract explicitly defines that field as numeric text;
- NaN or infinite after contract-safe decoding;
- object or array where no scalar observation contract exists;
- missing a declared unit;
- missing a trustworthy metric identity;
- truncated or otherwise presentation-derived rather than parsed from the authoritative payload.

089 must parse the authoritative persisted payload independently of 088's presentation truncation helper; it must not scrape rendered JSON text from the DOM.

### 5.3 Units are part of identity

A numeric value without a trustworthy unit is not comparable in 089.

Units must be displayed beside every comparable value and in any summary header. The UI must not hide units in a tooltip, legend-only affordance, color encoding, or inaccessible chart axis.

## 6. Comparability contract

### 6.1 Default fail-closed rule

Two observations are comparable only when all of the following are true:

1. their metric identities are the same under the producing contract;
2. both values satisfy the scalar observation contract;
3. both units satisfy one readiness-frozen compatibility rule;
4. both belong to the current workspace and to runs the user deliberately included in the comparison.

If any condition is unknown, comparison is rejected.

### 6.2 Unit compatibility

Readiness must choose the **smallest already-authoritative rule** available on current master.

Preferred order:

1. if current persisted output contracts already emit one canonical unit per metric, compare only exact canonical-unit matches;
2. if an existing deterministic repository unit contract is already used at the relevant result boundary and can convert without adding a new authority layer, readiness may freeze that exact converter and target unit;
3. otherwise exact unit-string equality is the only authorized first implementation.

089 must never add its own conversion table or normalize textual aliases such as `bar`, `bara`, `Pa`, `kPa`, `C`, `°C`, `K`, `kg/h`, or `kg/s` by assumption.

A physically convertible pair is still **incompatible for this UI** when the repository lacks an authoritative conversion decision at the relevant boundary. The visible reason should say that compatible units are required, not that the physics is impossible.

### 6.3 Semantic compatibility beats dimensional compatibility

Equal dimensions do not make different metrics comparable. Pressure drop and vessel pressure, mass flow and inventory mass, inlet temperature and outlet temperature remain different metrics unless the producing contract explicitly gives them the same metric identity.

No grouping by unit alone is permitted.

### 6.4 Rejected groups remain visible

When the operator selects runs that contain the same metric identity with incompatible units or unusable values, the UI must show a bounded rejected-comparison state naming:

- metric identity or safe display label;
- participating run labels/IDs in bounded form;
- declared units where available;
- exclusion reason.

It must not silently omit the incompatibility and present a smaller group as if all selected runs were compared.

## 7. Analytics model

### 7.1 Run selection

The first implementation compares runs only inside the current App-owned workspace.

The operator must explicitly choose the compared run set. Selecting a run in `/runs` may seed or focus analytics only if readiness can preserve one clear state owner; it must not create a second persisted selection store or infer an analytics comparison from every visible run automatically.

Recommended minimum interaction:

- current workspace remains App-owned;
- analytics dock exposes a bounded run picker from existing `listRuns()` data;
- zero or one selected run shows an instructional state, not fake analytics;
- two or more selected runs enable comparison discovery;
- route/workspace changes clear comparison state unless an existing typed shell contract explicitly preserves it safely.

Readiness may narrow the exact wiring, but duplicate workspace ownership is forbidden.

### 7.2 Bounded scale

Readiness must freeze practical limits for:

- maximum selected runs;
- maximum extracted observations per run;
- maximum rendered comparison groups;
- maximum text/token lengths.

The limits exist to prevent a large or adversarial persisted payload from freezing the UI. Truncation must be explicit and must never change the underlying comparability decision silently.

### 7.3 Minimum valid summaries

For a compatible group with at least two selected observations, 089 may show only direct deterministic summaries derivable without statistical interpretation, for example:

- each recorded value;
- minimum and maximum;
- absolute range (`max - min`);
- delta from an explicitly identified baseline run.

A baseline must be visibly identified and deterministic. No percentage change is required because a zero or sign-changing baseline creates additional semantics and failure modes; readiness may authorize it only if a concrete product need and zero-handling rule are frozen.

Mean, median, standard deviation, percentile, trend slope and similar statistics are out of the minimum first implementation unless readiness proves that the observations constitute a meaningful homogeneous sample and freezes the semantics. Do not add them merely because they are easy to calculate.

### 7.4 Presentation

The required first widget is a compact semantic table/list with explicit units and run labels. It is sufficient for acceptance.

A native SVG plot may be added only if readiness proves that it materially improves the frozen comparison and can remain accessible without a new dependency. A charting dependency is not justified for 089 by default.

Color may reinforce but never carry the only distinction. Exact values and units must remain available as text.

## 8. Shell integration

089 consumes the existing shell AnalysisDock rather than creating a second drawer, modal, bottom sheet, dashboard page, or fixed overlay.

The dock remains:

- closed on fresh route load;
- closed after route changes unless the existing shell's explicit request seam opens it in response to a user action;
- transient React state only;
- unmounted when closed;
- keyboard reachable;
- Escape-closeable with focus returned to the initiating toggle.

089 may add an explicit, user-visible action from an appropriate Phase-3 surface to open analysis, provided it uses the existing `requestShellRegionOpen("dock")` seam or a minimum typed extension of that seam. It must not auto-open because multiple runs exist, a run finishes, a record is selected, or a payload contains a numeric value.

The dock content must identify the current workspace and current comparison set sufficiently to prevent context confusion.

## 9. Cross-surface continuity

089 must preserve:

- `/runs` as the authoritative run evidence workbench;
- `/engineering-data` as the searchable engineering-record surface;
- Lineage/freshness behavior from 087;
- all existing legacy diagnostic routes until their owning replacement spec removes them;
- App-owned workspace state;
- shell panel focus semantics;
- StageSelection distinctions.

Analytics is derived presentation, not a new source of record identity. Clicking or activating a run reference from the dock may navigate to `/runs` and focus that persisted run only through a typed navigation/selection seam proven at readiness. It must not scrape or simulate clicks in another page.

089 does not create or promote MemoryStore records from an analytics result.

## 10. Async and stale-state contract

All reads that can outlive their initiating workspace/run set must be guarded by both request generation and relevant identity.

At minimum, the implementation must correctly handle:

- workspace A → B with late A response;
- workspace A → B → A with late first-A response;
- selected run set X → Y with late X detail/result response;
- selected run set X → Y → X with late first-X response;
- a selected run disappearing after refresh;
- one run detail failing while others succeed;
- malformed result payload for one selected run;
- route change while analytics requests are pending.

A stale response must not repopulate values, incompatibility notices, summaries, selected-run labels, or errors for the new context.

When the authoritative comparison context changes, prior derived analytics must clear synchronously before new data is accepted. Showing old values under a new workspace or selection is beta-blocking.

## 11. Failure and empty states

The UI must distinguish at least:

- dock opened with no comparison runs selected;
- only one run selected;
- selected runs have no trustworthy comparable observations;
- comparison contains incompatible units;
- comparison contains same-unit but different metric identities;
- selected run disappeared;
- run list/detail request failed;
- malformed persisted payload;
- bounded extraction truncated available metrics;
- valid comparison ready.

A failure in one run must not be rendered as `0`, `—` inside an otherwise valid numeric series, or silently dropped. The group must state that the selected comparison is incomplete or rejected, according to the frozen rule.

Retry actions must repeat only the failed/current read and preserve current identity guards.

## 12. Accessibility and responsive behavior

089 inherits 070/083 requirements and adds:

- one visible heading for the analysis content;
- semantic controls with visible labels for run and metric selection;
- table/list structures understandable without color or hover;
- units in accessible text;
- rejected-comparison reason in accessible text;
- deterministic focus after an explicit `Open analysis` action;
- existing Escape-close and toggle focus restoration;
- no focus in closed dock content;
- no hover-only data point details;
- no inaccessible canvas-only chart.

At 200% zoom and compact desktop width:

- no document-level horizontal overflow;
- the dock may use its existing local bounded overflow where needed;
- long run IDs, metric keys, units and numeric strings must wrap or locally scroll without expanding the page;
- the primary work surface remains usable while the dock is open.

## 13. Security and privacy

089 makes no provider calls and sends no analytics data externally.

It must not expose:

- filesystem paths hidden by 088;
- secret values;
- provider credentials;
- raw database identifiers that existing read models intentionally hide;
- arbitrary HTML from payloads;
- executable links or markup derived from persisted values.

Persisted strings are inert text. No `dangerouslySetInnerHTML` or dynamic code execution is authorized.

## 14. Visual boundary

089 owns only local information hierarchy and structural styling necessary for the analysis dock:

- compact data rows/table;
- comparison/rejection grouping;
- unit labels;
- local overflow;
- selected/baseline state with non-color distinction.

It must reuse 070 semantic tokens and existing shared primitives where appropriate.

It must not change global token values, fonts, iconography, border/radius/shadow grammar, motion language, or application-wide component styling. The maintainer workstation reference guides density and hierarchy, while the separate visual-identity lane remains independently removable.

No fake confidence score, health score, optimization score, stress result, system telemetry, AI insight, or placeholder chart copied from a visual reference may appear.

## 15. Likely implementation boundary to verify at readiness

Readiness must derive the exact allow-list from current master. Expected existing/new paths are bounded around:

```text
frontend/src/App.tsx or one equivalent typed shell contribution seam
frontend/src/api/runs.ts only if a missing read helper is required
frontend/src/components/analytics/*
frontend/src/components/shell/AnalysisDock.tsx only if the existing content contract proves insufficient
frontend/src/pages/RunsWorkbench.tsx only for an explicit typed open/focus seam if necessary
frontend/src/styles/analytics.css
frontend/src/main.tsx only for the local stylesheet import
scripts/check_analytics_dock.py
docs/specs/STATUS.md during implementation lifecycle only
```

Readiness must remove any path that is not necessary. Backend paths, package manifests/lockfiles and global token files are excluded unless readiness first demonstrates a concrete blocker and amends this definition through a separate documentation-only authority change.

## 16. Readiness questions

Before promoting 089 to `ready`, the readiness decision must answer with exact current-master evidence:

1. Which existing run/result contracts contain unit-bearing scalar observations that are safe to compare?
2. What exact persisted JSON shapes and model-contract versions produce them?
3. What is the trustworthy metric identity for each allowed observation?
4. Are units already canonical per metric? If not, is there an existing deterministic converter authoritative at this boundary?
5. What exact rule rejects incompatible units?
6. What bounded limits prevent pathological payload/render size?
7. How will the dock obtain the App-owned workspace without duplicate ownership?
8. How will the operator explicitly choose runs and open analysis?
9. Which stale-response identity/generation rules are required?
10. Can 089 stay frontend-only? If not, what exact runtime insufficiency blocks it?
11. Which existing 035/087/088 preservation checkers must be reconciled for later-slice lifecycle without weakening semantic assertions?
12. What exact browser proof will demonstrate a real comparison and a visibly rejected incompatibility?

If question 1 has no affirmative answer on current master, readiness must leave 089 `planned` and record the blocker. It must not authorize fake fixture-only analytics as product behavior.

## 17. Deterministic and browser evidence

Readiness must freeze exact commands, but implementation evidence must include at least:

- `python scripts/check_spec_status.py --self-test`;
- inherited 070/083/087/088/035 preservation checks relevant on current master;
- one dedicated dependency-free 089 checker with negative self-tests for fake/unitless/incompatible data and lifecycle decoys;
- a focused deterministic state/extraction harness covering comparability and stale-response guards;
- locked `npm ci` and production `npm run build`;
- repository CI and BLUECAD Real Tool Proof on the exact implementation head;
- headless-browser or equivalent exact-head proof against isolated real backend/persisted fixture state.

The browser matrix must prove at least:

1. dock closed on initial load;
2. explicit open action and focus placement;
3. one comparison of at least two real persisted observations with visible metric identity and unit;
4. one selected incompatible-unit case visibly rejected with no converted value;
5. unitless/malformed values excluded without coercion;
6. workspace A → B → A stale response rejection;
7. selected-run X → Y → X stale response rejection;
8. selected run disappearing during refresh;
9. compact/effective-200%-width containment with no page-level horizontal overflow;
10. keyboard-only run/metric selection and Escape close/focus return;
11. Runs, Engineering Data and Lineage continuity;
12. no uncaught browser errors.

Fixture-backed browser data is acceptable as deterministic test evidence only when it uses the same production read contracts and extraction rules. It must never be described as live engineering output.

## 18. Acceptance criteria

089 is complete only when all of the following are true on one unchanged exact implementation head:

1. the existing AnalysisDock is the only analytics container and remains closed by default;
2. analytics use only persisted authoritative read data;
3. every comparable value has trustworthy metric identity, finite numeric value, declared unit and source run identity;
4. incompatible or unknown units are rejected visibly rather than converted/normalized silently;
5. semantically different metrics are never grouped merely because units match;
6. unitless, malformed, nonnumeric and presentation-truncated values cannot enter a numeric comparison;
7. comparison state is bounded, transient and workspace-scoped;
8. stale responses cannot repopulate analytics after workspace/run-set changes;
9. missing/disappearing/failed runs cannot become zeroes or silently vanish from an apparently complete comparison;
10. the required real-data comparison and incompatibility-rejection browser cases pass;
11. keyboard, focus, Escape, 200% zoom, compact width and no-global-overflow behavior pass;
12. 035, 087 and 088 product behavior remains intact;
13. no backend/schema/dependency/provider/credential/AI/grade/global-identity scope has been added without a merged definition amendment;
14. no P0/P1/beta-blocking P2 finding remains;
15. rollback can remove the 089 extraction/presentation contribution and restore the prior migration-pending AnalysisDock without data migration or authority loss.

## 19. Rollback

089 must be independently removable.

Rollback removes the analytics extraction/state/presentation and any typed shell contribution seam introduced solely for 089, then restores the existing honest migration-pending analysis dock content.

Rollback must not:

- delete or rewrite persisted runs;
- change engineering records;
- change lineage/freshness state;
- require a migration;
- alter backend contracts;
- alter global visual identity.

## 20. Registry disposition

This definition PR adds only this specification file. Registry row 089 remains:

```text
planned | Implementation PR —
```

A separate readiness PR must promote 089 to `ready` only after section 16 is resolved from exact current master.

No runtime implementation is authorized by merging this definition.