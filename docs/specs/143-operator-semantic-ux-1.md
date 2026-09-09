# 143 — OPERATOR-SEMANTIC-UX-1

Status: planning/readiness candidate

## Outcome

Repair already-shipped beta-critical operator surfaces so the primary interface communicates human meaning, capability, status and change before exposing machine identity. Preserve all existing server-owned authority, provenance and exactness; this is a presentation/interaction repair, not a new product domain or execution surface.

The operator should be able to answer, without reading raw JSON or a full SHA:

- what object/version/state am I looking at;
- what can I do here and what is intentionally read-only/proposal-only;
- what changed between the running JarvisOS checkout and the remote target;
- what is healthy, blocked, stale, partial or unavailable;
- where the exact technical evidence can be inspected when needed.

## Accepted causal family

This slice may repair the directly related already-shipped surfaces discovered by the 2026-09-08 operator audit, including Coding Repository, Coding Runtime, Development Pipeline, Model Dossier and Settings after 124 is present.

1. **Primary semantic presentation**
   - Human labels/status/capability/reason/delta are primary.
   - UUIDs, full commit SHA, digests, root identities, timestamps, raw reason codes and raw response JSON are secondary technical evidence unless intrinsically the user-facing value.
   - Technical evidence remains available through a real, keyboard-accessible disclosure such as `Technical details`.

2. **Truthful interaction affordances**
   - A chevron/disclosure visual must perform a real expand/collapse/select/navigation interaction. Decorative chevrons on inert rows are removed.
   - Existing real actions remain bounded by their current authority. This slice grants no new COMMIT/EXECUTE/push/merge/provider/filesystem authority.

3. **Coding runtime delta**
   - Reuse server-owned 119 runtime truth and its existing `semantic_delta` as the first authority for local-vs-remote change presentation.
   - Show a concise human-readable relation and useful changed-file/capability evidence before exact hashes.
   - The frontend must not infer Git ancestry, cleanliness or remote truth independently.
   - A new backend owner/store is forbidden unless fresh implementation evidence proves the existing 119 projection cannot express an accepted semantic requirement.

4. **Structured evidence instead of raw JSON**
   - PR/check/review evidence, pipeline state and proposal outcomes get concise structured operator summaries.
   - Raw JSON may remain only in secondary technical details/debug evidence.

5. **Model Dossier semantics**
   - Version label/title/status/maturity and useful run/artifact/evidence meaning remain primary.
   - Exact model/version IDs, digests and provenance identifiers move to secondary technical details where a human label exists.

6. **Settings semantics**
   - Provider/policy/credential/budget state uses readable labels and explanations in the primary surface while retaining canonical machine codes in technical details.
   - 124 owner boundaries, redaction, credential mutation rules and egress/accounting truth are unchanged.

## Browser-proof acceptance

The trusted exact-head Chromium proof must test interaction, not mere text presence, for the repaired beta-critical paths:

- `/coding/repository`: at least one real disclosure/selection path plus structured evidence rendering; no direct mutation/execute/push/merge affordance.
- `/coding/runtime`: human-readable local/remote relation and semantic delta are visible; technical details can be expanded; no browser-side Git inference/mutation.
- `/memory/models`: exact-version selection remains functional and machine identity is secondary when a human version label exists.
- `/settings/ai` once 124 is merge-ready: provider/settings state is readable, technical detail disclosure is functional, and no secret/provider direct egress is exposed.

Existing exact-head identity, trusted-controller ownership, credential isolation, candidate isolation and artifact requirements from 142 remain mandatory. Browser assertions may be extended only as trusted proof; they do not become product authority.

## Deterministic acceptance

- Existing 113/124/140 frontend contract tests and production build remain green after adapting assertions to the repaired presentation.
- Add focused tests that reject raw-JSON-as-primary output on the touched operator surfaces and reject inert disclosure chevrons in the repaired causal family.
- Existing backend tests remain green; no backend contract change is required merely to rename/present a machine code.
- No secret value, provider credential, GitHub token or browser-side provider/GitHub/filesystem call is introduced.

## Non-goals

- no global design-system rewrite;
- no new router/store/workflow/orchestrator;
- no generic schema-driven UI renderer;
- no self-update, terminal, local-worktree, commit, execute, push or merge authority;
- no replacement of canonical owner-derived machine codes; readable labels are presentation, with original codes retained in technical details;
- no speculative capability-diff engine if current 119 semantic delta is sufficient;
- no broad cleanup outside the directly observed operator-semantic failure family.

## Minimum-necessary test

The beta is not operator-usable if truthful data is presented primarily as implementation identifiers/raw payloads or if controls visually imply interactions they do not provide. The accepted outcome can be reached by repairing existing projections and components; a new domain/store/framework is not necessary.

## Readiness

Implementation is `ready` after this planning/readiness front is merged and its hard dependencies are merged. The coordinator should prefer one bounded repair wave over page-by-page independent slices. Exact file touch lists are expected-surface guidance, not a legal whitelist under the current execution protocol.