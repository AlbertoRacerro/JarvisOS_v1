# 035 — ENGINEERING-DATA-1

## Status
Definition only. Runtime implementation is not authorized until a separate readiness decision merges and the canonical registry is reconciled after 088.

## Goal
Replace the shell's Engineering Data migration placeholder with one searchable, read-first engineering-record navigator that reuses existing canonical workspace records and the merged 087 lineage/freshness model, while preserving legacy Domain Foundation creation/scenario controls until later slices explicitly migrate them.

This slice is the navigation and inspection layer between merged lineage/run surfaces and later analytics/proposal review. It must make existing engineering truth easier to find without creating a second store, recomputing records, silently promoting proposals, or absorbing 089/054/062 scope.

## System context
The legacy `DomainFoundation` page currently owns a mixed diagnostic surface for workspace selection, model specs, model implementations, assumptions, parameters, simulation runs, decisions, scenario binding preview/execution and record creation. The new shell already has App-owned transient workspace state, a read-only lineage workbench (087), and the RUNS workbench (088). ENGINEERING-DATA-1 must consume those established seams rather than recreating workspace or run authority.

Hard dependencies are 040, 050, 051, 083, 087 and 088. No new backend contract is presumed by this definition: readiness must inventory the existing typed clients/routes for workspace-scoped model specs, assumptions, parameters, decisions and any other record kinds actually required before authorizing implementation.

## Operator outcome
For the current workspace, an operator can:

1. open Engineering Data from the primary shell;
2. search/filter across the supported canonical engineering-record kinds using deterministic frontend projection only;
3. distinguish record kind, identity, accepted/proposed state where real authority exists, freshness/staleness where real 051 authority exists, and concise provenance/source references where already exposed;
4. select one record and inspect bounded real fields without raw filesystem paths, fake semantic labels, fabricated confidence or inferred engineering meaning;
5. follow bounded navigation into existing lineage/run surfaces when a real canonical reference supports it;
6. recover predictably when workspace, filters or underlying record lists change, including A→B→A request races;
7. continue using the legacy Domain Foundation route for creation, scenario execution and other not-yet-migrated mutations.

## Authority and data rules
- SQLite/backend records remain canonical. Frontend search indices, grouping and selection are derived presentation state only.
- App remains the single transient workspace owner. No Engineering-Data-local workspace store, context or URL persistence is introduced.
- Stale/fresh state is shown only from existing 051 authority or an existing endpoint that already exposes it. Absence of freshness evidence must render as unavailable/unknown, never fresh by assumption.
- Proposal/accepted/rejected semantics are shown only when an existing record contract exposes them. 035 does not add promote/reject actions; those belong to 054 where applicable.
- Runs remain owned by 088. 035 may link to a run by canonical reference but must not duplicate the run detail/log/artifact workbench.
- Lineage remains owned by 087. 035 may expose concise provenance and navigation but must not introduce a second graph model or recomputation path.
- No grade placement/state from blocked 062 may appear.

## Minimum record boundary
Readiness must derive the exact supported kinds from current master. Expected minimum candidates are canonical assumptions, parameters, decisions and model specifications because the legacy page already reads them. Additional kinds may be included only when an existing stable workspace-scoped read contract and a concrete navigation need are demonstrated. Do not generalize into an arbitrary entity browser.

## Search and ordering
- Search is bounded, deterministic and local to already-fetched records unless readiness proves an existing backend search route is necessary for scale.
- Normalize only presentation-safe textual fields explicitly defined per record kind; do not stringify entire objects into a hidden search corpus.
- Default ordering is deterministic and stable across refreshes. Readiness must freeze the exact primary/secondary sort keys per kind from real fields.
- Filters must preserve unknown enum/status values as visible evidence rather than dropping them.
- Empty query and empty filters show the complete supported current-workspace set, subject to bounded presentation limits frozen at readiness.

## Selection and race handling
- Requests carry generation plus workspace identity. A→B→A late responses are rejected even when the final workspace id equals the original.
- Record detail requests, if any are separate from list reads, also carry record identity plus generation; X→Y→X late responses are rejected.
- On refresh, preserve selection only if the exact selected canonical record remains present and allowed by current filters; otherwise choose the deterministic next visible record or clear selection.
- Switching workspace synchronously clears prior-workspace derived detail before new data can paint.
- A failed refresh does not relabel stale visible data as current. If previously visible data is retained for continuity, it must be explicitly marked as retained/stale presentation and readiness must prove that behavior; otherwise clear it.

## Shell composition
The primary Engineering Data stage uses the existing 083 regions:

- main stage: dominant searchable record list/table or dense record browser;
- navigator contribution: optional compact kind/filter controls only if this improves density without duplicating primary content;
- sidecar contribution: bounded selected-record inspector and real navigation affordances;
- dock: closed by default and used only if readiness demonstrates a concrete evidence/history need. Do not pre-empt 089 analytics.

The layout follows the maintainer workstation direction: dense technical hierarchy, compact chrome, natural leaf/chlorophyll accent only through existing semantic tokens, no global visual-identity rewrite.

## Legacy continuity
The existing `/legacy/domain-foundation` route remains reachable and behavior-preserving. ENGINEERING-DATA-1 does not migrate workspace creation, model registration, scenario binding preview, scenario execution, record creation or other mutation forms unless a later specification explicitly authorizes them.

The new Engineering Data stage must not import or mount the legacy page as its implementation shortcut.

## Accessibility and responsive behavior
- Complete keyboard route to workspace controls inherited from shell, search/filter controls, record selection, selected-record inspector and navigation links.
- Visible focus under system/light/dark themes.
- Selection and freshness/proposal states must not rely on color alone.
- At effective 200% zoom / compact desktop width, no page-level horizontal overflow. Dense record rows may use explicitly bounded local overflow only where the readiness acceptance matrix permits it.
- Long ids, symbols, units, source refs and prose must wrap/truncate in a way that preserves access to the full value when required for operator evidence.
- Reduced-motion contract from 070 remains intact.

## Failure modes to prove
Readiness and implementation must cover at least:

1. workspace discovery empty/failure;
2. one record-kind list failing while others succeed;
3. malformed/null optional fields from historical records;
4. unknown enum/status values;
5. A→B→A workspace response race;
6. X→Y→X detail response race if separate detail reads exist;
7. selected record disappearing after refresh;
8. selected record hidden by filter/search change;
9. freshness/provenance unavailable without fake fallback;
10. long-token and effective-200%-width containment;
11. keyboard selection/focus recovery;
12. preservation of 087, 088 and legacy Domain Foundation behavior.

## Explicit non-goals
- no backend/schema/migration/cache/search-index infrastructure unless readiness proves the existing reads are technically insufficient;
- no new state framework, generalized entity registry or plugin architecture;
- no record creation/edit/delete/promote/reject;
- no run creation/rerun/cancel or duplicated RUNS detail;
- no lineage recomputation or second graph store;
- no analytics/charts/comparison normalization (089);
- no proposal review authority (054);
- no grade UI or 062 semantics;
- no Jarvis/AI thread behavior (090/091);
- no global visual identity lane C changes;
- no speculative refactor of the legacy Domain Foundation page.

## Expected implementation boundary
Readiness must freeze the exact allow-list from current master. The likely minimum is:

- one typed engineering-data read/projection client or reuse of existing typed clients;
- one small deterministic state/search helper plus harness;
- one Engineering Data page/stage component;
- local Engineering Data styles using existing tokens;
- `App.tsx` only for replacing the migration placeholder with the stage;
- `stages/registry.ts` only if bounded contributions are required;
- one dependency-free `scripts/check_engineering_data.py` plus the minimum merged-preservation updates required by older frontend checkers;
- `docs/specs/STATUS.md` lifecycle changes only when protocol requires them.

No package/lockfile change is expected.

## Deterministic gates
Readiness must preserve the inherited spec/status, UI-foundation, APP-SHELL, lineage and RUNS gates and add a dedicated 035 checker/self-test. If a small pure state helper is introduced, compile/execute a locked TypeScript harness after `npm ci`. Production `npm run build` is mandatory. Browser proof must use an isolated deterministic fixture over real existing read contracts and verify the failure/race/accessibility/200%-width matrix above.

All evidence is exact-head. Any implementation-head mutation invalidates earlier build/browser/review evidence.

## Downstream contracts
ENGINEERING-DATA-1 must leave a narrow, stable selection/navigation seam usable by:

- 089 ANALYTICS-DOCK-1 for real comparable values without making 035 own analytics;
- 054 PROPOSAL-REVIEW-1 for locating proposed records without granting 035 promotion authority;
- later 091 sidecar context without making 035 an AI context store.

Prefer canonical ids plus typed record kind over passing large copied objects between stages. Do not add a global selection framework unless readiness proves the existing shell seams cannot satisfy these three concrete consumers.

## Rollback
The slice must remain independently removable: restore the Engineering Data migration placeholder, remove 035-only page/helper/client/styles/checker and preservation clauses, with no backend/schema/data migration rollback and no impact on legacy Domain Foundation, 087 or 088.

## Readiness decision required
Before runtime work, a separate readiness record must re-read exact master after 088 reconciliation and freeze:

1. exact supported record kinds and existing endpoints/types;
2. list/detail data shapes and nullability;
3. exact sort/search/filter projection;
4. freshness/proposal/provenance fields that are genuinely authoritative;
5. shell region composition and selected-record navigation seams;
6. exact file allow-list;
7. deterministic checker/harness commands;
8. isolated browser fixture and acceptance matrix;
9. rollback;
10. confirmation that no backend/dependency/global-identity expansion is necessary.
