# HANDOFF — Close the Positive Cycle + BlueRev Engineering Value

- **From:** Fable (architecture & quality owner, review authority)
- **To:** Sol (GPT 5.6, implementation orchestrator)
- **Date:** 2026-07-16 (state verified against GitHub `master@c39dd31`)
- **Maintainer / merge owner:** Alberto
- **Registry authority:** `docs/specs/STATUS.md` on `master` is the single source of truth for spec state. This document is a snapshot and a work order, never a second registry.

---

## 0. State snapshot (verified 2026-07-16)

- **059b (IP-EGRESS-1B) is implemented and merged** — PR #119, ~50 files. Policy autopilot, automatic sanitizer provenance, exact per-binding packets, ticket-ID confirmation, atomic projected-budget reservation, sampled audit, fallback enforcement, usage-source-bound accounting. The long-standing runtime gate has fallen.
- **Spec 061 TOKEN-FLOW-0 is reconciled and merged as a contract** (PR #122; `docs/specs/061-token-flow-0.md` + its registry row updated together). Row status: `planned` → must be promoted to `ready` before implementation.
- **Open spec-PR stack (docs only, owned by Alberto+Fable, NOT Sol's scope):** #123 (062 GRADE-0, ready-for-review, CI green) → #124 (066) → #125 (067) → #127 (068). PR #126 was intentionally closed: registry updates now travel inside each spec PR.
- CI is green and authoritative again (billing fixed 2026-07-14). Checks: `backend`, `bluecad-geometry-canary`, plus `strict-alpha-proof` where triggered.
- ~30 slices merged (records spine, BLUECAD CAD→mesh→FEM loop with proofs, provider gateway, sensitivity foundation 059a, now 059b). Only `ready` row today: 006b.

## 1. Mission

Two value tracks plus one transversal quality mandate, running in parallel on disjoint files:

- **Track A — close the measurable loop:** implement 061 (TOKEN-FLOW-0), then 062 (GRADE-0), then expose the v0 KPI `external_provider_spend_per_useful_outcome`. After this, every AI flow is classified, accounted, gradeable — and routing decisions (025, later) become evidence-driven instead of vibes-driven.
- **Track B — BlueRev engineering value:** port the process workbook into `calc_v0` (047 → 048 → 049), then flowsheet DAG and linking (050 → 051 → 052 → 053). This is the actual product: Mark-1 decisions backed by inspectable calculation evidence.
- **Track C — product surface:** UI foundation, then 037 → 029 → 058 → 054. JarvisOS must be *smooth and honest to use*: the human-authority surfaces (proposal review, grading, spend status) are load-bearing, not decoration.

**Strategic coupling:** Track B generates the real, representative dogfood flows that Track A measures and the operator grades. Neither closes the loop alone. Track C is what makes grading and promotion low-friction enough to actually happen.

## 2. Non-negotiable ground rules

1. `AGENTS.md` is binding: hard invariants, test gate, spec workflow. Read it before the first branch. (Digest in Appendix C, but the file wins.)
2. **Spec ladder:** backlog row → kernel → full spec (`ready`) → implementation PR. No implementation of a `planned` row. Registry row transitions (`ready`/`in_review` + PR number/`merged`) travel in the same PR that causes them; CI enforces via `scripts/check_spec_status.py`.
3. **One slice per PR**, independently green, reviewable in one sitting. Sol never merges; Alberto merges after Fable review.
4. **Frozen contract files.** `docs/specs/062-grade-0.md`, `066-hermes-passthrough-0.md`, `067-jarvis-mcp-0.md`, `068-hermes-config-0.md` and their STATUS rows are owned by open PRs #123–#127 — never edit them. `docs/specs/061-token-flow-0.md` is a merged frozen contract: implement it, don't amend it (contract changes only via a Fable-reviewed spec PR). When a Track-A/B/C PR edits `STATUS.md`, keep the diff strictly to its own row and rebase promptly.
5. **Hermes is out of scope** (060, 066–069): no implementation, no activation, no config work.
6. **Parked, do not start:** 025 (needs graded dogfood), 039 FRONTIER-1 (parked behind benchmark evidence), any cache layer (no caching before telemetry exists), 063/064 memory layers (after the core loop proves value), new providers, new orchestrators, new frontend frameworks.
7. **Economic honesty invariant (applies to code AND UI copy):** local compute is *unpriced*, never *free*; synthetic is *non-economic evidence*, never a cost win. A UI showing "$0.00" for local compute is a spec violation — show "unpriced" markers exactly as 061/062 define them. No token truncation anywhere.
8. Additive, versioned migrations only. Secrets never in repo, localStorage, logs, or normal frontend state. Server-owned egress/budget/sensitivity authority is untouchable.
9. Max **2 implementation PRs in flight** at any time, on disjoint file sets. Spec-drafting PRs may parallelize (docs only, watch STATUS.md conflicts).
10. Every UI PR includes before/after screenshots and passes the UX bar (§6).

## 3. Track A — close the positive cycle

### A0 — Promote 061 (tiny registry PR)
Gate: confirm with Alberto that (a) #123 is merged or its merge is imminent, and (b) after the Hermes-stack rebase, **no open PR still amends `docs/specs/061-token-flow-0.md`** (as of 2026-07-16, #124 showed restack-artifact diffs against 061/062 — they must disappear or be reviewed as no-ops before A1 starts). Then: one-line registry PR `061: planned → ready`.

### A1 — Implement 061 TOKEN-FLOW-0 (gate: A0 merged; 2–3 slices)
The contract is `docs/specs/061-token-flow-0.md` (merged, ~550 lines). Read it fully; its acceptance criteria are the definition of done. Before slicing, read Appendix A in full: integration points 2, 4 and 8 there (usage_source CHECK rebuild, Scaleway outside the declarative registry, micro-USD vs REAL money representation) are **decision points to raise in your first report-back**, not silent choices. Suggested slicing (re-slice with justification if the code says otherwise, each slice green):

- **A1a — classification + schema foundation.** Additive migration on `ai_jobs`: execution class (`synthetic` | `local_compute` | `external_provider`), `adapter_invoked`, `external_dispatch_state` (`not_applicable`/`not_started`/`started`/`unknown`), usage basis, accounting basis, `accounted_provider_spend_usd` as exact integer micro-USD, cache-read token field, flow/attempt identity. Provider-registry validation: class ↔ `requires_network` coherence, unknown/contradictory classification fails registry loading, fallback entries re-resolve class from the concrete record.
- **A1b — dispatch evidence + usage + accounting.** Adapter wrapper returns normalized dispatch evidence on every path (`started`/`not_started`/`unknown`; an unclassifiable exception is `unknown`, never a guessed value); usage alias parsing including cache fields (today the adapter drops them — see Appendix A/C); exact vs conservative spend bases; cache pricing rules (zero/absent cache reads need no cache price; positive cache reads without accepted cache price → charged at ordinary input price); reconciliation with 059b reservations (external `unknown` is conservatively consumed; `not_started` is not a network attempt). Payoff to prove with an end-to-end test: the monthly external-provider cap becomes *effective for the first time* — today it gates on a `cost_estimate` field nothing populates (audit finding, Appendix C).
- **A1c — flow aggregation + status surface.** Flow-level composition and dispatch-quality summaries, per-class counters, external spend summed exactly once, `local_compute_cost_unpriced` marker, external-not-sent/unknown counts; extend `/ai/status` accordingly. Tests: the spec's invariant matrix (class↔dispatch↔accounting coherence) as table-driven tests + adapter-exception edge cases.

### A2 — Implement 062 GRADE-0 (gate: #123 merged AND A1 merged)
Contract lands with #123 (`docs/specs/062-grade-0.md`). Core: gradeability preconditions (terminal flow, reservations reconciled, attempts finalized), versioned `flow_outcome_digest` snapshot, append-only grade history with expected-version optimistic concurrency, four grades (`useful`/`partly`/`rework`/`failed`) + bounded reason codes, cohort metrics with reconciliation invariants (every flow once in flow metrics, every attempt once in attempt metrics, synthetic excluded from empirical cohorts, ungraded stays in denominators), and the single v0 monetary metric `external_provider_spend_per_useful_outcome` (null-safe, always shown with coverage caveats; `total_economic_cost_per_useful_outcome` is explicitly unavailable in v0).

### A3 — Grading affordance + KPI visibility (small, may fold into A2 or C2)
The loop closes only if grading is ~1 click. Minimal honest slice: a grade action (4 buttons + optional reason code) on the existing workbench flow/attempt detail, plus the KPI + coverage caveats in `/ai/status` output. Full dashboard waits for 029/058 — do not gold-plate here.

**Explicitly out of Track A:** 025 (needs the dogfood 062 will produce), route changes, provider additions.

## 4. Track B — BlueRev engineering value

Registry rows 047–053 are `planned` outlines; each needs kernel → full spec → implementation. The registry row descriptions already encode known workbook bugs to FIX during the port (do not port bugs faithfully).

- **B1 — 047 BLUEREV-PROCESS-0** (geometry, hydraulics, pumping; workbook ranks 1–7). **Hard input gate: Alberto delivers the workbook extraction** (Excel v0.9). Spec must correct hydraulic-vs-illuminated area and residence-vs-loop-turnover definitions; every node is a unit-bearing `calc_v0` node with deterministic + literature verification cases.
- **B2 — 048 BLUEREV-PROCESS-1** (ranks 8–18: biomass, nutrients, gas, harvest, energy/cost KPIs). Includes `preliminary_economic_evaluation_v0` family (`variable_opex_rate`, `specific_variable_cost`, `gross_margin_proxy`) with explicit `economic_boundary`/`economic_basis`, per-input uncertainty/provenance, and a real `not_computable` outcome (never silent zero).
- **B3 — 049 BLUEREV-PROCESS-2** (buoyancy with hardware mass + safety factor; light/transmittance proxies labeled honestly, explicit optical path length).
- **B4–B7 — 050 flowsheet DAG → 051 stale propagation → 052 CAD-LINK → 053 dossier export.** Strictly after 047–049 land; each trigger-gated per registry. 053 is the thesis/investor-facing payoff: decision-to-evidence dossier.

Cadence: B1 spec drafting can start immediately (parallel to A1 — disjoint files). B is the primary *content* track; A is the primary *measurement* track. Run BlueRev work as real dogfood flows through the normal AI spine wherever sensible, so Track A has data to grade.

## 5. Track C — product surface ("smooth e figo")

Dependency-honest order (all deps refer to registry rows):

- **C0 — Propose new row `070 UI-FOUNDATION-0`** (registry addition PR, needs Alberto's ack): design tokens (color/type/spacing, light+dark), app shell, shared primitives (buttons, tables, badges, dialog, toast, skeleton/empty/error states), applied to one existing workbench page as proof. No behavior changes, no new framework. Rationale: 029/037/058/054 all need it, and today's frontend has no token system (see Appendix B). This unblocks all UI work without violating 058's dependency chain.
- **C1 — 037 chat entry point** (deps 010, 042 — both merged): smallest on-ramp that drafts a candidate/brief in the existing workbench. Build on the existing `DevLocalChat` patterns (history, context filter, budget meter) rather than inventing a second chat. No second product surface.
- **C2 — 029 settings & status page** (deps 015, 018, 061 → after A1): provider mode, external USD budget/spend/reservations, token usage **by execution class**, local-compute activity with unpriced marker, continuation guard, secret entry (keys never in localStorage/logs/repo/frontend state). Reuse `/ai/status`.
- **C3 — 058 unified workspace home** (deps 006, 029, 037, 061): workbench/3D-first layout, persistent right-side AI entry, compact status strip (spend/reservations + unpriced-local coverage).
- **C4 — 054 proposal-review UI** (deps 040, 041, 058): THE human-authority surface. Proposed records with provenance, proposed-vs-current comparison, explicit promote/reject with confirm, keyboard-fast triage, direct link to grade the originating flow (062). This is where "smooth" pays: an operator should clear a 10-proposal queue in under a minute without fear.

## 6. UX quality bar (binding acceptance criteria for every C slice)

1. Every async view ships loading (skeleton), empty (with next-action hint), and error (with retry + honest message) states. No blank screens, no fake progress.
2. Tokens only — no ad-hoc hex/px in components. Light + dark from day one (C0).
3. Provenance visible wherever a record/number is shown (who/what produced it, when, from which inputs).
4. Economic honesty in copy: "unpriced" for local compute, "non-economic" for synthetic, coverage caveats next to any KPI. Never "$0.00" for unpriced work.
5. Core flows keyboard-navigable; controls labeled; focus states visible.
6. Local interactions feel instant (<200ms perceived); backend calls show explicit progress; destructive/irreversible actions (promote, reject, grade withdraw) get a confirm step showing exactly what changes.
7. Before/after screenshots in every UI PR body; Fable reviews against this list item by item.

## 7. Working protocol for Sol

- **Subagents:** parallelize *read-only* exploration and *spec drafting* with cheap/fast subagents; use a strong subagent for architecture-heavy analysis. Implementation is single-writer per branch: one agent owns a slice's code; no concurrent writers; nothing pushes without your review of the diff.
- **Per-PR checklist:** spec row updated in-PR; CI green; acceptance criteria mapped to test names in the PR body; screenshots for UI; no drive-by refactors; no files overlapping another open PR.
- **Report-back per slice (to Alberto+Fable):** PR link, what changed vs spec, acceptance checklist with evidence, open questions/decisions needed, next slice proposal. Keep it under a page.
- **When blocked** (spec ambiguity, dependency, registry conflict): stop the slice, write the question with your recommended answer, continue on the other track. Do not improvise contract changes — 061/062 contracts are frozen except through spec PRs reviewed by Fable.

## 8. Immediate first actions (Sol, day one)

1. Read `AGENTS.md`, `docs/specs/STATUS.md`, `docs/specs/061-token-flow-0.md`, `scripts/check_spec_status.py`, and Appendices A–C below.
2. Confirm gates with Alberto: #123 merge status; 061-file stability (no open PR amends it); workbook extraction availability for B1.
3. Open A0 (061 → ready) once gates pass.
4. While A0 awaits merge (docs-only work is allowed): B1 (047) kernel/spec draft + C0 (070 UI-FOUNDATION-0) registry proposal.
5. Only after A0 merges: start the A1a implementation branch. The ladder forbids implementation branches on a `planned` row — A1a never starts before A0 lands.
6. Send the first report-back after A1a is in review.

## 9. Open decisions for Alberto

1. Merge order/timing of the spec stack #123 → #124 → #125 → #127 (independent review pending — Codex quota). Track A2 is gated on #123 only.
2. Deliver the BlueRev workbook (Excel v0.9) for 047 extraction.
3. Ack the `070 UI-FOUNDATION-0` registry addition (C0).
4. Local housekeeping in your working tree: `docs/specs/045-ledger-verdict-0.md` (superseded by 061/062 — delete or archive) and the parked `docs/specs/039-*.md` draft; decide whether to commit `docs/strategy/JARVISOS_TASK_EFFICIENCY_AND_EVIDENCE_AUDIT.md` and this handoff so Sol can read them from the repo.

---

## Appendix A — Backend implementation surface for 061 (agent-verified map, master @ c39dd31)

### A1. Current state (file:line)

- **`ai_jobs`:** `backend/app/core/schema.py:338-359`. Has route/provider/model, digests, input/output tokens, `cost_estimate REAL`, `usage_source TEXT CHECK ('actual','estimated','mixed')` (added by `egress_schema.py:360-361` — **no `none`**), latency, error_type. Missing everything 061 adds: flow identity, execution_class, adapter_invoked, dispatch state, accounting basis, cache/reasoning tokens, micro-USD spend.
- **Migration mechanism:** additive `ALTER TABLE` lists (`schema.py:457-494`, `egress_schema.py:353-362`), idempotent duplicate-column swallow (`database.py:81-89`), migration registry rows (`database.py:203-217`; current head `0010_ip_egress_policy_autopilot`). 061 = new `0011_*` module mirroring `egress_schema.py`; new tables must be added to `is_database_initialized()` (`database.py:111-135`).
- **Spine:** `run_ai_task` at `backend/app/modules/ai/execution.py:413-783`. Local/non-network path lives entirely there (fallback loop `611-779`, single `adapter.complete()` at `705`, ledger write `_write_ai_job:172-233` — the INSERT omits `usage_source`, so **local rows leave it NULL today**). Network bindings are redirected (`354-410`, `432-446`) into the 059b path.
- **059b modules** (`backend/app/modules/ai/egress_*.py`): `egress_policy` (config), `egress_service` (packet projection/hash/sampling), `egress_authority` (prompt/context authority + sanitizer trigger), `egress_sanitizer` (provenance + sampled audit), `egress_persistence` (atomic packet+decision+reservation, `BEGIN IMMEDIATE` at `:219`), `egress_lifecycle` (tickets/reservations; `reconcile_reserved_attempt:271` takes a plain bool `network_attempt`, `usage_source` restricted to `{actual,mixed,estimated}`), `egress_spine` (queued→finalized `ai_jobs`), `egress_runtime` (`run_external_task:117`, adapter call at `:490`), `egress_confirmation` (`run_confirmation_ticket:61`, adapter call at `:242`), `egress_revalidation`.
- **Registry/adapters:** `provider_registry.py` — `ProviderConfig:29-39` (**no execution_class**), `ModelConfig:51-58` (**no context_window_tokens**), closed pricing key-set `_PRICING_KEYS:18-26` (**no cache-read price key**; extra keys rejected). `configs/ai_providers.yaml` has fake/local_ollama/deepseek/glm/kimi; **Scaleway is absent from the YAML** — hardcoded adapter in `execution.py:45,111-113`. `providers/openai_compat_adapter.py:130-139` parses only `prompt_tokens`/`completion_tokens` and **drops cache/reasoning subfields**. No adapter-internal retry anywhere in `providers/*.py` (already spec-compliant).
- **Dispatch-state gap:** `network_attempt=True` is hardcoded on every post-reservation path (`egress_runtime.py:502,543,567`; `egress_confirmation.py:254,291,311`) — boolean, no started/not_started/unknown.
- **Confirmation:** DB-backed, restart-safe tickets (`egress_schema.py:126-147`; `POST /ai/tasks/escalations/confirm` → `routes.py:90-98`). **No flow/segment/continuation concept exists anywhere yet** (grep for `flow_id`/`execution_class`/`accounting_basis` returns nothing).
- **Status:** `GET /ai/status` → `budget.evaluate_ai_status:166-245`, legacy token-cap shaped; `provider_month_to_date_usage` (`budget.py:136-153`) sums REAL `cost_estimate`. No aggregation code to reuse.
- **`scripts/check_spec_status.py`:** the implementation PR must declare `**Spec gate:** implementation 061` (or matching title), flip the 061 row to `in_review` with the PR number in the same PR, and have all deps `merged` (true: 021, 059b).
- **Tests:** flat `backend/tests/test_ai_*.py`, per-file fake adapters (`test_ai_execution_spine.py:16-81` et al.), autouse `isolated_data_root` in `conftest.py:27-47`, no shared fixture library. 061 tests → new `test_ai_flow_*.py` files; proposing a shared helper module is a legitimate design decision to raise.

### A2. Integration points 061 requires (keep this numbering when referencing)

1. New additive migration module (`token_flow_schema.py`-style) wired into `database.py`: `ai_flows`, `ai_flow_segments`, new `ai_jobs` columns (flow/parent linkage, fallback/continuation index, execution_class, adapter_invoked, external_dispatch_state, effective output ceiling, normalized finish_reason, cache_read/reasoning tokens, accounting_basis, accounted spend).
2. Widen `ai_jobs.usage_source` CHECK to include `none` — SQLite cannot ALTER a CHECK constraint: table rebuild or app-layer enforcement. **Decision point.**
3. Registry: add `execution_class` to `ProviderConfig`/YAML, `context_window_tokens` to `ModelConfig`, `cache_read_input_usd_per_million` to `_PRICING_KEYS`, plus fail-closed mutual-consistency validation in `parse_provider_registry` (`provider_registry.py:91-174`).
4. Resolve Scaleway's absence from the YAML registry (register it, or an explicit carve-out) — classification cannot be total while a live adapter sits outside the declarative registry. **Decision point.**
5. Adapter dispatch wrapper around the two real external call sites (`egress_runtime.py:490`, `egress_confirmation.py:242`) producing started/not_started/unknown; replace the hardcoded `network_attempt=True` sites and the bool param in `reconcile_reserved_attempt`.
6. Extend `contracts.AIUsage`/`AIUsageSource` (`contracts.py:74-119`) with nullable `cache_read_tokens`/`reasoning_tokens` and a `none` member; teach `openai_compat_adapter._response_from_data` (`:130-175`) to parse tested cache/reasoning aliases.
7. Give the local/synthetic path in `execution.py` the same fresh binding/capability/policy re-evaluation discipline the external path gets from `egress_authority`/`egress_persistence` — today only external attempts have it (largest structural asymmetry vs the spec).
8. Add `accounted_provider_spend_usd` as exact integer micro-USD **alongside** the existing REAL columns (`ai_jobs`, `egress_budget_reservations`, `egress_attempts`); `usage_cost.actual_registry_cost_usd` (`usage_cost.py:7-32`) returns float today. Must not break 059b reservation math. **Decision point.**
9. Finish-reason normalizer (`stop|length|content_filter|tool_call|error|unknown`) — none exists; adapters return raw strings.
10. `ai_settings.max_direct_continuations` (0..16, default 8) + `AISettingsRead/Update` (`models.py:10-47`), snapshotted onto `ai_flows` at creation.
11. Extend tickets/`run_confirmation_ticket`/`egress_revalidation` to bind flow/segment/continuation-guard identity and load accumulated segment content.
12. Extend `/ai/status` (`AIStatusRead`, `budget.evaluate_ai_status`) + a new flow-aggregation query module.

### A3. Known contract mismatches / regression risks

- Local/fake rows never set `usage_source` (INSERT omits it) — contradicts "every attempt persists a usage source".
- `network_attempt` hardcoded True over-records network attempts for 059b first-use accounting once real evidence is threaded — fix together with point 5.
- Record-capture (`_create_proposed_records_from_response`, `execution.py:329-351`) fires per-attempt on `status=="success"` — once flows/fallbacks/continuations exist it will double-fire unless re-gated on `ai_flows` terminal state.
- Money as REAL USD end-to-end vs micro-USD integers: dual representation during transition, reconcile carefully (point 8).
- Closed `_PRICING_KEYS` means cache pricing is schema work, not a YAML tweak.

## Appendix B — Frontend/UX inventory (agent-verified map)

**Stack:** React 18.3 + TypeScript strict, Vite 6 (`npm run dev` on 127.0.0.1:5173, `npm run build` = tsc + vite). No UI library; Three.js for the GLB viewer. All styling in `frontend/src/styles/global.css` (~1200 lines of plain CSS): Inter + Cascadia Mono, navy sidebar (#102a43), light background, status pills, token-meter bars. **No CSS variables/tokens, no dark mode.** State is per-page `useState`; API layer is `frontend/src/api/client.ts` (getJson/postJson/putJson/deleteJson, throws generic errors).

**Pages (6):** `Dashboard` (health/milestones), `SystemStatus` (backend/DB/AI gateway panel incl. budget + MTD spend), `DomainFoundation` (workspace records CRUD), `BlueCAD` (candidate list/detail, 3D viewer, validation table, attempt history; promote button exists but is minimal — no review/reject flow), `AIDraft` (891 lines: AI task executor + AI settings form + Scaleway secret form + token meters — settings/secrets are scattered here), `DevLocalChat` (working chat with history, context filter, prompt-budget meter — a solid foundation for 037). Components: `Layout` (fixed 280px sidebar), `BluecadGlbViewer`, `PageErrorBoundary`.

**UX debt (verified):** no tokens/dark mode; generic error strings with no retry; no skeleton loading (text toggles + disabled buttons); hardcoded `"bluerev"` workspace id in several pages; settings + secrets buried inside AIDraft; copy-pasted form CSS (`.settings-form`, `.draft-form`, `.ai-task-form`, `.bluecad-new-form`); ARIA/keyboard gaps (unlabeled nav buttons, form inputs); incomplete proposal UX (promote shows a bare decision_id).

**Placement for Track C:** 070 = extract palette/typography/spacing into CSS variables + shared primitives (button/table/pill/skeleton/empty/error), apply to one workbench page as proof; 037 = productionize the DevLocalChat patterns into the brief-drafting on-ramp; 029 = consolidate AIDraft's settings + secret forms + spend meters into one settings page with per-execution-class counters (post-A1); 058 = new home replacing Dashboard with workbench-first layout + compact status strip; 054 = dedicated review queue (standalone page + link from BlueCAD detail) with provenance, proposed-vs-current, promote/reject.

## Appendix C — Governance digest, spec-file inventory, audit findings

### C1. AGENTS.md digest (the file itself wins on any divergence)

Hard invariants (10): (1) auto never executes external providers; (2) every AI call goes through the execution spine `run_ai_task` and writes an `ai_jobs` row; (3) frontend never calls providers/Ollama/filesystem/tools directly; (4) safe defaults stay safe (paid AI disabled, budget zero, fake provider); (5) local classifier is advisory only; (6) no secrets in logs/events/docs/fixtures/commits; (7) data-root paths via `backend/app/core/paths.py`; (8) AI outputs are proposals — explicit promotion required; (9) no fabricated results; (10) smallest sufficient change before new subsystems.

Test gate: `python -m pytest -q` and `python -m ruff check app tests` (backend), plus `npm run build` when frontend changed. Workflow: row `ready` → branch `spec/NNN-<slug>` → implement → test gate → PR with the STATUS row set `in_review` + PR number (CI enforces via `scripts/check_spec_status.py`) → maintainer merges and sets `merged`. One spec per PR; non-goals are binding; never merge your own PR; model reviews are advisory; external reviews manual-only. Spec files: `NNN-<slug>.md` with scope, acceptance criteria, tests, non-goals; verify any "files likely touched" list against the actual code; live status lives only in STATUS.md.

### C2. Spec-file inventory (master, 2026-07-16)

- **Need full drafting (registry row only, no spec file):** 025, 029, 037, 039, 047, 048, 049, 050, 051, 052, 053, 054, 058 — plus the proposed 070. No kernel files exist yet for any of them.
- **Spec file already exists but row is `planned` (do not implement without promotion):** 045 (`045-runner-hardening.md`), 063 (`063-capture-vault-0.md`), 064 (`064-lit-rag-0.md`).
- 061 spec file is merged and frozen; 062/066/067/068 files exist but are being amended by the open stack #123–#127.

### C3. Audit findings binding for Track A (from `docs/strategy/JARVISOS_TASK_EFFICIENCY_AND_EVIDENCE_AUDIT.md`, 2026-07-13, uncommitted in Alberto's tree)

1. `ai_jobs` today: ~79 historical jobs, `cost_estimate = 0.0` everywhere — adapters never populate it. KPI numerator missing.
2. The OpenAI-compatible adapter **drops** cache/reasoning usage fields the providers already return (`prompt_cache_hit_tokens`, `prompt_tokens_details.cached_tokens`, `completion_tokens_details.reasoning_tokens`). A1b must parse them.
3. Monthly provider caps currently gate on that never-populated `cost_estimate` → caps are unverifiable today; A1b makes them real (end-to-end test required).
4. `policy_version`/`sensitivity` persisted only for auto control rows, not all jobs → 061's per-attempt sensitivity/policy binding closes this.
5. No acceptance verdict exists anywhere → 062 provides it. **Note:** the audit's original patch sketch (a `human_verdict` column on `ai_jobs` + per-job endpoint) is **superseded** by the reconciled 062 contract (flow-level, append-only grade history with digest snapshot). Where audit patches and 061/062 contracts diverge, the contracts win.
6. Benchmark scenario seeds BM-01..BM-10 are defined in the audit doc (secret-block, disabled-provider proposal, cap exhaustion, context-budget fail-closed, external proposal, two real bug-fix baselines, CAD loop, malformed-spec repair→park, decision-conflict deference). Reuse them as 061/062 test scenarios where they fit; the benchmark itself stays curation-only.
7. Anti-goals reaffirmed by the audit (still binding): no new orchestrator, no runtime A/B loop, no application cache, no RAG/vectors, no new providers (039 parked), no durable multi-step run state.
