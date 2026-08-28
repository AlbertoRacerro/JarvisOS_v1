# 100a — CODEBASE-LEAN-AUDIT-1 evidence

**Audited runtime/source SHA:** `faddf39aaae7513943fd337f352de905626120ca`  
**Readiness authority:** `docs/specs/100a-readiness-2026-08-28.md`  
**Audit scope:** complete tracked first-party runtime/test/tooling surface defined by 100a  
**Audit mode:** evidence only; no runtime cleanup, rewiring, schema/API change, provider call, feature wiring or new infrastructure

## Executive disposition

The repository is large, but the audit does **not** support a broad dead-code deletion pass. The most visually obvious historical or currently unwired areas are either active authority boundaries, accepted evidence/test surfaces, or work explicitly owned by later slices. In particular, canonical-write overlap belongs to 101, process-stack selection/strangling belongs to 103/104, and the obsolete `engineering` boundary plus the dependency/provenance `flowsheet` naming collision belong to 105. Treating those areas as 100b cleanup would pre-empt their accepted owners.

One small generic cleanup candidate is supported with high confidence outside those later semantic owners: the 100f-specific `frontend/src/api/finalOperatorReads.ts` duplicates the shared HTTP read helper and several workspace/model/parameter/decision read types/functions already present in `frontend/src/api/client.ts`, while its only evidenced consumer is `frontend/src/components/fusion/FinalOperatorReadSurface.tsx`. This is classified **MERGE**, not DELETE: 100b may fold the richer fields/requirement read into the existing client boundary and remove the duplicate adapter only if exact-base tests prove no behavior change.

Therefore the bounded 100b candidate set is **CLEANUP, one candidate only**. No other runtime mutation is authorized by this artifact.

## Reproducible quantitative baseline

The exact audited ref was measured in CI from Git objects rather than from a mutable checkout. The temporary standard-library collector enumerated `git ls-tree -r --name-only <audited-sha>`, read each tracked file with `git show <audited-sha>:<path>`, counted physical/nonblank lines and bytes, extracted literal FastAPI route decorators and frontend exported API symbols, and derived import fan-in/fan-out without executing application code. The resulting workflow artifact was `100a-codebase-lean-metrics`, digest `sha256:7da883c9942b0669d04d7d60f2ba00fa5989e6529e3f0dcdcfe2849541e300d9`.

| Area | Files | Physical lines | Nonblank lines | Bytes |
| --- | ---: | ---: | ---: | ---: |
| backend/app | 264 | 70,187 | 63,429 | 2,667,131 |
| backend/tests | 230 | 58,700 | 49,993 | 2,123,658 |
| frontend/src | 90 | 16,278 | 14,632 | 667,917 |
| frontend/tests | 5 | 499 | 460 | 34,069 |
| scripts | 54 | 20,552 | 18,274 | 819,590 |
| workflows | 7 | 1,059 | 969 | 40,735 |
| launchers/config | 11 | 255 | 231 | 6,427 |
| **Total** | **661** | **167,530** | **147,988** | **6,359,527** |

Additional structural counts on the same exact ref:

- literal backend route decorators: **87**;
- exported frontend API symbols under API/client files: **76**;
- workflow files: **7**;
- first-party scripts: **54**;
- exact whole-file duplicate groups inside the measured scope: **0**.

These are structural metrics, not runtime-performance measurements.

## Structural hotspots

Top Python fan-in modules on the exact audited ref were `app.core.database` (169 importers), `app.modules.events.service` (88), `app.core.config` (68), `app.modules.ai.contracts` (66), `app.core.bootstrap` (61), `app.modules.ai.context_builder` (53), `app.main` (51), `app.modules.ai.settings` (50), and `app.modules.ai.token_flow_service` (41). High fan-in is evidence of change radius, not evidence that a module is slow or should be collapsed.

Top Python fan-out included `app.modules.ai.execution` (27 first-party dependencies), `app.modules.ai.egress_runtime` (22), `app.modules.ai.egress_confirmation_core` (21), `app.modules.bluecad.loop` (18), and `app.main` (16). Those boundaries carry execution, egress, confirmation, orchestration or application-composition responsibilities; 100a classifies them as **KEEP / PROFILE**, not cleanup targets.

Frontend relative-import fan-out was led by `frontend/src/App.tsx` (21), `frontend/src/main.tsx` (17), `frontend/src/components/Layout.tsx` (12), and `frontend/src/stages/registry.ts` (8). The counts reflect the final shell/fusion composition and do not establish a rendering hotspot.

## Complete area disposition inventory

The table below covers the complete first-party areas measured above at coherent ownership/component boundaries. Individual files inherit their component disposition unless separately called out in the candidate or exception registers.

| Component / boundary | Primary disposition | Confidence | Evidence / reason | Owner / next authority |
| --- | --- | --- | --- | --- |
| `backend/app/api` + FastAPI composition in `app.main` | KEEP | high | Active health/system/dev routes and explicit router composition. | current runtime |
| `backend/app/core` database/schema/config/paths/static/error infrastructure | KEEP | high | Highest fan-in foundation; carries schema, storage, config and SPA boundary invariants. | current runtime / 101 only where write semantics change |
| `backend/app/modules/ai` execution, policy, egress, token-flow, context and settings | KEEP / PROFILE | high | Active AI spine; high fan-in/out reflects security/cost/authority boundaries. No runtime timing data proves a hotspot. | current runtime; future changes require dedicated authority |
| `backend/app/modules/local_ai` and `local_ai_eval` | KEEP / DEFER | high | Local runtime lifecycle is imported by `app.main`; evaluation/support paths remain intentional local-first capability. | current runtime / future local-AI authority |
| `backend/app/modules/bluecad` | KEEP | high | Active CAD/mesh/FEM/evidence/candidate path with accepted verification evidence. | current runtime |
| `backend/app/modules/runner` | KEEP | high | Active deterministic execution boundary and evidence-producing run path. | current runtime |
| `backend/app/modules/workspaces`, `events`, `secrets` | KEEP | high | Mounted/consumed state, audit and credential boundaries. | current runtime |
| `backend/app/modules/modeling` + `memory` | DEFER | high | Both remain active, but overlapping canonical-write semantics are explicitly reserved for 101; 100a cannot collapse them safely. | **101** |
| `backend/app/modules/process_kernel` and bundled BlueRev process models/adapters | DEFER / REPLACE-UPSTREAM candidate evidence only | high | Incumbent scientific/process evidence must survive the zero-sunk-cost upstream bake-off; generic solver selection/strangling is explicitly later work. | **103/104** |
| `backend/app/modules/flowsheet` | DEFER | high | Active dependency/provenance graph is mounted by `app.main`; name/domain collision with future process flowsheets is known but structurally owned later. | **105** |
| `backend/app/modules/engineering` | DEFER | high | Small engineering boundary exists but is not mounted by `app.main`; 100b definition explicitly reserves this obsolete boundary to 105 unless independently proven disposable without affecting that work. | **105** |
| `backend/app/modules/agents` | DEFER / WIRE | medium-high | Thin `Agent` protocol and registry exist without current app composition; lack of caller is not deletion authority and future persona/agent policy remains planned/frozen elsewhere. | future agent/persona authority; do not delete in 100b |
| `backend/app/modules/files` | UNKNOWN / DEFER | medium | Small file registry/service boundary is not sufficient evidence by itself for deletion; artifact/file semantics may be consumed indirectly. No complete deletion gate was established. | preserve until concrete caller/product-intent trace |
| other backend support modules under `backend/app/modules` | KEEP unless routed above | high | No independent high-confidence deletion/merge evidence emerged from route/import/component audit; absence from `app.main` alone is insufficient. | current/future owning spec |
| `backend/tests` | KEEP | high | 58.7k lines are accepted behavior/security/scientific evidence; a test failure is not proof of obsolete behavior. | follows owning runtime boundaries |
| `frontend/src` shell/router/layout/100f fusion/BLUECAD/Properties/Jarvis/analytics/settings | KEEP | high | Production final operator composition; 100f is merged and must not be reinterpreted during lean audit. | current runtime |
| `frontend/src/api/client.ts` and focused API modules | KEEP | high | Server-owned API access remains required. Focused modules may carry richer contracts than the broad client. | current runtime |
| `frontend/src/api/finalOperatorReads.ts` | **MERGE** | **high** | Duplicates `getJson`, workspace/model/parameter/decision read types/functions already present in `client.ts`; single evidenced fusion consumer. Preserve richer lifecycle/requirement fields while folding into shared client. | **bounded 100b candidate** |
| legacy diagnostic/compatibility frontend surfaces | KEEP / DEFER | high | `App.tsx` still explicitly routes compatibility/diagnostic views; current route compatibility is accepted behavior, not dead code. | later explicit compatibility retirement only |
| `frontend/tests` + 058d/100/100f deterministic JS harnesses | KEEP | high | Conformance/identity/interaction evidence; do not delete merely because implementation slice merged. | current CI/conformance |
| `scripts/check_*`, review/security tooling, evidence generators | KEEP / DEFER | high | CI/protocol/manual-review/security/evidence owners remain explicit. 54 scripts are not automatically 54 cleanup targets. | current CI/manual tooling; retire only with owner removal |
| `.github/workflows` | KEEP | high | CI, geometry proof, explicit manual review and merged continuation authorities remain registered. | current repo governance |
| launchers and Python/Node config | KEEP | high | Active local launch/build/test configuration. | current runtime/toolchain |

## Desired-but-unwired / protected register

These items are specifically protected from the false inference `unused => unwanted`:

1. **Agent protocol/registry** — the small `backend/app/modules/agents` boundary has no app composition evidence in the audited `main.py`, but planned/frozen agent/persona work exists. Disposition: `DEFER/WIRE`, not DELETE.
2. **Engineering boundary** — `backend/app/modules/engineering` is not mounted in `app.main`; the accepted 100b boundary nevertheless routes structural engineering-domain cleanup to 105. Disposition: `DEFER(105)`.
3. **Process kernel/incumbent process models** — even if generic process infrastructure later loses to an upstream, current equations/tests/fixtures are required as incumbent evidence for the 103 bake-off. Disposition: `DEFER(103/104)`.
4. **Legacy modeling write surfaces versus MemoryStore** — overlap is real but canonical lifecycle/promotion semantics make this 101 work. Disposition: `DEFER(101)`.
5. **Frontend legacy/diagnostic routes** — current `App.tsx` explicitly preserves compatibility routes. Disposition: `KEEP/DEFER`, not deletion based on primary-IA absence.
6. **Backend APIs not exposed by the final 100f UI** — lack of a current visible consumer is not authority to delete smoke, review, proposal, run, evidence or administrative capability. Each remains with its accepted backend owner until a separate product/compatibility decision retires it.

## Deletion-gate evidence

100a recommends **zero `DELETE` dispositions** on the exact audited SHA. Consequently no runtime file is represented as having passed the full deletion gate. This is deliberate: static reachability and route mounting were used as discovery signals, then checked against product intent and later authority boundaries. Items without a complete product-intent, dynamic/reflection/configuration, test/evidence and downstream-owner proof remain `KEEP`, `DEFER`, `WIRE`, `PROFILE` or `UNKNOWN`.

The 100b candidate below is `MERGE`, not DELETE: its accepted behavior is retained in the shared API client before the duplicate module can disappear.

## Ranked ROI / risk register

| Rank | Finding | Disposition | Expected value | Risk | Decision |
| ---: | --- | --- | --- | --- | --- |
| 1 | `frontend/src/api/finalOperatorReads.ts` duplicates shared HTTP/types/read functions | MERGE | Small but concrete reduction: one duplicate API boundary/helper/type family; simpler final-fusion read ownership | low if richer fields and exact endpoints are preserved | **freeze as sole 100b candidate** |
| 2 | Modeling CRUD + MemoryStore write overlap | DEFER | potentially high semantic simplification | high: lifecycle/promotion/audit semantics | **101 owns** |
| 3 | Custom process stack generic infrastructure | DEFER / bake-off | potentially large reduction if upstream wins | high scientific/architecture risk | **103/104 own** |
| 4 | `engineering` placeholder + `flowsheet` naming/domain collision | DEFER | moderate structural simplification | medium; provenance graph is live | **105 owns** |
| 5 | thin agent/file support boundaries without clear current app composition | DEFER/UNKNOWN | small LOC/file reduction | medium product-intent risk; low payoff | no 100b action |
| 6 | high fan-in/out AI/core/frontend composition | PROFILE | unknown runtime value | high regression/security risk | no cleanup without measured hotspot |

## Performance findings: measured vs unmeasured

100a measured source size, route/API counts, exact-file duplication and import fan-in/fan-out. It **did not** run a representative runtime benchmark, profiler, browser timing trace, database query benchmark or solver timing study. Therefore:

- no wall-time, latency, memory, startup-time or rendering-speed claim is made;
- `app.core.database`, AI execution/egress and frontend shell files are structural change-radius hotspots only;
- any future performance optimization must first collect a decision-relevant profile on a representative workload;
- reducing LOC in 100b must not be described as a runtime-speed improvement.

## Bounded 100b candidate set

**Top-level evidence outcome for fresh 100b derivation: `CLEANUP`.**

Freeze exactly one candidate for the 100b readiness decision unless exact post-100a master invalidates the evidence:

### C1 — merge final operator reads into the existing frontend API client

- **100a disposition:** `MERGE`, high confidence.
- **Current duplicate boundary:** `frontend/src/api/finalOperatorReads.ts` (2,243 bytes on audited SHA).
- **Current consumer:** `frontend/src/components/fusion/FinalOperatorReadSurface.tsx` imports its five read functions and associated read types.
- **Existing authoritative neighbor:** `frontend/src/api/client.ts` already owns `API_BASE_URL`, the same `getJson` pattern, `getSystemInfo`, workspace/model-spec/parameter/decision types, and corresponding list/read calls.
- **Preservation obligation:** keep exact endpoints and response fidelity, including requirement reads and the richer parameter fields used by the fusion UI (`value_status`, `lifecycle_state`, unit/value data). Do not weaken 098 lifecycle truth.
- **Touched runtime boundary proposed for 100b:** `frontend/src/api/client.ts`, `frontend/src/api/finalOperatorReads.ts`, `frontend/src/components/fusion/FinalOperatorReadSurface.tsx`; test-only updates only if imports/contract assertions require them.
- **Expected reduction:** remove one duplicate API module/helper/type family; net active frontend source should decrease. Exact before/after LOC must be recorded by 100b.
- **Required proof:** `cd frontend && npm run build` (which includes the existing 058d/100/100f gates), plus focused 100f/fusion assertions that Project Basis, Models and Runtime retain truthful READ/Unknown/unavailable behavior. No backend mutation is needed.
- **Non-goals:** no visual/IA change, no new API, no new state store, no backend changes, no feature wiring, no cleanup of unrelated legacy routes.

If exact post-100a master shows C1 has already been collapsed or a test demonstrates a separate semantic owner is required, fresh 100b readiness must downgrade to `NO_ACTION` rather than manufacture replacement work.

## 100a acceptance conclusion

- exact audited SHA is recorded;
- all first-party measured areas are covered by component dispositions;
- quantitative baseline is reproducible from the exact Git ref and embedded here;
- desired-but-unwired capabilities are protected;
- no unsupported DELETE claim is made;
- later 101/103/104/105 authorities are explicitly preserved;
- runtime performance remains unclaimed where unmeasured;
- a single bounded high-confidence 100b candidate is identified;
- 100a itself changes no runtime semantics.

`NEXT_EXACT_ACTION`: freeze the 100a PR head to audit evidence + registry metadata only, run exact-head deterministic gates, merge 100a with expected-head guard, reconcile `STATUS.md` to `merged`, then freshly derive 100b from the merged artifact. Because the evidence outcome is `CLEANUP`, 100b runtime implementation remains maintainer-gated after docs-only derivation/readiness.
