# JarvisOS Platform Gaps — Triage and Binding Design Kernels

Status: v0.1 (2026-07-03)
Source: seam map findings (`BLUECAD_SEAM_MAP.md`) + external handoff (GPT) proposing
4 platform runs. This doc records what was accepted, rejected, or modified, and
fixes the binding design decisions ("kernels") that drafted specs must follow.

## Triage decisions

| Proposal | Decision | Rationale |
| --- | --- | --- |
| Audit ~10 reference repos (LiteLLM, LangGraph, AutoGen, CrewAI, Temporal, Prefect, E2B, DeerFlow, …) | **Rejected** | Pattern knowledge is sufficient for specs this size; source audits would consume the remaining frontier-model budget for marginal gain. References may be consulted *by name* for concepts, never for code (clean-room rules apply). |
| Adopt LiteLLM (or similar) as gateway dependency | **Rejected** | Huge surface for a single-user system that needs 2–4 providers. Native thin gateway evolving the existing `ProviderBinding`/adapter pattern instead. |
| External-first S0/S1 with sanitized packets; fail-closed local for S3/S4 (BlueRev raw IP, secrets, unredactable) | **Accepted as policy line** | Consistent with existing sensitivity taxonomy and RouterPolicy redaction gates. No new alpha machinery; recorded as a constraint on all provider-facing specs. |
| Candidate/attempt lifecycle (10+10 states) | **Accepted, simplified** | Several proposed states are redundant (e.g. `accepted_by_validator` ≡ `valid`; `needs_user_review` ≡ `parked(attempts_exhausted)`). Attempt-level *states* replaced by per-phase *outcome fields* — queryable, no state machine to babysit. Final shape in spec 010. |
| Core Team v1 (11 stable agents + temporary specializations) | **Accepted, frozen as data** | Personas are config (prompt + permissions + default route class), not code entities. See `JARVISOS_CORE_TEAM_V1.md`. No BoardSession machinery until after BLUECAD alpha. |
| Honest sandbox language | **Already done** | `BLUECAD_CORE_DESIGN.md` §3 was corrected on 2026-07-03. |

Execution model unchanged: Fable fixes kernels + reviews; Codex drafts full
specs and implements. BLUECAD alpha (specs 005/006/010) is not displaced —
platform specs run behind it.

## Spec numbering

| Spec | Title | Blocks |
| --- | --- | --- |
| 010 | BLUECAD AI loop v0 (includes candidate/attempt ledger) | alpha |
| 015 | PROVIDER-GW-1: provider gateway v1 | nothing in alpha; enables multi-provider + future frontier |
| 016 | RUNNER-EXT-1: scoped runner extension for BLUECAD L2 | spec 012 only |
| 017 | AGENT-CORE-1: Core Team personas as config + panel plumbing | spec 011 only |

## Kernel — PROVIDER-GW-1 (spec 015, binding decisions)

1. **Evolve, don't replace**: keep `run_ai_task(adapters=..., bindings=...)`
   injection and the `AIProviderAdapter.complete(AIRequest) -> AIResponse`
   contract. The gateway is a registry of bindings + adapters, not a new call
   path.
2. **Provider registry as config** (`configs/ai_providers.yaml`, schema-validated):
   provider id, base_url, api_key ref (secrets module — never inline), model
   catalog with per-model route classes, max_tokens defaults, timeout,
   per-provider monthly token/cost caps.
3. **OpenAI-compatible envelope** internally; one generic
   `OpenAICompatAdapter(base_url, key_ref)` covers Scaleway, DeepSeek direct,
   GLM direct, Kimi direct. Anthropic adapter is a later, separate class —
   do not pretend it exists.
4. **Route classes become data**: `external:cheap` / `external:reasoning`
   mappings move from the hardcoded binding table into the registry config.
   Existing behavior must be reproducible byte-for-byte by the default config
   (migration test).
5. **Fallback chains as data** (ordered provider list per route class),
   attempted only on provider errors/timeouts, never on policy/budget blocks.
6. **Budget gates stay where they are** (`evaluate_ai_status` extended
   per-provider, not bypassed). Sensitivity policy line applies: S3/S4 or
   pending redaction never reaches any external adapter (existing RouterPolicy
   invariants remain the enforcement point).
7. All existing tests keep passing; new tests use fake adapters, offline.

## Kernel — RUNNER-EXT-1 (spec 016, binding decisions)

1. **New `implementation_kind = "bluecad_l2_v0"`** alongside
   `batch_growth_v0`; registration accepts caller-supplied script text, stored
   as artifact with SHA-256 (existing hash machinery reused).
2. **Input contract**: `input.json` = a GeometrySpec v0 (validated with the
   005 schema) + declared ports; output contract = the 005 artifact set
   (STEP/STL/GLB/manifest) + `result.json`.
3. **Policy upgrade for L2 only**: keep the textual denylist, add an
   **AST-based import allowlist** (`build123d`, `math`, `json` and stdlib
   subset — explicit list in the spec). Denylist-only is not acceptable for
   LLM-authored code; allowlist is cheap and meaningfully stronger.
4. **Honest isolation statement** (verbatim in the spec): current runner
   isolation is not OS-level sandboxing; it is scoped scripts, input
   validation, textual+AST checks, and a cleared environment. It must not be
   described as network-secure. Stronger isolation (job objects/containers)
   is a future, separate decision.
5. `SANDBOX_VIOLATION` (any policy/allowlist failure) is non-retryable and
   parks the owning candidate (BLUECAD invariant).
6. Existing `batch_growth_v0` path byte-identical behavior (regression tests).

## Kernel — AGENT-CORE-1 (spec 017, binding decisions)

1. Personas are **config, not code**: `configs/agents.yaml` — name, mission,
   system prompt ref, allowed task kinds, default route class, permission
   set (which tools/endpoints it may be used with). Roster frozen in
   `JARVISOS_CORE_TEAM_V1.md`.
2. Temporary specializations = persona + suffix + prompt overlay
   (`Linus.Backend`); never new roster entries.
3. First consumer: BLUECAD review panel (spec 011) — panelists are personas
   invoked through the ordinary provider path; no new orchestration engine.
4. BoardSession / group-chat machinery: **out of scope** until after the
   BLUECAD alpha ships.
