# 003 — ESCALATE-CONFIRM-0: external escalation proposal + user-confirmed execution

Status: implemented (pending review)
Depends on: none (002 recommended first, for measured evidence of local ceiling)

## Goal

When Auto detects that a task exceeds local capability, the user receives a
non-executing escalation proposal (target route, cost estimate, and the exact text
that would leave the machine) and can execute it with one explicit confirmation.
Auto itself still never executes an external provider.

## Why

The local quality ceiling is currently silent: hard tasks get best-effort local
answers with only a metadata flag. This is the cheapest path to frontier quality on
hard tasks without violating the Auto-local-only invariant: the *user* executes, not
Auto. Interim egress rule: prompt text only, no workspace/project context, ever.
(Strategy reference: `docs/strategy/JARVISOS_AI_ROUTING_AND_MODEL_ECONOMY.md`,
"External Escalation Future Path".)

## Scope

In scope:
- **Phase A (verify first, report before proceeding):** confirm that the
  `external:reasoning` explicit route works end-to-end today via existing smoke
  paths, or report exactly what is broken and stop. Do not fix provider issues in
  this slice unless trivial.
- A static cost registry: per external route/model, input+output price per 1M
  tokens, in a small backend config/module (hand-editable, no network fetch).
- Escalation proposal payload: when the Auto bridge sets `capability_exceeds_local`,
  the control-state response additionally includes a structured
  `escalation_proposal`: proposed external route, resolved provider/model, estimated
  cost (from registry + a crude token estimate of prompt and max output), the exact
  outbound text (the raw prompt only), and an explicit `context_excluded: true` field.
- A confirm endpoint (e.g. `POST /ai/tasks/escalations/confirm` — follow existing
  route naming conventions): takes the proposal (or its ledger reference), executes
  through the **existing explicit external route path** in the spine with the raw
  prompt only, and links the resulting `ai_jobs` row to the proposal's ledger row.
- Ledger: proposal and confirmed execution are both recorded and linked.
- Minimal frontend: in the AI console, when a response carries an
  `escalation_proposal`, render a confirmation card (route, model, estimated cost,
  outbound text preview, confirm button). Keep it plain; no new UI framework
  patterns.

Out of scope (binding non-goals):
- **No workspace/project context or manual context blocks in the outbound external
  request. Prompt text only.** This is the whole interim redaction policy; do not
  build a redaction engine.
- No automatic escalation of any kind: no retry-to-cloud, no policy that executes
  without a per-call user click.
- No session/workspace-level "always allow" persistence.
- No changes to RouterPolicy authority, budget/token guard behavior, or safe
  defaults (paid AI must still be explicitly enabled in settings for the confirm to
  execute; if disabled, confirm fails closed with a clear message).
- No streaming, no new providers, no provider registry beyond the static cost table.

## Files likely touched

- `backend/app/modules/ai/routing/bridge.py` (attach proposal to control state)
- `backend/app/modules/ai/execution.py` (external binding resolution — read, likely
  minor or no change)
- `backend/app/modules/ai/routes.py` (+ confirm endpoint)
- New small module/file for the cost registry (place under `backend/app/modules/ai/`)
- `backend/app/modules/ai/models.py` / `contracts.py` (payload shapes)
- `frontend/` AI console page + API client (confirmation card)
- `backend/tests/` (see below)

## Design constraints

- The confirm path reuses `run_ai_task` with the explicit external route — no new
  execution path, no bypass of budget/token/policy guards.
- Existing sensitivity behavior is preserved: if the local classifier flagged the
  prompt `secret`, no proposal is produced at all (stays blocked); for
  `confidential`/`sensitive_ip` flags, the proposal must carry a prominent
  sensitivity warning field the UI displays — but execution still requires the same
  explicit user click either way.
- Cost estimate is explicitly labeled an estimate; formula and registry values live
  in code/config, not UI text.
- All tests use the fake provider; simulate the external route binding with the
  existing fake/mocked provider patterns from gateway/spine tests.

## Acceptance criteria

1. Phase A result documented in implementation notes (working, or exact failure).
2. An Auto request whose classification marks `capability_exceeds_local` returns a
   non-executing response containing a complete `escalation_proposal`; no provider
   call occurs; ledger row records the proposal.
3. The proposal's outbound text equals the raw prompt and nothing else, and
   `context_excluded` is `true`, even when the original request included
   `include_project_context=true` or manual context blocks.
4. Confirming executes via the explicit external route through the spine, writes a
   linked `ai_jobs` row, and returns the response with ledger ids for both rows.
5. Confirm fails closed (clear error, no call) when paid AI is disabled, budget is
   zero, or credentials are absent.
6. `secret`-flagged prompts produce no proposal.
7. AI console renders the card and can trigger confirm (manual verification note is
   acceptable for visual details; the API client call must be exercised by the
   frontend build).

## Required tests

- Bridge test: exceeds-local classification → proposal shape, no execution, ledger
  row (extend `backend/tests/test_ai_auto_bridge.py` patterns).
- Context-exclusion test: request with project context + manual blocks → outbound
  text contains prompt only.
- Confirm endpoint tests: happy path (fake provider), paid-AI-disabled fail-closed,
  budget-zero fail-closed, secret-blocked produces no proposal.
- Cost registry unit test: estimate computation for a known prompt size.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status updated,
summary written. This slice may land as two commits (backend, then frontend card)
on the same branch.


## Implementation notes

- Phase A verification: `external:reasoning` is present in the execution spine binding table and can be exercised end-to-end through the existing explicit external route path when the Scaleway route gates are enabled; the confirm endpoint reuses that path. In this container, live provider execution was not attempted. Tests verify the route through the spine with a mocked Scaleway adapter/fake response and verify fail-closed behavior for disabled paid AI and zero budget.
- Escalation proposals use the interim redaction policy: outbound text is exactly the raw prompt, `context_excluded` is `true`, and manual/project context is not sent on confirm.
- Proposal/execution linking is recorded in `ai_jobs.route_reason_json`: proposal rows include `escalation_proposal`, and confirmed execution rows include `escalation_proposal_ledger_id`.
- Frontend visual verification was limited to `npm run build` in this non-interactive container.

## Review notes (2026-07-02, spec-003 round 1)

- **Trigger is intentionally dormant (MAJOR from review).** `capability_from_classification`
  never returns `CAPABILITY_DEEP_REASONING` today, so `capability_exceeds_local` is
  always false in production and the escalation branch is exercised only by tests
  (via monkeypatch). This is **by design and correct for the current sequencing**:
  detecting when local capability is genuinely exceeded requires the measured
  local-ceiling data from spec 002 (smoke matrix + routing eval). Wiring a real
  trigger now would hard-code an unmeasured threshold — the opposite of the
  determinism/blast-radius principle (measure quality signals, don't guess). This
  slice therefore lands as **complete-and-verified plumbing** (proposal → confirm,
  egress = prompt only, secret blocked, fail-closed all tested) that activates when
  a later slice, informed by 002, teaches the capability classifier to emit
  `deep_reasoning`. Acceptance criterion 2 is demonstrated via the bridge tests
  until that wiring exists.
- **Secret audit-reason fidelity (MINOR, accepted).** The `secret → CONTROL_BLOCKED`
  short-circuit returns before `decide_router_policy`, so the ledger reason for secret
  prompts is the generic control-block code rather than `_block_secret`'s specific
  code. Execution behavior is unchanged (deterministic policy already blocked these);
  only audit granularity is reduced. Accepted for now.
- **Non-executing proposal row (MINOR, fixed).** `_attach_escalation_proposal_to_job`
  no longer stamps `provider_id`/`model_id`/`cost_estimate` on the proposal's `ai_jobs`
  row; the estimate stays in `route_reason.escalation_proposal`, so a future
  `SUM(cost_estimate)` audit cannot misread an estimate as real spend.
- **Credentials-absent fail-closed (MINOR, fixed).** Added
  `test_confirm_escalation_credentials_absent_fails_closed` to cover the third case
  of acceptance criterion 5.
