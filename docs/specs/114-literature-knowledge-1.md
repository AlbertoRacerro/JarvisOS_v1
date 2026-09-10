# 114 LITERATURE-KNOWLEDGE-1

Status: **planning candidate; `docs/specs/STATUS.md` remains authoritative and is still `planned` until an accepted readiness transition**.

Exact re-derivation base: `d3a3e3c6cd316d8bba4fe28131c51649e9a8f7a3`.

## Outcome

Make `Memory > Literature` a truthful operator surface backed by one bounded literature read/provenance owner rather than reference fixtures or synthetic content.

The operator can inspect imported/public literature as a compact list, keep multiple records expanded inline, inspect extracted claims/data with exact source location and provenance, preview supported source material, and open the real source. Reading or opening literature never silently adds Jarvis context and never promotes a literature statement into canonical project/model truth.

This contract re-derives the 100c `FV-B06` / `FV-F05` obligations from fresh runtime. It does not implement semantic retrieval, autonomous research, generic RAG, or a second engineering-memory authority.

## Fresh ownership evidence

At the re-derivation base:

- `frontend/src/App.tsx` deliberately renders `memory-literature` through `FinalOperatorUnavailableSurface` and states that no bounded literature corpus/read owner exists yet. This is the actual product gap.
- `backend/app/modules/files` already owns registered file/artifact metadata and carries `source_ref`; it remains the owner of stored file bytes/path-safe file access rather than being copied into a literature blob store.
- Memory/modeling records already carry `source_ref` provenance fields. Those existing fields remain downstream provenance links; 114 must not create parallel Parameter/Requirement/model truth.
- The 100c queue requires structured Source -> Document/import -> Claim/Datum -> Citation/location/context -> Used-by provenance, bridged to existing file/source authority.
- The approved operator capability matrix requires compact source/file rows, inline multi-expand, extracted knowledge with exact provenance, bounded preview, real full-source open, and proposal-only web-finding promotion.

## Canonical ownership boundary

114 may introduce **one literature-domain owner** for literature-specific identity and provenance that existing generic owners do not represent. It may persist only the minimum structured metadata needed to identify and relate:

- a literature source;
- an imported/registered document reference owned by the existing file boundary;
- a claim or extracted datum;
- an exact citation/location/context inside that source;
- explicit links showing where that literature item is used by existing project/model records.

Implementation may choose the minimum normalized representation after inspecting current SQLite/schema owners, but it must satisfy all of the following:

1. file bytes and safe file serving remain with the existing file owner;
2. Project Basis, Parameters, Requirements, modeling versions/runs and other engineering records remain with their existing canonical owners;
3. literature records never become an alternate canonical engineering-value store;
4. `source_ref` interoperability is explicit and stable rather than heuristic text matching;
5. used-by links either derive from exact existing provenance refs or are stored as typed references whose targets are validated; no copied downstream record bodies;
6. workspace ownership is enforced on every read/write/link boundary;
7. deletion/supersession cannot leave a literature item appearing authoritative after its backing source/document is unavailable.

A new generic vector database, document vault, crawler, second files table, second proposal store, or second search index fails the minimum-necessary test for this slice.

## Required read model

The server-owned Literature read surface must expose enough typed information for the approved UI without forcing backend taxonomy into presentation strings:

- stable literature/source identity and workspace identity;
- human title plus source/document kind and availability state;
- bibliographic/source metadata when actually known, with unknown fields represented as unknown rather than fabricated;
- exact backing file/source reference when one exists;
- claims/data with statement/value/unit/status as applicable;
- citation location adequate to return to the exact source region when the backing format supports it (for example page for PDF, line/range for text/Markdown, or an explicitly unsupported locator state);
- used-by typed refs to existing canonical records;
- provenance timestamps/source identity needed to distinguish imported facts from canonical project truth;
- bounded pagination/limits for list and expanded content.

Malformed/stale/dangling references fail visibly. A missing file, unsupported preview, invalid locator, or unknown metadata must never be converted into a plausible-looking substitute.

## Mutation and proposal semantics

114 owns only literature-domain curation needed to make the corpus/provenance truthful, such as registering/importing a source through existing file authority and recording/editing/rejecting literature-specific extracted metadata under normal operator authority.

Research, web discovery, OCR/extraction, summarization, inferred claims, or AI-generated data are **proposal inputs**. They do not commit canonical engineering records and do not bypass the existing AI execution, sensitivity, provider, budget, ledger, MemoryStore/proposal, or Project Knowledge promotion boundaries.

A literature claim becoming a Project Basis/Parameter/model fact requires the existing owning domain's explicit proposal/commit/reconciliation path. 114 must preserve the distinction between `literature evidence exists` and `project truth accepted`.

No live external provider, crawler, browser automation, arbitrary URL fetcher, or paid research call is required for deterministic acceptance of 114.

## Operator surface

`Memory > Literature` replaces the current truthful-unavailable placeholder only when the backing read owner exists.

Required behavior:

- compact vertical source/file list at rest;
- multiple literature rows may remain expanded simultaneously;
- expanded content shows extracted knowledge and provenance without raw machine payload becoming the primary presentation;
- opening/expanding a row does not add it to Jarvis context;
- supported source preview is bounded and uses the real existing file/source read boundary;
- unsupported or unavailable preview is explicit;
- `Open full source` targets only a validated real source/file location and preserves Memory navigation state;
- empty, loading, malformed, stale and unavailable states remain distinguishable;
- reference HTML fixture values are never production data.

Jarvis `CONTEXT` / `PROPOSE` actions over literature remain owned by 121. 114 may expose the exact typed refs needed by 121 but must not pre-implement or fake those actions.

## Failure modes that must be closed

Implementation and tests must cover at least:

- cross-workspace source/document/claim/used-by reference attempts;
- dangling or wrong-kind `source_ref` / target refs;
- missing backing file after metadata exists;
- unsupported MIME/preview type;
- invalid/out-of-range page or text locator;
- malformed extracted datum (including value/unit mismatch or non-finite numeric values where numeric data is represented);
- unbounded list/claim expansion;
- duplicate import/retry behavior creating accidental duplicate authority;
- a web/AI finding being rendered as accepted project truth without promotion;
- stale/superseded literature remaining presented as current;
- unsafe original-source URL/path exposure;
- secret-bearing material being copied into logs, fixtures, frontend errors or model context merely because it was imported as a source.

## Acceptance criteria

114 is implementation-complete only when all of these are true:

1. A workspace with real imported literature can list sources/documents from server-owned state with bounded reads.
2. At least one source can expose a claim or datum carrying exact source provenance/location and a real used-by relationship without duplicating the downstream canonical record.
3. Supported preview/open uses the real file/source boundary; missing/unsupported content fails truthfully.
4. The approved compact-list + inline-multi-expand Literature composition is activated with real data, including empty/error/unavailable states and no fixture substitution.
5. Merely browsing/opening literature does not mutate Jarvis context, Project Basis, Parameters, Requirements, models, runs or proposals.
6. AI/web/extraction output remains proposal-only until the existing owning promotion path accepts it.
7. Workspace isolation, typed-reference validation, stale/dangling handling, bounded pagination and safe source opening are deterministic and covered by focused tests.
8. Existing hard invariants remain intact: no secrets in frontend responses/logs/artifacts/model context; no new provider/egress authority; no direct frontend filesystem/provider access.
9. Frontend build and relevant backend deterministic tests pass on the frozen implementation head.
10. Exact-head trusted real-browser proof exercises the Literature list, at least two simultaneous expansions, a real supported preview/open affordance or truthful unsupported case, and proves opening a record does not silently add Jarvis context.

## Non-goals

- semantic/vector retrieval or 064 LIT-RAG;
- 115 project-wide search;
- 121 Jarvis Literature context/proposal actions;
- autonomous literature research/crawling;
- arbitrary remote URL fetching;
- OCR or LLM extraction as a required baseline capability;
- replacing existing file/artifact/source serving;
- replacing MemoryStore, Project Knowledge, Parameter/Requirement/model owners;
- generic bibliography/reference-manager product scope;
- hidden promotion from literature evidence to canonical engineering truth;
- visual redesign beyond activating the already-approved Literature composition.

## Evidence/readiness requirements

Before `STATUS.md` may move 114 from `planned` to `ready`, the planning diff must be accepted against fresh master and the implementation owner must confirm the minimum concrete persistence/API shape from current code. That readiness transition must preserve dependencies `040, 042, 112`, cite the merged 100c authority, and identify the exact canonical Literature HTML/reference blob used for browser conformance.

Implementation then follows the ordinary Generic Frontier Builder Contract. No implementation branch is authorized by this document while the registry row remains `planned`.
