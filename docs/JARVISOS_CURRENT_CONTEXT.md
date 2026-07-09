# JarvisOS current context

This file is the short handoff entry point for a new chat or agent. Until spec 057 is implemented, the active-work section is manual. After spec 057, the spec ledger block should be generated/checkable.

## Current active work

- Active implementation dispatch: issue #63, `Spec 038 implementation dispatch — SIM-WIRE`.
- Active branch prepared: `spec/038-sim-wire`.
- Current instruction: Codex should implement `docs/specs/038-sim-wire.md`, open a PR to `master`, and not merge.
- 038 depends on 044; 044 is already merged into `master`.
- Human action needed: review the eventual 038 PR; do not start a conflicting BLUECAD loop wiring branch unless #63 stalls.

## Recently merged

- PR #62 / spec 044 was squash-merged into `master` as `25f2d9deb2f4daba18f7fcf0d9e2c434c11c868d`.
- 044 added typed BLUECAD evidence records and context-pack evidence support.
- `backend/app/modules/bluecad/evidence.py` exists on `master`; specs may now use the real evidence writer hooks instead of a stand-in.

## Next recommended specs

1. 038 — SIM-WIRE: wire mesh + FEM into the candidate/attempt loop. Active via issue #63.
2. 024 — FEM verification battery. Recommended after 038 or immediately if FEM credibility becomes the main blocker.
3. 021 — Alpha gate. Recommended after the loop has real validation/evidence/simulation context.
4. 057 — SPEC-LEDGER-0. This spec formalizes this handoff mechanism and makes the ledger generated/checkable.

## Known stale/conflicting docs

- `docs/specs/README.md` may lag individual spec files and merged PR state. Treat live code, merged PRs, and individual spec files as higher authority.
- Old chat handoffs and local intake files are historical snapshots, not source of truth.
- A spec is not `done` merely because implementation exists; it is done only after merge.

## Standing rules

- Runtime code, tests, CI, and merged PR state beat roadmap prose.
- Merge requires explicit human confirmation.
- Codex/model reviews are advisory. Deterministic tests and direct code inspection are authority.
- Do not start a spec whose hard dependencies are not merged.
- For implementation dispatches: one spec, one branch, one PR, no broadening.
- For BLUECAD safety: no provider/model calls, no auto-promotion, no hidden runner/background work unless the spec explicitly allows it.

<!-- spec-ledger:start -->

Generated ledger is not active yet. Implement spec 057 to replace this section with deterministic output from `scripts/spec_ledger.py`.

<!-- spec-ledger:end -->
