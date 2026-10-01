# 023 — Adversarial proposal corpus

State: **ready** under the 2026-09-30 maintainer directive. Dependency 010 is merged. This slice is confined to the existing BLUECAD GeometrySpec proposal loop and offline backend tests.

## Outcome

The 010 loop treats hostile and degenerate model output as invalid proposal evidence. It records bounded attempts and parks after the configured ladder without crashing, building geometry, promoting a candidate, using a real provider, or executing instructions embedded in model text.

## Scope and boundaries

- Add a small, named, offline corpus covering empty/chatter output, multiple objects, authority or tool-call injection, wrong JSON shapes, non-finite numbers, deep nesting, and oversized responses. Keep samples synthetic and free of secrets.
- Exercise the actual parser and synchronous loop with the existing scripted fake adapter. Assert the real attempt ledger, call cap, terminal parked reason, and absence of build/promotion for malformed output.
- Apply only a demonstrated bounded parser repair needed by the corpus. Do not change GeometrySpec, provider routing, budgeting, promotion, repository authority, frontend, or a conformance test.
- The corpus may make fake adapter calls to emulate returned model output. No network or paid provider is used. Existing `run_ai_task` and `ai_jobs` provenance remain intact.

## Acceptance

1. Every corpus entry is rejected without an uncaught exception; hostile instructions are data and cannot gain tool, file, provider, or promotion authority. Empty provider output retains its existing `provider_error` classification.
2. Repeating each entry through a single-tier, bounded loop creates only the configured number of synthetic attempts, no build or artifacts, and a parked candidate (`malformed_repeated` or `attempts_exhausted` for empty provider output).
3. Oversized output is refused before JSON extraction or schema traversal. Deeply nested output is handled as malformed without a crash or unbounded retry.
4. Focused offline tests, backend lint, and exact-head CI pass. The final diff stays backend/test/documentation only.
