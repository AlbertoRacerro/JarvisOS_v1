# 100b — CODEBASE-LEAN-CLEANUP-1

Definition status: **freshly re-derived from merged 100a evidence; CLEANUP candidate frozen, runtime implementation maintainer-gated**  
Exact derivation base: `6acf76316dc3301b7e8fe38f95b47e5860eb55c4`  
Merged audit authority: `docs/audits/100a-codebase-lean-audit-faddf39.md`  
Depends on runtime authority: 100a (`merged` through PR #405)

## 1. Purpose and outcome

100b has exactly one evidence-backed top-level outcome on this base: **`CLEANUP`**.

The merged 100a audit found no justified broad deletion pass and zero `DELETE` dispositions. It found one high-confidence `MERGE` candidate outside the semantic ownership of 101 and 103–105: fold the 100f-specific read adapter `frontend/src/api/finalOperatorReads.ts` into the existing shared client boundary `frontend/src/api/client.ts`, preserving every truthful read contract used by `frontend/src/components/fusion/FinalOperatorReadSurface.tsx`.

This specification freezes that one candidate only. It does **not** authorize runtime implementation under the 2026-08-28 overnight release; maintainer review is required before any source mutation.

## 2. Frozen candidate set

### C1 — merge final operator reads into the shared frontend API client

**Disposition:** `MERGE`  
**Confidence:** high  
**Audit evidence:** 100a ranked ROI/risk item 1 and bounded candidate C1.

Proposed runtime touched boundary, if later explicitly authorized:

- `frontend/src/api/client.ts` — retain as the single shared read/API owner and add any richer types/read functions that exist only in the focused adapter;
- `frontend/src/api/finalOperatorReads.ts` — remove only after all accepted exports are migrated and consumers no longer import it;
- `frontend/src/components/fusion/FinalOperatorReadSurface.tsx` — switch imports only; do not alter operator behavior, IA, rendering semantics or authority;
- test-only frontend files only when required to preserve or strengthen existing contract assertions.

No other runtime path is in the 100b candidate set.

## 3. Preservation obligations

A later C1 implementation must preserve all of the following exactly:

1. the same backend endpoints and server-owned READ authority;
2. Project Basis, Models and Runtime truthful read/Unknown/unavailable behavior established by 100f;
3. requirement reads used by the final operator surfaces;
4. Parameter fidelity required by 098, including `value`, `unit`, `value_status` and `lifecycle_state` where exposed by the current server response;
5. workspace/model/decision identity and payload fidelity;
6. existing error behavior: consolidation must not turn failed/unknown reads into invented success/default data;
7. no provider, GitHub, filesystem, shell, process or state-store access from the frontend;
8. no canonical mutation, run creation, proposal promotion or feature wiring;
9. the final operator IA and all eleven 100f surfaces unchanged.

`Unused != unwanted` remains binding. Nothing classified by 100a as `WIRE`, `DEFER`, `KEEP`, `PROFILE` or `UNKNOWN` may enter this cleanup.

## 4. Explicit exclusions and later owners

100b must not pre-implement or partially absorb:

- modeling CRUD / MemoryStore / lifecycle unification — **101**;
- process upstream selection or custom-kernel strangling — **103/104**;
- `app/modules/engineering` retirement or the provenance-`flowsheet` naming/domain collision — **105**;
- agent/file support retirement, feature wiring, backend API retirement, compatibility-route redesign or any unproven dead-code deletion;
- any backend schema/API/domain/provider/Hermes/PTY/self-update authority;
- visual or interaction changes to 100f.

The 100a incumbent scientific/process tests and evidence remain protected for later zero-sunk-cost decisions.

## 5. Failure modes the cleanup must prevent

A future implementation is invalid if it:

- drops richer Parameter lifecycle fields while reusing a narrower existing type;
- changes endpoint paths, query parameters or response interpretation;
- turns optional/unknown server data into frontend defaults that look authoritative;
- creates a second HTTP/client abstraction while claiming to remove one;
- removes tests or compatibility behavior merely to make consolidation pass;
- broadens into adjacent modules because they appear unused;
- changes 100f composition, labels, routes or action classes;
- grows active semantic surface without a demonstrated simplification that outweighs the growth.

If exact implementation-base evidence shows C1 has already been collapsed, has acquired an independent semantic owner, or cannot preserve the obligations above with a bounded import/client change, readiness must be re-derived to `NO_ACTION` rather than substitute another cleanup target.

## 6. Required implementation proof if maintainer later authorizes C1

The future runtime PR must record exact base/head SHA and before/after source evidence for the touched frontend boundary. At minimum it must prove:

- `cd frontend && npm run build` passes, including retained 058d/100/100f gates;
- focused final-fusion/read assertions cover Project Basis, Models and Runtime behavior affected by the moved imports/types;
- no backend files, schemas or APIs changed;
- no stale import of `finalOperatorReads.ts` remains before that file is removed;
- before/after active frontend source/file count is recorded, with net semantic-surface reduction;
- all preserved `WIRE`/`DEFER` findings remain untouched.

No runtime-performance claim is authorized from LOC reduction. 100a measured structure, not latency/render/startup performance.

## 7. Acceptance criteria

100b is implementation-ready only if all are true:

1. the top-level outcome remains exactly `CLEANUP` and candidate set remains exactly C1;
2. 100a is `merged` and the exact merged artifact is cited;
3. touched runtime boundaries are limited to the C1 paths above plus necessary focused tests;
4. all section 3 preservation obligations are explicit and testable;
5. no `DELETE` claim is inferred from missing callers;
6. no 101, 103, 104 or 105 semantic work is pre-implemented;
7. no new dependency, framework, state store, compatibility subsystem or infrastructure is introduced;
8. expected reduction is one duplicate frontend API module/helper/type family, with accepted behavior retained in `client.ts`;
9. exact-head deterministic gates for the docs-only definition/readiness PR are green and no material finding remains;
10. runtime implementation remains blocked until explicit maintainer authorization after review of this frozen set.

## 8. Minimum-necessary test

The only justified generic pre-101 cleanup is the narrow duplicate frontend read boundary identified by 100a. A broad refactor, automatic dead-code pass, backend cleanup or feature wiring would increase semantic risk and collide with later accepted owners. Therefore C1 is the minimum candidate set and the correct stop point.

## 9. Definition of done for the current authorized docs-only phase

- this fresh full spec is merged from exact post-100a master;
- `docs/specs/100b-readiness-2026-08-28.md` records a `READY / CLEANUP` disposition for C1 only;
- `STATUS.md` is reconciled to `100b=ready` with no implementation PR;
- a remote checkpoint records exact master, audit artifact, candidate, risk and proposed boundaries;
- `NEXT_EXACT_ACTION=MAINTAINER REVIEW OF 100b CLEANUP SET`;
- **no runtime source is mutated and 100c/101–110 do not start.**
