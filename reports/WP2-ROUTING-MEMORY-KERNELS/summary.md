# WP2 — routing and memory planning kernels

## Scope

Registry rows and planning kernels only. No runtime, schema, UI, provider, worker,
vector index, model call, or PR #90 change.

## Added kernels

- 061 `TOKEN-FLOW-0`
- 062 `GRADE-0`
- 063 `CAPTURE-VAULT-0`
- 064 `LIT-RAG-0`

All rows remain `planned`. They are not implementation contracts and must still
pass kernel → full-spec → ready promotion.

## Important audit bindings

TOKEN-FLOW records the projected-budget and max-token defects tracked in issue
#94 rather than assuming existing provider caps are already authoritative.

CAPTURE-VAULT keeps vectors local, rebuildable, and non-authoritative. Canonical
SQLite records are not embedded and remain the sole truth. Every model-backed
embedding call must traverse `run_ai_task` on an explicit local route and write a
safe `ai_jobs` row; direct Ollama/provider adapter calls from the indexing layer
are forbidden. If the current execution spine lacks a provider-neutral embedding
contract, the full spec must add that contract before runtime implementation.

LIT-RAG preserves source locators and authority tags; literature cannot override
canonical records or authorize egress.

## Codex review disposition

The review on head `8ab3414d90` raised one P2 finding: the CAPTURE-VAULT kernel
allowed an implementation to call an Ollama-compatible embedding adapter directly.
The finding is accepted. Spec 063 now binds every embedding model call to
`run_ai_task` and `ai_jobs`, requires a deterministic direct-adapter-bypass test,
and blocks promotion until the provider-neutral embedding contract is defined.

## Unresolved planning gap

The maintainer direction requires `MEMORY-CONSOLIDATE-0`, but WP2 named only four
rows/kernels and did not assign a registry id to consolidation. This PR does not
silently absorb that boundary job into CAPTURE-VAULT or LIT-RAG. A later
maintainer decision must assign its id and exact dependency on Conversation v0.

## Reconciliation

The branch is reconstructed directly from `master` commit
`6340d6832fc0248a547e3a820843aefd85be911e`, after the post-ADR-059 lifecycle
reconciliation merged. It preserves:

- 059a as `merged` through PR #90;
- ADR-059 and the amended 059 definition as merged;
- 059b as `blocked` pending full-spec reconciliation and explicit promotion;
- all unrelated registry rows and roadmap history.

The final master-relative diff is exactly:

- `docs/specs/061-token-flow-0.md`;
- `docs/specs/062-grade-0.md`;
- `docs/specs/063-capture-vault-0.md`;
- `docs/specs/064-lit-rag-0.md`;
- `docs/specs/STATUS.md`;
- this report.

## Verification gate

GitHub Actions must execute on the final reconstructed head. All rows remain
`planned`; this PR authorizes no runtime implementation. 059b remains blocked and
is not promoted by this planning slice.
